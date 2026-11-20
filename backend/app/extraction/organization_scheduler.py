"""Opt-in organization admission. No network, environment loading or Stage A/B hooks.

Evidence is a trusted operator attestation, not a provider-authenticated signature.
SQLite partitions claims/usage by verified organization; it cannot see other callers.
"""
from contextlib import contextmanager
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


MODEL = "openai/gpt-oss-120b"
METRICS = ("RPM", "RPD", "TPM", "TPD")
from app.extraction.quota_policy import HARD_CEILINGS,quota_ceiling
CONFIGURED_CEILINGS = dict(HARD_CEILINGS)
Text = Annotated[str, Field(pattern=r"\S")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Stamp = Annotated[float, Field(allow_inf_nan=False)]


class SchedulerHold(RuntimeError):
    retryable = False


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, hide_input_in_errors=True)


class ExtractionConfiguration(Frozen):
    prompt_policy: Literal['quote_catalog_v1', 'grounded_fields_v2', 'context_grounded_v3', 'canonical_grounded_v4'] = 'quote_catalog_v1'
    wire_format: Literal['native','compact_claim_table_v1','compact_field_rows_v1','compact_field_rows_quiz_v1','compact_field_rows_quiz_v2','compact_field_rows_quiz_v3','compact_field_rows_quiz_v4','typed_claim_refs_v1','category_bounded_12a_v1'] = 'native'
    target_category: Literal['concepts','definitions','explanations','examples','facts','formulas','procedures','relationships'] | None = None
    provider: Literal["Groq"] = "Groq"
    model: Literal["openai/gpt-oss-120b"] = MODEL
    temperature: Literal[0] = 0
    response_format: Literal["json_object", "json_schema"] = "json_object"
    reasoning_effort: Literal["low"] | None = None
    strict_evidence: Literal[True] = True
    fallback: Literal[False] = False
    # Existing extractor/budget defaults, not the new aggregate admission margin.
    tokens_per_minute: Literal[8000] = 8000
    preferred_output_tokens: Literal[1000, 2000, 3000, 4000] = 4000
    min_output_tokens: Literal[500] = 500
    max_retries: int = Field(default=2, ge=0, le=3)
    scheduler_ceilings: tuple[int, int, int, int] = (25, 850, 6800, 170000)


SHARED_CONFIGURATION = ExtractionConfiguration()


class Identity(Frozen):
    slot: int = Field(ge=1, le=10)
    organization: Text
    project: Text
    credential_id: Text
    credential_sha256: Hash
    verified_by: Text
    ownership_evidence: Text
    verified_at: Stamp
    # Explicit null means operator approval lasts until revoked. Missing is invalid.
    expires_at: Stamp | None

    def valid_at(self, now):
        return self.verified_at <= now and (self.expires_at is None or now < self.expires_at)


class Organizations:
    """Runtime secrets are separate from serializable identity and status records."""
    def __init__(self, identities, credentials, enabled):
        self.identities = tuple(identities)
        self.enabled = tuple(enabled)
        self.__credentials = dict(credentials)
        slots = [i.slot for i in self.identities]
        orgs = [i.organization.strip() for i in self.identities]
        fingerprints = [i.credential_sha256 for i in self.identities]
        if (len(slots) != len(set(slots)) or len(orgs) != len(set(orgs))
                or len(fingerprints) != len(set(fingerprints))):
            raise SchedulerHold("Duplicate organization, credential or slot")
        if not self.enabled or len(set(self.enabled)) != len(self.enabled):
            raise SchedulerHold("At least one distinct enabled slot required")
        if any(s not in slots for s in self.enabled):
            raise SchedulerHold("Enabled slot has no verified identity")
        for identity in self.identities:
            if identity.slot in self.enabled:
                self.key(identity)

    def __repr__(self):
        return f"Organizations(enabled_slots={self.enabled!r})"

    def key(self, identity):
        key = self.__credentials.get(identity.slot)
        if not isinstance(key, str) or not key.strip() or sha256(key.encode()).hexdigest() != identity.credential_sha256:
            raise SchedulerHold("Credential does not match verified identity")
        return key

    def check_metadata(self, value):
        text = json.dumps(value, default=str)
        if any(key and key in text for key in self.__credentials.values()):
            raise SchedulerHold("Credential material found in metadata")


def load_organizations(identities, environ=None, *, slots=range(1, 6)):
    """Read already-loaded environment. Never reads/writes .env or uses legacy keys."""
    environ = os.environ if environ is None else environ
    enabled, keys = [], {}
    for slot in slots:
        prefix = f"GROQ_ORG_{slot}_"
        flag = environ.get(prefix + "ENABLED", "false").strip().lower()
        if flag not in ("true", "false"):
            raise SchedulerHold("Organization ENABLED must be true or false")
        if flag == "true":
            enabled.append(slot)
            keys[slot] = environ.get(prefix + "API_KEY")
            matches = [i for i in identities if i.slot == slot]
            if len(matches) != 1 or environ.get(prefix + "ID") != matches[0].organization:
                raise SchedulerHold("Organization ID does not match verified inventory")
    return Organizations(identities, keys, enabled)


