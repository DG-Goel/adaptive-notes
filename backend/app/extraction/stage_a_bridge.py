"""Opt-in bridge to the unchanged, fixed-payload Stage A harness."""
import importlib.util
from pathlib import Path
import time
from app.extraction.quota_policy import quota_ceiling,UTILIZATION_FRACTION

from app.extraction.organization_scheduler import SchedulerHold, digest
from app.extraction.organization_scheduler import Frozen, Text, Hash, LocalQuotaAdmission, QuotaLimit, METRICS
from pydantic import Field
from typing import Literal
from app.extraction.organization_scheduler import Stamp
from hashlib import sha256
from hmac import compare_digest


class LocalCredentialApproval(Frozen):
    provider: Literal['Groq']
    model: Literal['openai/gpt-oss-120b']
    stage: Literal['A']
    credential_id: Text
    credential_sha256: Hash
    organization: Text
    project: Text
    evidence_kind: Literal['operator_reviewed_console_inventory', 'operator_reviewed_provider_record']
    ownership_evidence: Text
    verified_by: Text
    verified_at: Stamp
    expires_at: Stamp | None
    operator: Text
    authorization: Text
    authorization_evidence: Text
    run_id: Text
    request_sha256: Hash


def verify_local_credential(record, approval, key, now):
    fields = ('provider', 'model', 'stage', 'credential_id', 'organization', 'project',
              'operator', 'authorization', 'run_id', 'request_sha256')
    if any(getattr(record, f) != getattr(approval, f) for f in fields):
        raise SchedulerHold('Credential inventory or authorization binding mismatch')
    if approval.verified_at > now or (approval.expires_at is not None and now >= approval.expires_at):
        raise SchedulerHold('Credential approval is expired or future-dated')
    if not (key and compare_digest(record.credential_sha256, approval.credential_sha256)
            and compare_digest(sha256(key.encode()).hexdigest(), approval.credential_sha256)):
        raise SchedulerHold('Selected credential does not match the trusted inventory')


class LocalStageARecord(Frozen):
    """Stage A authorization under the total-limit policy; no usage attestations."""
    decision: Literal["PASS"]
    stage: Literal["A"]
    provider: Literal["Groq"]
    model: Literal["openai/gpt-oss-120b"]
    source_id: Literal["T0022"]
    run_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
    organization: Text
    project: Text
    operator: Text
    authorization: Text
    credential_id: Text
    credential_sha256: Hash
    request_sha256: Hash
    limits: tuple[QuotaLimit, ...]


from threading import Lock

_harness_import_lock = Lock()

def frozen_harness():
    with _harness_import_lock:
        return _load_frozen_harness()

