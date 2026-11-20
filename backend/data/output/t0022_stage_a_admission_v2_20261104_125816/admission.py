"""Operator-attested admission and durable claims for one-shot Stage A."""
from contextlib import contextmanager
from pathlib import Path
from hashlib import sha256
from hmac import compare_digest
import sqlite3
import time
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Hold(ValueError):
    pass


FREE = {"RPM": 30, "RPD": 1000, "TPM": 8000, "TPD": 200000}
MINUTE = {"RPM", "TPM", "ITPM", "OTPM"}
REQUEST = {"RPM", "RPD"}


Nonblank = Annotated[str, Field(pattern=r"\S")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Timestamp = Annotated[float, Field(allow_inf_nan=False)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Limit(StrictModel):
    scope: Literal["organization", "project"]
    metric: Literal["RPM", "RPD", "TPM", "TPD", "ITPM", "OTPM"]
    limit: int = Field(gt=0)


class Window(Limit):
    data_as_of: Timestamp
    used: int = Field(ge=0)
    outstanding: int = Field(ge=0)
    evidence: Nonblank


class CredentialApproval(StrictModel):
    """Separately maintained trusted operator record, without embedded key material."""
    provider: Literal["Groq"]
    model: Literal["openai/gpt-oss-120b"]
    stage: Literal["A"]
    credential_id: Nonblank
    credential_sha256: Hash
    organization: Nonblank
    project: Nonblank
    evidence_kind: Literal["operator_reviewed_console_inventory", "operator_reviewed_provider_record"]
    ownership_evidence: Nonblank
    verified_by: Nonblank
    verified_at: Timestamp
    expires_at: Timestamp
    operator: Nonblank
    authorization: Nonblank
    authorization_evidence: Nonblank
    run_id: Nonblank
    request_sha256: Hash


def verify_credential(record, approval, key, now):
    approval = CredentialApproval.model_validate(approval.model_dump())
    fields = ("provider", "model", "stage", "credential_id", "organization", "project",
              "operator", "authorization", "run_id", "request_sha256")
    if any(getattr(record, field) != getattr(approval, field) for field in fields):
        raise Hold("Credential inventory or authorization binding mismatch")
    if not approval.verified_at <= now < approval.expires_at:
        raise Hold("Credential approval is expired or future-dated")
    if not (key and compare_digest(record.credential_sha256, approval.credential_sha256)
            and compare_digest(sha256(key.encode()).hexdigest(), approval.credential_sha256)):
        raise Hold("Selected credential does not match the trusted inventory")


class Admission(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: Literal["PASS"]
    stage: Literal["A"]
    provider: Literal["Groq"]
    model: Literal["openai/gpt-oss-120b"]
    source_id: Literal["T0022"]
    run_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
    organization: Nonblank
    project: Nonblank
    operator: Nonblank
    authorization: Nonblank
    credential_id: Nonblank
    credential_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_as_of: float = Field(allow_inf_nan=False)
    verified_at: float = Field(allow_inf_nan=False)
    control_until: float = Field(allow_inf_nan=False)
    traffic: Literal["controlled", "accounted"]
    coordination_evidence: Nonblank
    authoritative_limits: Literal[True]
    complete_limit_inventory: Literal[True]
    complete_usage_inventory: Literal[True]
    inventory_evidence: Nonblank
    project_limits_apply: bool
    organization_split_metrics: list[Literal["ITPM", "OTPM"]]
    project_split_metrics: list[Literal["ITPM", "OTPM"]]
    limits: list[Limit]
    windows: list[Window]


def validated_windows(record):
    expected = {("organization", metric) for metric in FREE}
    if record.project_limits_apply:
        expected.update(("project", metric) for metric in FREE)
    elif record.project_split_metrics:
        raise Hold("Project split limits contradict project applicability")
    for scope, metrics in (("organization", record.organization_split_metrics),
                           ("project", record.project_split_metrics)):
        if len(set(metrics)) != len(metrics):
            raise Hold("Duplicate split-limit declaration")
        expected.update((scope, metric) for metric in metrics)
    limits = {(row.scope, row.metric): row.limit for row in record.limits}
    windows = {(row.scope, row.metric): row for row in record.windows}
    if any(metric in {"RPD", "TPD"} and (scope, metric) not in windows
           for scope, metric in expected):
        raise Hold("Missing daily quota windows in the inventory")
    if (len(limits) != len(record.limits) or len(windows) != len(record.windows)
            or limits.keys() != expected or windows.keys() != expected):
        raise Hold("Missing or duplicate quota windows or inconsistent inventory")
    for (scope, metric), window in windows.items():
        if window.limit != limits[scope, metric]:
            raise Hold("Quota row contradicts the authoritative limit inventory")
        org_limit = limits.get(("organization", metric))
        if scope == "project" and org_limit is not None and window.limit > org_limit:
            raise Hold("Project limit contradicts the organization ceiling")
    return windows


def fresh(record, now):
    if not (0 <= now - record.data_as_of <= 15
            and record.data_as_of <= record.verified_at <= now
            and record.control_until >= now + 90):
        raise Hold("Stale evidence or traffic control expires too soon")
    if any(not 0 <= now - row.data_as_of <= 15 or row.data_as_of > record.verified_at
           for row in record.windows):
        raise Hold("Stale, future-dated or unverified quota row")


class QuotaLedger:
    def __init__(self, path):
        self.path = Path(path)
        with self.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS live_a_claims (
                run_id TEXT PRIMARY KEY, org TEXT NOT NULL, project TEXT NOT NULL,
                claimed REAL NOT NULL, completed REAL, input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL, state TEXT NOT NULL,
                request_hash TEXT NOT NULL, authorization TEXT NOT NULL
            )""")

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            with db:
                yield db
        finally:
            db.close()

    def claim(self, record, budget, margin):
        if not 0 < margin <= 0.85:
            raise Hold("Safety margin must be positive and at most 0.85")
        windows = validated_windows(record)
        with self.transaction() as db:
            now = time.time()
            fresh(record, now)
            if db.execute("SELECT 1 FROM live_a_claims WHERE run_id=?", (record.run_id,)).fetchone():
                raise Hold("Stage A claim already consumed")
            for (scope, metric), window in windows.items():
                seconds = 60 if metric in MINUTE else 86400
                rows = db.execute("""SELECT input_tokens,output_tokens FROM live_a_claims
                    WHERE org=? AND (?='organization' OR project=?)
                    AND (completed IS NULL OR completed>?)""",
                    (record.organization, scope, record.project, now - seconds)).fetchall()
                if metric in REQUEST:
                    local, planned = len(rows), 1
                elif metric == "ITPM":
                    local, planned = sum(row[0] for row in rows), budget.input_tokens
                elif metric == "OTPM":
                    local, planned = sum(row[1] for row in rows), budget.max_output_tokens
                else:
                    local, planned = sum(i + o for i, o in rows), budget.total_tokens
                ceiling = min(window.limit, FREE.get(metric, window.limit))
                effective = ceiling if metric in REQUEST else int(ceiling * margin)
                # External totals may already include local claims. Charge both conservatively.
                if window.used + window.outstanding + local + planned > effective:
                    raise Hold(f"Insufficient {scope} {metric} headroom")
            db.execute("""INSERT INTO live_a_claims VALUES
                (?,?,?,?,NULL,?,?,'claimed',?,?)""",
                (record.run_id, record.organization, record.project, now,
                 budget.input_tokens, budget.max_output_tokens,
                 record.request_sha256, record.authorization))

    def mark(self, run_id, state, *, completed=False, usage=None):
        with self.transaction() as db:
            usage = usage or {}
            counts = [usage.get("prompt_tokens"), usage.get("completion_tokens")]
            counts = [n if type(n) is int and n >= 0 else 0 for n in counts]
            total = usage.get("total_tokens")
            if type(total) is int and total > sum(counts):
                counts[0] += total - sum(counts)
            db.execute("""UPDATE live_a_claims SET state=?, completed=?,
                input_tokens=max(input_tokens, ?), output_tokens=max(output_tokens, ?)
                WHERE run_id=?""",
                (state, time.time() if completed else None, *counts, run_id))