class QuotaWindow(Frozen):
    scope: Literal["organization", "project"]
    metric: Literal["RPM", "RPD", "TPM", "TPD", "ITPM", "OTPM"]
    limit: int = Field(gt=0)
    used: int = Field(ge=0)
    outstanding: int = Field(ge=0)
    data_as_of: Stamp
    evidence: Text


class VerifiedAdmission(Frozen):
    organization: Text
    project: Text
    credential_id: Text
    credential_sha256: Hash
    request_id: Text
    request_sha256: Hash
    configuration_sha256: Hash
    state: Literal["quota_verified", "quota_estimated", "quota_unknown", "quota_exhausted"]
    authorization: Text
    verified_by: Text
    inventory_evidence: Text
    complete_limit_inventory: Literal[True]
    complete_usage_inventory: Literal[True]
    project_limits_apply: bool
    organization_split_metrics: tuple[Literal["ITPM", "OTPM"], ...] = ()
    project_split_metrics: tuple[Literal["ITPM", "OTPM"], ...] = ()
    traffic: Literal["controlled", "accounted", "unknown"]
    coordination_evidence: Text
    verified_at: Stamp
    control_until: Stamp
    windows: tuple[QuotaWindow, ...]

    def check(self, identity, request_id, request_hash, config_hash, now):
        if self.state != "quota_verified" or self.traffic == "unknown":
            raise SchedulerHold("Unverified quota is non-dispatchable")
        if any(getattr(self, f) != getattr(identity, f) for f in
               ("organization", "project", "credential_id", "credential_sha256")):
            raise SchedulerHold("Admission identity mismatch")
        if (self.request_id, self.request_sha256, self.configuration_sha256) != (request_id, request_hash, config_hash):
            raise SchedulerHold("Admission request/configuration mismatch")
        if not identity.valid_at(now):
            raise SchedulerHold("Identity review expired or future-dated")
        if not 0 <= now - self.verified_at <= 15 or self.control_until < now + 90:
            raise SchedulerHold("Stale admission or insufficient traffic-control duration")
        expected = {("organization", m) for m in METRICS}
        if self.project_limits_apply:
            expected.update(("project", m) for m in METRICS)
        elif self.project_split_metrics:
            raise SchedulerHold("Contradictory project applicability")
        for scope, metrics in (("organization", self.organization_split_metrics), ("project", self.project_split_metrics)):
            if len(metrics) != len(set(metrics)):
                raise SchedulerHold("Duplicate split metric")
            expected.update((scope, m) for m in metrics)
        rows = {(w.scope, w.metric): w for w in self.windows}
        if len(rows) != len(self.windows) or set(rows) != expected:
            raise SchedulerHold("Incomplete or duplicate quota inventory")
        for w in self.windows:
            if not 0 <= now - w.data_as_of <= 15 or w.data_as_of > self.verified_at:
                raise SchedulerHold("Stale or future-dated usage evidence")
            org = rows.get(("organization", w.metric))
            if w.scope == "project" and org and w.limit > org.limit:
                raise SchedulerHold("Project ceiling exceeds organization ceiling")


class QuotaLimit(Frozen):
    """Configured total capacity, without a claim about external usage."""
    scope: Literal["organization", "project"]
    metric: Literal["RPM", "RPD", "TPM", "TPD", "ITPM", "OTPM"]
    limit: int = Field(gt=0)