def _load_frozen_harness():
    path = Path(__file__).resolve().parents[2] / "data/output/t0022_stage_a_admission_v2_20261104_125816/live_stage_a.py"
    # The frozen harness uses sibling imports. Keep their resolution explicit.
    import sys
    directory = str(path.parent)
    sys.path.insert(0, directory)
    try:
        spec = importlib.util.spec_from_file_location("groq_frozen_live_stage_a", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(directory)


class StageAAuthorization:
    """Caller-supplied genuine records. Constructing this grants no admission."""
    def __init__(self, record, approval):
        self.record = record
        self.approval = approval

    def claim(self, scheduler, identity, admission, request_id, payload, budget):
        harness = frozen_harness()
        local = isinstance(admission, LocalQuotaAdmission)
        record = (self.local_record_type() if local else harness.Admission).model_validate(self.record)
        approval = (LocalCredentialApproval if local else harness.CredentialApproval).model_validate(self.approval)
        expected = self.expected_payload(request_id)
        if payload != expected:
            raise SchedulerHold("Frozen Stage A authorizes a different exact payload")
        if not self.permits_registry(scheduler) or scheduler.configuration.max_retries != 0:
            raise SchedulerHold("Live Stage A requires a permitted organization registry and no automatic retries")
        if (record.run_id != request_id or record.request_sha256 != digest(payload)
                or record.organization != identity.organization or record.project != identity.project
                or record.credential_id != identity.credential_id
                or record.credential_sha256 != identity.credential_sha256):
            raise SchedulerHold("Stage A request/run/identity binding mismatch")
        verifier = verify_local_credential if local else harness.verify_credential
        verifier(record, approval, scheduler.organizations.key(identity), time.time())
        if local:
            self._claim_local(harness, scheduler, identity, admission, request_id, payload, budget, record)
            return
        # Both gates must describe the same external quota evidence.
        windows = [window.model_dump() for window in admission.windows]
        if windows != [window.model_dump() for window in record.windows]:
            raise SchedulerHold("Stage A quota evidence differs from scheduler admission")
        root = harness.LIVE_STATE
        root.mkdir(parents=True, exist_ok=True)
        harness.QuotaLedger(root / "quota.sqlite").claim(record, budget, UTILIZATION_FRACTION)
        run_dir = root / record.run_id
        run_dir.mkdir(exist_ok=False)
        harness.Ledger(run_dir, record.run_id).claim("A", {
            "authorization": record.authorization, "request_sha256": record.request_sha256})
        # Claims remain conservatively charged after any uncertain outcome.

    def permits_registry(self,scheduler):
        return len(scheduler.organizations.enabled)==1

    def expected_payload(self, request_id):
        return frozen_harness().request_plan()[0]

    def local_record_type(self):
        return LocalStageARecord

    def _claim_local(self, harness, scheduler, identity, admission, request_id, payload, budget, record):
        admission.check(identity, request_id, digest(payload), scheduler.config_hash, time.time())
        if record.authorization != admission.authorization:
            raise SchedulerHold("Stage A authorization differs from scheduler admission")
        if sorted((w.scope, w.metric, w.limit) for w in record.limits) != sorted(
                (w.scope, w.metric, w.limit) for w in admission.windows):
            raise SchedulerHold("Stage A total limits differ from scheduler admission")
        with scheduler.transaction() as db:
            operation = db.execute("SELECT * FROM operations WHERE id=?", (request_id,)).fetchone()
            active = db.execute("SELECT active FROM scheduler WHERE id=1").fetchone()[0]
            attempt = db.execute('SELECT * FROM attempts WHERE request_id=? ORDER BY number DESC LIMIT 1',
                                 (request_id,)).fetchone()
            if (not operation or operation['state'] != 'claimed' or (not scheduler.parallel and active != request_id)
                    or operation['org'] != identity.organization or operation['request_hash'] != digest(payload)
                    or operation['admission'] != admission.model_dump_json()):
                raise SchedulerHold("Stage A requires the bound scheduler reservation")
            if (not attempt or attempt['input_reserved'] != budget.input_tokens
                    or attempt['output_reserved'] != budget.max_output_tokens
                    or budget.total_tokens != budget.input_tokens + budget.max_output_tokens
                    or payload.get('max_completion_tokens', payload.get('max_tokens')) != budget.max_output_tokens):
                raise SchedulerHold('Stage A budget differs from scheduler reservation')
        root = harness.LIVE_STATE
        root.mkdir(parents=True, exist_ok=True)
        # Reuse the frozen harness's physical quota database so its old claims,
        # concurrent workers and unresolved requests remain charged, not reset.
        ledger = harness.QuotaLedger(root / 'quota.sqlite')
        ceilings = dict(zip(METRICS, scheduler.configuration.scheduler_ceilings))
        with ledger.transaction() as db:
            now = time.time()
            if db.execute('SELECT 1 FROM live_a_claims WHERE run_id=?', (request_id,)).fetchone():
                raise SchedulerHold('Stage A claim already consumed')
            for w in record.limits:
                seconds = 86400 if w.metric in ('RPD', 'TPD') else 60
                rows = db.execute('''SELECT input_tokens,output_tokens FROM live_a_claims
                    WHERE org=? AND (?='organization' OR project=?)
                    AND COALESCE(completed,claimed)>?''',
                    (identity.organization, w.scope, identity.project, now-seconds)).fetchall()
                if w.metric in ('RPM', 'RPD'):
                    used, planned = len(rows), 1
                elif w.metric == 'ITPM':
                    used, planned = sum(r[0] for r in rows), budget.input_tokens
                elif w.metric == 'OTPM':
                    used, planned = sum(r[1] for r in rows), budget.max_output_tokens
                else:
                    used, planned = sum(r[0]+r[1] for r in rows), budget.total_tokens
                ceiling = quota_ceiling(w.limit,w.metric,ceilings)
                if used + planned > ceiling:
                    raise SchedulerHold('quota_exhausted: Stage A local 85% ceiling')
            db.execute('''INSERT INTO live_a_claims VALUES
                (?,?,?,?,NULL,?,?,'claimed',?,?)''',
                (request_id, identity.organization, identity.project, now,
                 budget.input_tokens, budget.max_output_tokens, digest(payload), record.authorization))
        run_dir = root / request_id
        run_dir.mkdir(exist_ok=False)
        harness.Ledger(run_dir, request_id).claim('A', {
            'authorization': record.authorization, 'request_sha256': record.request_sha256,
            'quota_policy': 'local_85_percent_of_total'})

    def reconcile_local(self, scheduler, request_id):
        """Complete rolling windows only for confirmed attempts; retain uncertainty."""
        with scheduler.transaction() as db:
            op = db.execute('SELECT admission FROM operations WHERE id=?', (request_id,)).fetchone()
            if not op:
                return
            import json
            if json.loads(op['admission']).get('state') != 'local_tracked':
                return
            attempts = db.execute('SELECT * FROM attempts WHERE request_id=?', (request_id,)).fetchall()
        harness = frozen_harness()
        path = harness.LIVE_STATE / 'quota.sqlite'
        if not path.exists():
            return
        confirmed = bool(attempts) and all(a['completed'] is not None for a in attempts)
        usage = {'prompt_tokens': sum(a['input_actual'] if a['input_actual'] is not None else a['input_reserved'] for a in attempts),
                 'completion_tokens': sum(a['output_actual'] if a['output_actual'] is not None else a['output_reserved'] for a in attempts)}
        # Local policy reconciles confirmed usage to actual ledger charges. Missing
        # usage still uses reserved counts. Uncertain claims age from reservation time.
        with harness.QuotaLedger(path).transaction() as db:
            db.execute('''UPDATE live_a_claims SET state=?,completed=?,input_tokens=?,output_tokens=?
                WHERE run_id=?''',('confirmed' if confirmed else 'uncertain',time.time() if confirmed else None,
                                  usage['prompt_tokens'],usage['completion_tokens'],request_id))
