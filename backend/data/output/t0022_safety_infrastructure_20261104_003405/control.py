"""Offline-only experiment control. No transport or credential loader."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import time

from app.extraction.token_budget import TokenBudgetManager

PROVIDER = "Groq"
MODEL = "openai/gpt-oss-120b"


class Refused(ValueError):
    pass


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(data):
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class Limit:
    window: str
    requests_limit: int
    requests_used: int
    tokens_limit: int
    tokens_used: int


@dataclass(frozen=True)
class QuotaEvidence:
    provider: str
    organization: str
    model: str
    verified_at: float
    limits: tuple[Limit, ...]
    authoritative_limits: bool
    coordinated_usage: bool
    exclusive_traffic_control: bool


def admit(evidence, organization, allocation, now):
    if not organization.strip() or evidence is None or (evidence.provider, evidence.organization, evidence.model) != (
        PROVIDER, organization, MODEL
    ):
        raise Refused("Quota identity or evidence missing")
    if not 0 <= now - evidence.verified_at <= 15:
        raise Refused("Quota evidence stale")
    if not (evidence.authoritative_limits and evidence.coordinated_usage
            and evidence.exclusive_traffic_control):
        raise Refused("Quota evidence or coordinated traffic control missing")
    if not evidence.limits or not any(limit.window == "minute" for limit in evidence.limits):
        raise Refused("Applicable quota windows missing")
    for limit in evidence.limits:
        if (any(type(value) is not int for value in (limit.requests_limit, limit.requests_used,
                                                     limit.tokens_limit, limit.tokens_used))
                or min(limit.requests_used, limit.tokens_used) < 0
                or limit.requests_used + 1 > limit.requests_limit
                or limit.tokens_used + allocation > limit.tokens_limit):
            raise Refused(f"Insufficient quota headroom in {limit.window}")


@dataclass(frozen=True)
class MockReply:
    body: str
    finish_reason: str = "stop"
    usage: dict | None = None
    request_id: str | None = None
    status_code: int = 200


class OfflineScenario:
    """Scripted responses and simulated quota only. No callable transport."""
    def __init__(self, reply, evidence, *, timeout=False):
        self.reply = reply
        self.evidence = evidence
        self.timeout = timeout
        self.calls = 0

    @contextmanager
    def quota_lease(self):
        # Simulates an externally held coordination lease for tests only.
        yield self.evidence

    def dispatch(self):
        self.calls += 1
        if self.timeout:
            raise TimeoutError("Simulated timeout")
        return self.reply


class Ledger:
    def __init__(self, directory, run_id):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.db = self.directory / "control.sqlite"
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS run (singleton INTEGER PRIMARY KEY CHECK(singleton=1), id TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS claims (
                run TEXT, stage TEXT CHECK(stage IN ('A','B')), claimed_at REAL,
                PRIMARY KEY(run, stage)
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, run TEXT, stage TEXT, kind TEXT, at REAL, payload TEXT
            );
            CREATE TABLE IF NOT EXISTS approvals (
                run TEXT, stage TEXT CHECK(stage='B'), reviewer TEXT, artifact_hash TEXT,
                approved_at REAL, review TEXT, PRIMARY KEY(run,stage)
            );
            """)
            db.execute("INSERT OR IGNORE INTO run VALUES (1, ?)", (run_id,))
            if db.execute("SELECT id FROM run").fetchone()[0] != run_id:
                raise Refused("Directory belongs to another run")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=15)
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def claim(self, stage, authorization):
        try:
            with self.connect() as db:
                db.execute("INSERT INTO claims VALUES (?,?,?)", (self.run_id, stage, time.time()))
                self._event(db, stage, "authorized_and_claimed", authorization)
        except sqlite3.IntegrityError as exc:
            raise Refused("Stage authorization already consumed or invalid") from exc

    def _event(self, db, stage, kind, payload):
        db.execute("INSERT INTO events(run,stage,kind,at,payload) VALUES (?,?,?,?,?)",
                   (self.run_id, stage, kind, time.time(), encode(payload).decode()))

    def event(self, stage, kind, payload):
        with self.connect() as db:
            self._event(db, stage, kind, payload)

    def events(self, stage):
        with self.connect() as db:
            return [(kind, json.loads(payload)) for kind, payload in db.execute(
                "SELECT kind,payload FROM events WHERE run=? AND stage=? ORDER BY id",
                (self.run_id, stage))]

    def disposition(self, stage):
        events = dict(self.events(stage))
        if "confirmed_response" in events:
            return "confirmed_response"
        if "dispatch_attempt" in events:
            return "uncertain"
        if "authorized_and_claimed" in events:
            return "claimed_without_dispatch"
        return "unclaimed"

    def artifact(self, name, data):
        with (self.directory / name).open("xb") as stream:
            stream.write(data)
            stream.flush()
            import os
            os.fsync(stream.fileno())


def dispatch_once(ledger, stage, scenario, organization, messages, authorization):
    if type(scenario) is not OfflineScenario:
        raise Refused("Only scripted offline scenarios are accepted")
    budget = TokenBudgetManager().calculate_budget(messages["user"], system_text=messages["system"])
    if not budget.is_safe:
        raise Refused("Unsafe request budget")
    with scenario.quota_lease() as evidence:
        admit(evidence, organization, budget.total_tokens, time.time())
        ledger.claim(stage, authorization)
        ledger.artifact(f"{stage}_request.json", encode({
            "offline": True, "provider": PROVIDER, "model": MODEL, "organization": organization,
            "messages": messages, "messages_sha256": digest(encode(messages)),
            "budget": asdict(budget), "simulated_quota_evidence": asdict(evidence),
            "sdk_retries": 0, "application_retries": 0,
            "key_pool": False, "fallback": False, "response_format": {"type": "json_object"},
        }))
        ledger.event(stage, "dispatch_attempt", {"offline": True})
        try:
            reply = scenario.dispatch()
        except Exception as exc:
            ledger.event(stage, "uncertain_outcome", {"error_type": type(exc).__name__})
            raise Refused("Dispatch outcome uncertain. Authorization consumed.") from exc
        ledger.event(stage, "confirmed_response", asdict(reply))
        ledger.artifact(f"{stage}_response.json", encode(asdict(reply)))
    return reply