class LocalQuotaAdmission(Frozen):
    """Request authorization with local-ledger budgeting, not verified headroom.

    The Stage A bridge accepts a matching LocalStageARecord under this policy.
    Unknown usage outside this ledger is not represented as measured zero.
    """
    organization: Text
    project: Text
    credential_id: Text
    credential_sha256: Hash
    request_id: Text
    request_sha256: Hash
    configuration_sha256: Hash
    authorization: Text
    state: Literal["local_tracked"] = "local_tracked"
    windows: tuple[QuotaLimit, ...]
    project_limits_apply: bool = False
    organization_split_metrics: tuple[Literal["ITPM", "OTPM"], ...] = ()
    project_split_metrics: tuple[Literal["ITPM", "OTPM"], ...] = ()

    def check(self, identity, request_id, request_hash, config_hash, now):
        if any(getattr(self, f) != getattr(identity, f) for f in
               ("organization", "project", "credential_id", "credential_sha256")):
            raise SchedulerHold("Admission identity mismatch")
        if (self.request_id, self.request_sha256, self.configuration_sha256) != (request_id, request_hash, config_hash):
            raise SchedulerHold("Admission request/configuration mismatch")
        if not identity.valid_at(now):
            raise SchedulerHold("Identity review expired or future-dated")
        expected = {("organization", m) for m in METRICS}
        if self.project_limits_apply:
            expected.update(("project", m) for m in METRICS)
        elif self.project_split_metrics:
            raise SchedulerHold("Contradictory project applicability")
        for scope, metrics in (("organization", self.organization_split_metrics), ("project", self.project_split_metrics)):
            if len(metrics) != len(set(metrics)):
                raise SchedulerHold("Duplicate split metric")
            expected.update((scope, m) for m in metrics)
        rows = {(w.scope, w.metric): w for w in self.windows}
        if len(rows) != len(self.windows) or set(rows) != expected:
            raise SchedulerHold("Incomplete or duplicate quota inventory")
        for w in self.windows:
            org = rows.get(("organization", w.metric))
            if w.scope == "project" and org and w.limit > org.limit:
                raise SchedulerHold("Project ceiling exceeds organization ceiling")


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def configuration_fingerprint(configuration):
    import inspect
    from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT,build_extraction_prompt
    from app.extraction.quote_catalog import chunk_prompt,catalog,resolve_response
    if configuration.wire_format == 'compact_field_rows_quiz_v4':
        from app.extraction import quiz_mcq
        previous = configuration.model_copy(update={'wire_format': 'compact_field_rows_quiz_v3'})
        return digest({'base': configuration_fingerprint(previous), 'config': configuration.model_dump(),
                       'quiz_mcq': inspect.getsource(quiz_mcq)})
    if configuration.wire_format == 'compact_field_rows_quiz_v3':
        from app.extraction import quiz_optional
        previous = configuration.model_copy(update={'wire_format': 'compact_field_rows_quiz_v2'})
        return digest({'base': configuration_fingerprint(previous), 'config': configuration.model_dump(),
                       'optional_quiz': inspect.getsource(quiz_optional)})
    if configuration.wire_format == 'compact_field_rows_quiz_v2':
        from app.extraction import quiz_topics
        legacy = configuration.model_copy(update={'wire_format': 'compact_field_rows_quiz_v1'})
        return digest({'base': configuration_fingerprint(legacy), 'config': configuration.model_dump(),
                       'topics': inspect.getsource(quiz_topics)})
    return digest({'config':configuration.model_dump(),'system':EXTRACTION_SYSTEM_PROMPT,
        'compact_wire':inspect.getsource(__import__('app.extraction.compact_claim_wire',fromlist=['VERSION'])) if configuration.wire_format=='compact_claim_table_v1' else None,
        'field_row_wire':(inspect.getsource(__import__('app.extraction.field_row_wire',fromlist=['VERSION'])) + inspect.getsource(__import__('app.extraction.quiz_wire',fromlist=['VERSION'])) if configuration.wire_format=='compact_field_rows_quiz_v1' else inspect.getsource(__import__('app.extraction.field_row_wire',fromlist=['VERSION'])) if configuration.wire_format=='compact_field_rows_v1' else None),
        'typed_claim_wire':inspect.getsource(__import__('app.extraction.typed_claim_wire',fromlist=['VERSION'])) if configuration.wire_format=='typed_claim_refs_v1' else None,
        'category_wire':inspect.getsource(__import__('app.extraction.category_wire',fromlist=['system'])) if configuration.wire_format=='category_bounded_12a_v1' else None,
        'prompt_builder':inspect.getsource(build_extraction_prompt),
        'catalog':inspect.getsource(catalog),'chunk_prompt':inspect.getsource(chunk_prompt),
        'resolver':inspect.getsource(resolve_response),
        'canonical_policy':inspect.getsource(__import__('app.extraction.canonical_grounding',fromlist=['SYSTEM'])),
        'claim_review':inspect.getsource(__import__('app.extraction.claim_review',fromlist=['review_claim'])),
        'context_policy':inspect.getsource(__import__('app.extraction.context_grounding',fromlist=['SYSTEM'])),
        'context_selection':inspect.getsource(__import__('app.extraction.source_context',fromlist=['select_context'])),
        'grounded_fields':inspect.getsource(__import__('app.extraction.grounded_fields',fromlist=['SYSTEM']))})


