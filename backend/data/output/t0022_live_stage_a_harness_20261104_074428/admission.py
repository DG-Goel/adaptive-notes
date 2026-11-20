"""Operator-attested admission and durable claims for one-shot Stage A."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Hold(ValueError):
    pass


FREE = {"RPM": 30, "RPD": 1000, "TPM": 8000, "TPD": 200000}
MINUTE = {"RPM", "TPM", "ITPM", "OTPM"}
REQUEST = {"RPM", "RPD"}


class Window(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: Literal["organization", "project"]
    metric: Literal["RPM", "RPD", "TPM", "TPD", "ITPM", "OTPM"]
    limit: int = Field(gt=0)
    used: int = Field(ge=0)
    outstanding: int = Field(ge=0)
    evidence: str = Field(min_length=1)


class Admission(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    decision: Literal["PASS"]
    stage: Literal["A"]
    provider: Literal["Groq"]
    model: Literal["openai/gpt-oss-120b"]
    source_id: Literal["T0022"]
    run_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
    organization: str = Field(min_length=1)
    project: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    authorization: str = Field(min_length=1)
    credential_id: str = Field(min_length=1)
    credential_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_as_of: float = Field(allow_inf_nan=False)
    verified_at: float = Field(allow_inf_nan=False)
    control_until: float = Field(allow_inf_nan=False)
    traffic: Literal["controlled", "accounted"]
    coordination_evidence: str = Field(min_length=1)
    authoritative_limits: Literal[True]
    complete_limit_inventory: Literal[True]
    complete_usage_inventory: Literal[True]
    windows: list[Window]


def fresh(record, now):
    if not (0 <= now - record.data_as_of <= 15
            and record.data_as_of <= record.verified_at <= now
            and record.control_until >= now + 90):
        raise Hold("Stale evidence or traffic control expires too soon")


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
        windows = {(w.scope, w.metric): w for w in record.windows}
        if len(windows) != len(record.windows) or not all(
            ("organization", metric) in windows for metric in FREE
        ):
            raise Hold("Missing or duplicate quota windows, including daily usage")
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