class OrganizationScheduler:
    """One active operation globally: success-ordered rotation is deterministic.

    Cross-process callers receive HOLD while busy; no lease expiry releases claims.
    Each network attempt has its own conservative reservation, including retries.
    """
    def __init__(self, path, organizations, configuration=SHARED_CONFIGURATION, *, configuration_review=None,
                 rotation_slots=(1, 2, 3, 4, 5), parallel=False):
        self.path = Path(path)
        self.parallel = parallel
        self.organizations = organizations
        self.rotation_slots = tuple(rotation_slots)
        if self.rotation_slots not in ((1, 2, 3, 4, 5), (6, 7, 8, 9, 10)) or not set(organizations.enabled) <= set(self.rotation_slots):
            raise SchedulerHold('Invalid organization rotation group')
        if parallel and (self.rotation_slots != (1, 2, 3, 4, 5) or configuration.max_retries != 0):
            raise SchedulerHold('Parallel Round 1 requires slots 1–5 and the approved retry configuration')
        self._configuration = configuration
        from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
        import inspect
        self.config_hash = configuration_fingerprint(configuration)
        identities = [i.model_dump() for i in organizations.identities]
        organizations.check_metadata(identities)
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS scheduler (id INTEGER PRIMARY KEY CHECK(id=1), cursor INTEGER NOT NULL, active TEXT, config TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS organizations (slot INTEGER PRIMARY KEY, org TEXT UNIQUE NOT NULL, project TEXT NOT NULL, identity TEXT NOT NULL, blocked TEXT, cooldown REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, org TEXT NOT NULL, slot INTEGER NOT NULL, request_hash TEXT NOT NULL, state TEXT NOT NULL, admission TEXT NOT NULL, created REAL NOT NULL, completed REAL, validation TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts (request_id TEXT NOT NULL, number INTEGER NOT NULL, created REAL NOT NULL, dispatched REAL, completed REAL, input_reserved INTEGER NOT NULL, output_reserved INTEGER NOT NULL, input_actual INTEGER, output_actual INTEGER, reasoning INTEGER, charged INTEGER NOT NULL, http_status INTEGER, finish TEXT, duration REAL, category TEXT, PRIMARY KEY(request_id,number));
                CREATE TABLE IF NOT EXISTS audit_events (sequence INTEGER PRIMARY KEY, request_id TEXT, org TEXT, created REAL NOT NULL, event TEXT NOT NULL, details TEXT NOT NULL);
            """)
        # executescript commits implicitly; initialization bindings use a separate transaction.
        with self.transaction() as db:
            if self.rotation_slots[0] == 1:
                db.execute("INSERT OR IGNORE INTO scheduler VALUES(1,1,NULL,?)", (self.config_hash,))
                db.execute("UPDATE scheduler SET config=? WHERE id=1 AND config='unconfigured' AND active IS NULL",
                           (self.config_hash,))
                old = db.execute("SELECT config,active FROM scheduler WHERE id=1").fetchone()
            else:
                db.execute("INSERT OR IGNORE INTO scheduler VALUES(1,1,NULL,'unconfigured')")
                db.execute("CREATE TABLE IF NOT EXISTS scheduler_group_config (first_slot INTEGER PRIMARY KEY, config TEXT NOT NULL)")
                db.execute("INSERT OR IGNORE INTO scheduler_group_config VALUES(6,?)", (self.config_hash,))
                old = db.execute("SELECT g.config,s.active FROM scheduler_group_config g CROSS JOIN scheduler s "
                                 "WHERE g.first_slot=6 AND s.id=1").fetchone()
            if old[0] != self.config_hash:
                if (not isinstance(configuration_review,dict) or configuration_review.get('target_sha256')!=self.config_hash
                        or not configuration_review.get('evidence') or old[1] is not None):
                    raise SchedulerHold("Shared extraction configuration changed; review required")
                organizations.check_metadata(configuration_review)
                if self.rotation_slots[0] == 1:
                    db.execute('UPDATE scheduler SET config=? WHERE id=1', (self.config_hash,))
                else:
                    db.execute('UPDATE scheduler_group_config SET config=? WHERE first_slot=6', (self.config_hash,))
                self._event(db,None,None,'configuration_review',{'old':old[0],'new':self.config_hash,'evidence':configuration_review})
            for identity in organizations.identities:
                row = db.execute("SELECT identity FROM organizations WHERE slot=?", (identity.slot,)).fetchone()
                encoded = json.dumps(identity.model_dump(), sort_keys=True)
                if row and row[0] != encoded:
                    raise SchedulerHold("Registered identity changed; explicit review required")
                db.execute("INSERT OR IGNORE INTO organizations(slot,org,project,identity) VALUES(?,?,?,?)",
                           (identity.slot, identity.organization, identity.project, encoded))

    @property
    def configuration(self):
        return self._configuration

    def _rotation(self, cursor):
        slots = self.rotation_slots
        start = slots.index(cursor) if cursor in slots else 0
        return slots[start:] + slots[:start]

    def _group_cursor(self, db, cursor):
        if self.rotation_slots[0] == 1:
            return cursor
        last = db.execute("SELECT slot FROM operations WHERE slot BETWEEN 6 AND 10 AND state='success' "
                          "ORDER BY completed DESC, rowid DESC LIMIT 1").fetchone()
        return self._rotation(last['slot'])[1] if last else 6

    def _event(self, db, request_id, org, event, details):
        self.organizations.check_metadata(details)
        db.execute("INSERT INTO audit_events(request_id,org,created,event,details) VALUES(?,?,?,?,?)",
                   (request_id, org, time.time(), event, json.dumps(details, sort_keys=True)))

    def review_organization(self, updated_registry, slot, evidence):
        """Explicit administrative repair, not an automatic rotation/claim release.

        Caller must independently protect this operator entry point. Existing usage
        and claims remain charged. Organization/project identity cannot be reassigned.
        """
        if not isinstance(evidence, str) or not evidence.strip():
            raise SchedulerHold("Explicit repair review evidence required")
        identity = next((i for i in updated_registry.identities if i.slot == slot), None)
        if identity is None or slot not in updated_registry.enabled:
            raise SchedulerHold("Reviewed enabled identity required")
        updated_registry.key(identity)
        updated_registry.check_metadata([evidence, identity.model_dump()])
        now = time.time()
        if not identity.valid_at(now):
            raise SchedulerHold("Identity review is not current")
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM operations WHERE state='claimed'").fetchone():
                raise SchedulerHold("Cannot repair while an operation is active")
            old = db.execute("SELECT * FROM organizations WHERE slot=?", (slot,)).fetchone()
            if not old or (old["org"], old["project"]) != (identity.organization, identity.project):
                raise SchedulerHold("Repair cannot reassign organization/project quota")
            for other in updated_registry.identities:
                if other.slot != slot:
                    row = db.execute("SELECT identity FROM organizations WHERE slot=?", (other.slot,)).fetchone()
                    if not row or row[0] != json.dumps(other.model_dump(), sort_keys=True):
                        raise SchedulerHold("Repair changed an unrelated identity")
            db.execute("UPDATE organizations SET identity=?,blocked=NULL WHERE slot=?",
                       (json.dumps(identity.model_dump(), sort_keys=True), slot))
            self._event(db, None, identity.organization, "operator_identity_review", {"evidence": evidence})
        # Cooldown, usage and unresolved claims are deliberately not cleared.
        self.organizations = updated_registry

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            with db:
                yield db
        finally:
            db.close()

    def _capacity(self, db, identity, admission, input_tokens, output_tokens, now):
        for w in admission.windows:
            seconds = 86400 if w.metric in ("RPD", "TPD") else 60
            rows = db.execute("""SELECT a.* FROM attempts a JOIN operations o ON o.id=a.request_id
                WHERE o.org=? AND (o.state='claimed' OR COALESCE(a.completed,o.completed,a.dispatched,a.created)>?)""",
                (identity.organization, now - seconds)).fetchall()
            if w.metric in ("RPM", "RPD"):
                local, planned = len(rows), 1
            elif w.metric == "ITPM":
                local = sum(r["input_actual"] if r["input_actual"] is not None else r["input_reserved"] for r in rows)
                planned = input_tokens
            elif w.metric == "OTPM":
                local = sum(r["output_actual"] if r["output_actual"] is not None else r["output_reserved"] for r in rows)
                planned = output_tokens
            else:
                local, planned = sum(r["charged"] for r in rows), input_tokens + output_tokens
            configured = dict(zip(METRICS, self.configuration.scheduler_ceilings))
            ceiling = quota_ceiling(w.limit,w.metric,configured)
            # Local mode has total limits only. It makes no external-usage claim.
            external = 0 if isinstance(admission, LocalQuotaAdmission) else w.used + w.outstanding
            if external + local + planned > ceiling:
                raise SchedulerHold(f"quota_exhausted: insufficient aggregate {w.metric} headroom")

    def claim(self, request_id, request_hash, input_tokens, output_tokens, admissions):
        if not isinstance(request_id, str) or not request_id.strip():
            raise SchedulerHold("Unique request ID required")
        if any(type(n) is not int or n <= 0 for n in (input_tokens, output_tokens)):
            raise SchedulerHold("Positive token reservation required")
        self.organizations.check_metadata([request_id, request_hash])
        for a in admissions.values():
            self.organizations.check_metadata(a.model_dump())
        with self.transaction() as db:
            if db.execute("SELECT 1 FROM operations WHERE id=?", (request_id,)).fetchone():
                raise SchedulerHold("Request already claimed; cannot redispatch")
            state = db.execute("SELECT * FROM scheduler WHERE id=1").fetchone()
            if state["active"] is not None or (not self.parallel and db.execute(
                    "SELECT 1 FROM operations WHERE state='claimed'").fetchone()):
                raise SchedulerHold("Another operation is active; crashed claims require review")
            now = time.time()
            identities = {i.slot: i for i in self.organizations.identities}
            for slot in self._rotation(self._group_cursor(db, state['cursor'])):
                if self.parallel and db.execute(
                        "SELECT 1 FROM operations WHERE slot=? AND state='claimed'", (slot,)).fetchone():
                    continue
                if slot not in self.organizations.enabled:
                    continue
                identity = identities[slot]
                eligibility = db.execute("SELECT * FROM organizations WHERE slot=?", (slot,)).fetchone()
                if eligibility["identity"] != json.dumps(identity.model_dump(), sort_keys=True):
                    raise SchedulerHold("Worker identity is stale after operator review")
                if eligibility["blocked"] or eligibility["cooldown"] > now:
                    continue
                admission = admissions.get(identity.organization)
                if admission is None:
                    continue
                try:
                    admission.check(identity, request_id, request_hash, self.config_hash, now)
                    self.organizations.key(identity)
                    self._capacity(db, identity, admission, input_tokens, output_tokens, now)
                except SchedulerHold:
                    continue
                # Keep evidence and fingerprint binding, but no secret material.
                db.execute("INSERT INTO operations VALUES(?,?,?,?,? ,?,?,NULL,?)",
                           (request_id, identity.organization, slot, request_hash, "claimed",
                            admission.model_dump_json(), now, "not_run"))
                if not self.parallel:
                    db.execute("UPDATE scheduler SET active=? WHERE id=1", (request_id,))
                self._reserve(db, request_id, 1, input_tokens, output_tokens, now)
                self._event(db, request_id, identity.organization, "claimed", {
                    "model": MODEL, "selection_reason": "success_ordered_round_robin_first_verified_eligible",
                    "quota_before": admission.state, "quota_after": "reservation_charged",
                    "estimated_input": input_tokens, "reserved_completion": output_tokens,
                    "configuration_sha256": self.config_hash})
                from app.extraction.quota_policy import active_quota_exception
                exception = active_quota_exception()
                if exception:
                    self._event(db, request_id, identity.organization, 'operator_quota_exception', exception)
                return identity, admission
            raise SchedulerHold("No eligible organization with verified admission and headroom")

    @staticmethod
    def _reserve(db, request_id, number, input_tokens, output_tokens, now):
        db.execute("""INSERT INTO attempts(request_id,number,created,input_reserved,output_reserved,charged)
                      VALUES(?,?,?,?,?,?)""", (request_id, number, now, input_tokens, output_tokens, input_tokens + output_tokens))

    def retry(self, request_id, identity, admission, input_tokens, output_tokens):
        with self.transaction() as db:
            op = db.execute("SELECT * FROM operations WHERE id=?", (request_id,)).fetchone()
            if not op or op["state"] != "claimed" or op["org"] != identity.organization:
                raise SchedulerHold("Retry is not bound to the active operation")
            n = db.execute("SELECT count(*) FROM attempts WHERE request_id=?", (request_id,)).fetchone()[0]
            if n > self.configuration.max_retries:
                raise SchedulerHold("Retry budget exhausted")
            now = time.time()
            admission.check(identity, request_id, op["request_hash"], self.config_hash, now)
            self._capacity(db, identity, admission, input_tokens, output_tokens, now)
            self._reserve(db, request_id, n + 1, input_tokens, output_tokens, now)
            self._event(db, request_id, identity.organization, "retry_reserved", {"retry_count": n, "same_organization": True})

    def check_dispatch(self, request_id, identity, admission):
        with self.transaction() as db:
            op = db.execute("SELECT * FROM operations WHERE id=?", (request_id,)).fetchone()
            org = db.execute("SELECT * FROM organizations WHERE slot=?", (identity.slot,)).fetchone()
            active = db.execute("SELECT active FROM scheduler WHERE id=1").fetchone()[0]
            if (not op or op["state"] != "claimed" or (not self.parallel and active != request_id) or op["org"] != identity.organization
                    or not org or org["blocked"] or org["cooldown"] > time.time()
                    or org["identity"] != json.dumps(identity.model_dump(), sort_keys=True)):
                raise SchedulerHold("Dispatch claim or organization eligibility changed")
            admission.check(identity, request_id, op["request_hash"], self.config_hash, time.time())
            self.organizations.key(identity)
            attempt = db.execute("SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1", (request_id,)).fetchone()
            if attempt["dispatched"] is not None:
                raise SchedulerHold("Attempt already dispatched; cannot send twice")
            db.execute("UPDATE attempts SET dispatched=? WHERE request_id=? AND number=?", (time.time(), request_id, attempt["number"]))
            self._event(db, request_id, identity.organization, "dispatch_attempt", {"attempt": attempt["number"]})

    def record_attempt(self, request_id, *, usage=None, http_status=None, finish=None, duration=0,
                       category=None, uncertain=False, diagnostics=None):
        usage = usage or {}
        def count(name):
            n = usage.get(name)
            return n if type(n) is int and n >= 0 else None
        inp, out, total = (count(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens"))
        details = usage.get("completion_tokens_details") or {}
        reasoning = details.get("reasoning_tokens") if isinstance(details, dict) else None
        reasoning = reasoning if type(reasoning) is int and reasoning >= 0 else None
        # Reasoning is a subset of completion tokens, not an additional charge.
        if reasoning is not None and (out is None or reasoning > out):
            inp = out = total = None
        if inp is None or out is None or (total is not None and total < inp + out):
            inp = out = total = None
        self.organizations.check_metadata([finish, category])
        with self.transaction() as db:
            row = db.execute("SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1", (request_id,)).fetchone()
            op = db.execute("SELECT * FROM operations WHERE id=?", (request_id,)).fetchone()
            if not row or not op or op["state"] != "claimed" or row["category"] is not None:
                raise SchedulerHold("Attempt already recorded or operation is not active")
            charged = max(inp + out, total or 0) if inp is not None else row["charged"]
            # Any unexplained total excess is also charged to input for split limits.
            if inp is not None:
                inp += charged - inp - out
            db.execute("""UPDATE attempts SET completed=?,input_actual=?,output_actual=?,reasoning=?,charged=?,
                http_status=?,finish=?,duration=?,category=? WHERE request_id=? AND number=?""",
                (None if uncertain else time.time(), inp, out, reasoning, charged, http_status, finish, duration,
                 category or "response", request_id, row["number"]))
            if diagnostics:
                self._event(db, request_id, op["org"], "provider_error", diagnostics)

    def close_undispatched(self,request_id,evidence):
        """Close a proven pre-dispatch legacy attempt; retain its entire charge."""
        if not evidence: raise SchedulerHold('Pre-dispatch reconciliation evidence required')
        self.organizations.check_metadata(evidence)
        with self.transaction() as db:
            op=db.execute('SELECT * FROM operations WHERE id=?',(request_id,)).fetchone()
            a=db.execute('SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',(request_id,)).fetchone()
            if (not op or not a or op['state'] not in ('failed','validation_failed') or op['completed'] is None
                or a['dispatched'] is not None or a['http_status'] is not None or a['category'] is not None or a['completed'] is not None):
                raise SchedulerHold('Attempt is not proven completed before dispatch')
            if db.execute("SELECT 1 FROM operations WHERE state='claimed'").fetchone():
                raise SchedulerHold('Cannot reconcile while active')
            db.execute('UPDATE attempts SET completed=?,category=?,input_actual=0,output_actual=0 WHERE request_id=? AND number=?',
                       (op['completed'],'not_dispatched',request_id,a['number']))
            self._event(db,request_id,op['org'],'undispatched_attempt_closed',dict(evidence=evidence,charge_preserved=a['charged'],redispatched=False))

    def finish(self, request_id, outcome, *, status=None, retry_after=None):
        if outcome not in ("success", "failed", "uncertain", "validation_failed"):
            raise SchedulerHold("Invalid operation outcome")
        with self.transaction() as db:
            row = db.execute("SELECT * FROM operations WHERE id=?", (request_id,)).fetchone()
            if not row or row["state"] != "claimed":
                raise SchedulerHold("Operation is not active")
            latest = db.execute("SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1", (request_id,)).fetchone()
            if latest['dispatched'] is None and latest['category'] is None and latest['completed'] is None and outcome in ('failed','validation_failed'):
                # Authorization can fail after reservation but before any HTTP call.
                # Close its lifecycle without deleting or reducing reserved charges.
                db.execute('UPDATE attempts SET completed=?,category=?,input_actual=0,output_actual=0 WHERE request_id=? AND number=?',
                           (time.time(),'not_dispatched',request_id,latest['number']))
                self._event(db,request_id,row['org'],'undispatched_attempt_closed',dict(charge_preserved=latest['charged'],redispatched=False))
            if outcome == "success" and (latest["category"] != "response" or latest["completed"] is None):
                raise SchedulerHold("Unresolved attempt cannot be successful")
            if status in (401, 403):
                db.execute("UPDATE organizations SET blocked=? WHERE slot=?", (str(status), row["slot"]))
            if status == 429:
                delay = retry_after if isinstance(retry_after, (int, float)) and math.isfinite(retry_after) else 60
                db.execute("UPDATE organizations SET cooldown=? WHERE slot=?", (time.time() + max(1, delay), row["slot"]))
            db.execute("UPDATE operations SET state=?,completed=?,validation=? WHERE id=?",
                       (outcome, time.time(), "passed_mechanical_only" if outcome == "success" else outcome, request_id))
            if self.rotation_slots[0] == 1 and outcome == 'success':
                db.execute("UPDATE scheduler SET active=NULL,cursor=? WHERE id=1", (self._rotation(row['slot'])[1],))
            else:
                db.execute("UPDATE scheduler SET active=NULL WHERE id=1")
            self._event(db, request_id, row["org"], "completed", {
                "model": MODEL, "extraction_outcome": outcome,
                "validation_outcome": "passed_mechanical_only" if outcome == "success" else "not_passed",
                "semantic_entailment_verified": False,
                "quota_after": "rate_limited" if status == 429 else "quota_unknown",
                "retry_count": latest["number"] - 1})

    def status(self, admissions=None, input_tokens=0, output_tokens=0):
        """Secret-free historical status; never represents old observations as current headroom."""
        with self.transaction() as db:
            state = dict(db.execute("SELECT * FROM scheduler WHERE id=1").fetchone())
            slots = []
            for slot in self.rotation_slots:
                org = db.execute("SELECT * FROM organizations WHERE slot=?", (slot,)).fetchone()
                last = db.execute("SELECT * FROM operations WHERE slot=? ORDER BY created DESC LIMIT 1", (slot,)).fetchone()
                attempts = [dict(r) for r in db.execute("SELECT a.* FROM attempts a JOIN operations o ON o.id=a.request_id WHERE o.slot=?", (slot,))]
                admission = json.loads(last["admission"]) if last else None
                current = (admissions or {}).get(org["org"]) if org else None
                quota_state = "quota_unknown"
                if current and org:
                    quota_state = current.state
                    try:
                        identity = Identity.model_validate_json(org["identity"])
                        current.check(identity, current.request_id, current.request_sha256, self.config_hash, time.time())
                        self._capacity(db, identity, current, input_tokens, output_tokens, time.time())
                    except SchedulerHold as exc:
                        quota_state = "quota_exhausted" if str(exc).startswith("quota_exhausted") else (
                            current.state if current.state in ("quota_estimated", "quota_exhausted") else "quota_unknown")
                    if db.execute("SELECT 1 FROM operations WHERE id=?", (current.request_id,)).fetchone():
                        quota_state = "quota_unknown"
                rate_limited = bool(org and org["cooldown"] > time.time())
                if rate_limited:
                    quota_state = "quota_exhausted"
                slots.append({"slot": slot, "enabled": slot in self.organizations.enabled,
                              "organization": org["org"] if org else None,
                              "identity_verified": org is not None and Identity.model_validate_json(org["identity"]).valid_at(time.time()),
                              "model_access": org["blocked"] if org and org["blocked"] else "not_blocked_not_proven",
                              "cooldown_until": org["cooldown"] if org else None,
                              "eligibility": "rate_limited" if rate_limited else ("blocked" if org and org["blocked"] else "requires_admission"),
                              "quota_state": quota_state, "last_admission_state": admission["state"] if admission else None,
                              "configured_ceilings": dict(zip(METRICS, self.configuration.scheduler_ceilings)),
                              "budgets": [{"scope": w["scope"], "metric": w["metric"], "limit": w["limit"], "internal": quota_ceiling(w["limit"],w["metric"],dict(zip(METRICS,self.configuration.scheduler_ceilings)))} for w in admission["windows"]] if admission else [],
                              "last_outcome": last["state"] if last else None, "attempts": attempts,
                              "tracked_usage": {"minute_tokens": sum(a["charged"] for a in attempts if a["completed"] is None or a["completed"] > time.time() - 60),
                                                "daily_tokens": sum(a["charged"] for a in attempts if a["completed"] is None or a["completed"] > time.time() - 86400)},
                              "outstanding_reservations": sum(a["charged"] for a in attempts if a["completed"] is None)})
            next_org = None
            by_slot = {record['slot']: record for record in slots}
            cursor = self._group_cursor(db, state['cursor'])
            for slot_number in self._rotation(cursor):
                slot = by_slot[slot_number]
                if (state["active"] is None and slot["enabled"] and slot["quota_state"] == "quota_verified"
                        and slot["model_access"] == "not_blocked_not_proven" and slot["cooldown_until"] <= time.time()):
                    next_org = slot["organization"]
                    break
            return {"model": MODEL, "cursor": cursor, "active_request": state["active"],
                    "next_eligible_organization": next_org, "eligibility_note": "Snapshot only; claim rechecks admission atomically",
                    "slots": slots}
