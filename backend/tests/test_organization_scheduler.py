"""Offline admission/SQLite tests; synthetic identities are never operator evidence."""
from hashlib import sha256
import json
import multiprocessing
import time

import pytest
from pydantic import ValidationError

from app.extraction.organization_scheduler import (
    Identity, Organizations, load_organizations, QuotaWindow, VerifiedAdmission,
    OrganizationScheduler, ExtractionConfiguration, SHARED_CONFIGURATION, SchedulerHold, METRICS,
)


def registry(enabled=(1, 2, 3, 4, 5)):
    # Fixed validity allows restart and process-contention tests to use identical records.
    identities = [Identity(slot=s, organization=f"org-{s}", project=f"project-{s}", credential_id=f"inventory-{s}",
                           credential_sha256=sha256(f"test-secret-{s}".encode()).hexdigest(),
                           verified_by="fixture", ownership_evidence="synthetic-test-only",
                           verified_at=0.0, expires_at=4102444800.0) for s in range(1, 6)]
    return Organizations(identities, {s: f"test-secret-{s}" for s in enabled}, enabled)


def approvals(scheduler, request_id="r", request_hash="a" * 64, **changes):
    now = time.time()
    limits = dict(RPM=30, RPD=1000, TPM=8000, TPD=200000)
    result = {}
    for i in scheduler.organizations.identities:
        data = dict(organization=i.organization, project=i.project, credential_id=i.credential_id,
                    credential_sha256=i.credential_sha256, request_id=request_id, request_sha256=request_hash,
                    configuration_sha256=scheduler.config_hash, state="quota_verified", authorization="fixture-only",
                    verified_by="fixture", inventory_evidence="fixture-only", complete_limit_inventory=True,
                    complete_usage_inventory=True, project_limits_apply=False, traffic="controlled",
                    coordination_evidence="fixture-only", verified_at=now, control_until=now + 200,
                    windows=tuple(QuotaWindow(scope="organization", metric=m, limit=v, used=0, outstanding=0,
                                              data_as_of=now, evidence="fixture-only") for m, v in limits.items()))
        data.update(changes)
        result[i.organization] = VerifiedAdmission(**data)
    return result


def make(tmp_path, enabled=(1, 2, 3, 4, 5), **config):
    return OrganizationScheduler(tmp_path / "quota.sqlite", registry(enabled), ExtractionConfiguration(**config))


def success(s, request="r", inp=100, out=200):
    identity, admission = s.claim(request, "a" * 64, inp, out, approvals(s, request))
    s.record_attempt(request, usage={"prompt_tokens": inp, "completion_tokens": out, "total_tokens": inp + out})
    s.finish(request, "success")
    return identity.slot


def test_five_organization_order_and_restart(tmp_path):
    s = make(tmp_path)
    assert [success(s, f"r-{n}") for n in range(6)] == [1, 2, 3, 4, 5, 1]
    assert success(make(tmp_path), "restart") == 2
    assert len(s.status()["slots"]) == 5


def test_disabled_slots(tmp_path):
    s = make(tmp_path, (2, 4))
    assert [success(s, f"r{n}") for n in range(3)] == [2, 4, 2]


@pytest.mark.parametrize("state", ["quota_unknown", "quota_estimated", "quota_exhausted"])
def test_unverified_never_dispatchable(tmp_path, state):
    s = make(tmp_path)
    with pytest.raises(SchedulerHold):
        s.claim("r", "a" * 64, 100, 200, approvals(s, state=state))
    assert s.status()["active_request"] is None
    assert all(i["quota_state"] == "quota_unknown" for i in s.status()["slots"])


@pytest.mark.parametrize("field,value", [("traffic", "unknown"), ("request_sha256", "b" * 64),
    ("configuration_sha256", "b" * 64), ("credential_sha256", "b" * 64),
    ("project", "wrong"), ("organization", "wrong"), ("credential_id", "wrong"),
    ("verified_at", 0.0), ("verified_at", 4102444800.0), ("control_until", 0.0)])
def test_bad_admission_hold(tmp_path, field, value):
    s = make(tmp_path)
    with pytest.raises(SchedulerHold):
        s.claim("r", "a" * 64, 100, 200, approvals(s, **{field: value}))


@pytest.mark.parametrize("defect", ["missing_daily", "duplicate", "stale", "future", "project", "split"])
def test_complete_fresh_inventory(tmp_path, defect):
    s = make(tmp_path)
    admissions = approvals(s)
    for org, a in list(admissions.items()):
        data = a.model_dump()
        if defect == "missing_daily":
            data["windows"] = a.windows[:-1]
        elif defect == "duplicate":
            data["windows"] = a.windows + (a.windows[0],)
        elif defect in ("stale", "future"):
            row = a.windows[0].model_dump()
            row["data_as_of"] = time.time() + (-16 if defect == "stale" else 60)
            data["windows"] = (QuotaWindow(**row),) + a.windows[1:]
        elif defect == "project":
            data["project_limits_apply"] = True
        else:
            data["organization_split_metrics"] = ("ITPM",)
        admissions[org] = VerifiedAdmission(**data)
    with pytest.raises(SchedulerHold):
        s.claim("r", "a" * 64, 100, 200, admissions)


@pytest.mark.parametrize("metric", METRICS)
def test_85_percent_ceiling_and_outstanding(tmp_path, metric):
    s = make(tmp_path, (1,))
    a = approvals(s)["org-1"]
    rows = []
    for w in a.windows:
        row = w.model_dump()
        if w.metric == metric:
            row["outstanding"] = w.limit * 85 // 100
        rows.append(QuotaWindow(**row))
    a = VerifiedAdmission(**{**a.model_dump(), "windows": tuple(rows)})
    with pytest.raises(SchedulerHold):
        s.claim("r", "a" * 64, 100, 200, {"org-1": a})


def test_independent_quotas_and_actual_reconciliation(tmp_path):
    s = make(tmp_path)
    i, a = s.claim("r", "a" * 64, 1000, 4000, approvals(s))
    s.record_attempt("r", usage={"prompt_tokens": 100, "completion_tokens": 200,
                                 "total_tokens": 300, "completion_tokens_details": {"reasoning_tokens": 50}})
    s.finish("r", "success")
    row = s.status()["slots"][0]["attempts"][0]
    assert row["charged"] == 300 and row["reasoning"] == 50
    assert not s.status()["slots"][1]["attempts"]
    assert success(s, "next", 1000, 4000) == 2
    assert s.status()["slots"][0]["budgets"] == [
        {"scope": "organization", "metric": m, "limit": v, "internal": b}
        for m, v, b in [("RPM",30,25),("RPD",1000,850),("TPM",8000,6800),("TPD",200000,170000)]]


def test_uncertain_usage_never_zero_and_crash_persists(tmp_path):
    s = make(tmp_path)
    s.claim("crash", "a" * 64, 1000, 4000, approvals(s, "crash"))
    restarted = make(tmp_path)
    assert restarted.status()["slots"][0]["outstanding_reservations"] == 5000
    with pytest.raises(SchedulerHold):
        restarted.claim("new", "a" * 64, 1, 1, approvals(s, "new"))
    with pytest.raises(SchedulerHold, match="already claimed"):
        restarted.claim("crash", "a" * 64, 1, 1, approvals(s, "crash"))


def test_retry_bound_and_reserved_separately(tmp_path):
    s = make(tmp_path)
    i, a = s.claim("r", "a" * 64, 100, 200, approvals(s))
    s.record_attempt("r", uncertain=True, category="transient_network")
    s.retry("r", i, a, 100, 200)
    assert s.status()["slots"][0]["outstanding_reservations"] == 600
    s.record_attempt("r", usage={"prompt_tokens": 50, "completion_tokens": 50}, http_status=200)
    s.finish("r", "success")
    assert s.status()["slots"][0]["outstanding_reservations"] == 300
    with pytest.raises(SchedulerHold):
        s.claim("r", "a" * 64, 100, 200, approvals(s))


@pytest.mark.parametrize("field", ["provider", "model", "temperature", "strict_evidence", "fallback"])
def test_shared_configuration_rejects_drift(field):
    with pytest.raises(ValidationError):
        ExtractionConfiguration(**{field: "wrong"})
    with pytest.raises(ValidationError):
        SHARED_CONFIGURATION.model = "wrong"


def test_environment_no_legacy_fallback_or_secret_repr():
    reg = registry()
    with pytest.raises(SchedulerHold):
        load_organizations(reg.identities, {"GROQ_API_KEY": "legacy"})
    env = {"GROQ_ORG_1_ENABLED": "true", "GROQ_ORG_1_ID": "org-1"}
    with pytest.raises(SchedulerHold):
        load_organizations(reg.identities, env)
    env["GROQ_ORG_1_API_KEY"] = "test-secret-1"
    loaded = load_organizations(reg.identities, env)
    assert loaded.enabled == (1,) and "test-secret" not in repr(loaded)
    env["GROQ_ORG_1_ID"] = "wrong"
    with pytest.raises(SchedulerHold):
        load_organizations(reg.identities, env)


@pytest.mark.parametrize("field,value", [("organization", "org-1"), ("credential_sha256", sha256(b"test-secret-1").hexdigest()), ("slot", 1)])
def test_duplicate_identity_rejected(field, value):
    identities = list(registry().identities)
    identities[1] = Identity(**{**identities[1].model_dump(), field: value})
    with pytest.raises(SchedulerHold, match="Duplicate"):
        Organizations(identities, {}, (1,2))


def contender(path, queue):
    s = OrganizationScheduler(path, registry())
    try:
        s.claim("contended", "a" * 64, 100, 200, approvals(s, "contended"))
        queue.put("claimed")
    except SchedulerHold:
        queue.put("hold")


def test_cross_process_claim_once(tmp_path):
    make(tmp_path)
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    workers = [ctx.Process(target=contender, args=(str(tmp_path / "quota.sqlite"), queue)) for _ in range(3)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(20)
        assert w.exitcode == 0
    assert sorted(queue.get(timeout=5) for _ in workers) == ["claimed", "hold", "hold"]


def test_no_secrets_in_database_or_status(tmp_path, caplog):
    s = make(tmp_path)
    success(s)
    output = json.dumps(s.status()) + caplog.text + (tmp_path / "quota.sqlite").read_bytes().decode("latin1")
    assert all(f"test-secret-{i}" not in output for i in range(1,6))
    with pytest.raises(SchedulerHold, match="Credential material"):
        s.claim("test-secret-1", "a" * 64, 1, 1, approvals(s, "test-secret-1"))


def test_current_status_and_configuration_read_only(tmp_path):
    s = make(tmp_path)
    status = s.status(approvals(s), 100, 200)
    assert status["next_eligible_organization"] == "org-1"
    assert status["slots"][0]["quota_state"] == "quota_verified"
    assert s.status(approvals(s, state="quota_estimated"))["next_eligible_organization"] is None
    assert s.status(approvals(s, state="quota_exhausted"))["slots"][0]["quota_state"] == "quota_exhausted"
    with pytest.raises(AttributeError):
        s.configuration = ExtractionConfiguration(max_retries=0)


def test_repair_requires_review_preserves_usage_and_blocks_stale_worker(tmp_path):
    s = make(tmp_path)
    stale = make(tmp_path)
    s.claim("r", "a" * 64, 100, 200, approvals(s))
    s.record_attempt("r", http_status=401)
    s.finish("r", "failed", status=401)
    identities = list(s.organizations.identities)
    identities[0] = Identity(**{**identities[0].model_dump(), "credential_sha256": sha256(b"repaired-test-secret").hexdigest()})
    updated = Organizations(identities, {**{i:f"test-secret-{i}" for i in range(1,6)}, 1:"repaired-test-secret"}, (1,2,3,4,5))
    with pytest.raises(SchedulerHold):
        s.review_organization(updated, 1, " ")
    s.review_organization(updated, 1, "fixture-reviewed-repair")
    assert s.status()["slots"][0]["model_access"] == "not_blocked_not_proven"
    assert s.status()["slots"][0]["attempts"][0]["charged"] == 300
    with pytest.raises(SchedulerHold, match="stale"):
        stale.claim("new", "a" * 64, 100, 200, approvals(stale, "new"))
    assert success(s, "repaired") == 1


def test_attempt_cannot_be_reconciled_twice(tmp_path):
    s = make(tmp_path)
    s.claim("r", "a" * 64, 100, 200, approvals(s))
    with pytest.raises(SchedulerHold):
        s.finish("r", "success")
    s.record_attempt("r", usage={"prompt_tokens":100,"completion_tokens":200})
    with pytest.raises(SchedulerHold):
        s.record_attempt("r", usage={"prompt_tokens":0,"completion_tokens":0})


@pytest.mark.parametrize("usage", [{}, {"prompt_tokens":True,"completion_tokens":1},
    {"prompt_tokens":100,"completion_tokens":50,"total_tokens":20},
    {"prompt_tokens":100,"completion_tokens":50,"completion_tokens_details":{"reasoning_tokens":100}}])
def test_missing_or_inconsistent_usage_retains_reservation(tmp_path, usage):
    s = make(tmp_path)
    s.claim("r", "a" * 64, 100, 200, approvals(s))
    s.record_attempt("r", usage=usage)
    assert s.status()["slots"][0]["attempts"][0]["charged"] == 300


def test_whitespace_evidence_and_nonfinite_time_rejected():
    for change in ({"evidence":" "}, {"data_as_of":float("nan")}, {"used":-1}):
        with pytest.raises(ValidationError):
            QuotaWindow(**{**dict(scope="organization", metric="TPM", limit=8000, used=0, outstanding=0,
                                  data_as_of=time.time(), evidence="fixture"), **change})


def test_dispatch_claim_prevents_second_send(tmp_path):
    s = make(tmp_path)
    identity, admission = s.claim("r", "a" * 64, 100, 200, approvals(s))
    s.check_dispatch("r", identity, admission)
    with pytest.raises(SchedulerHold, match="already dispatched"):
        s.check_dispatch("r", identity, admission)
    assert s.status()["slots"][0]["attempts"][0]["dispatched"] is not None


def test_reservation_blocks_other_process_requests_without_overspend(tmp_path):
    s = make(tmp_path, (1,))
    other = make(tmp_path, (1,))
    s.claim("first", "a" * 64, 1000, 4000, approvals(s, "first"))
    with pytest.raises(SchedulerHold, match="active"):
        other.claim("second", "a" * 64, 1000, 4000, approvals(other, "second"))
    s.record_attempt("first", uncertain=True)
    s.finish("first", "uncertain")
    with pytest.raises(SchedulerHold, match="No eligible"):
        other.claim("second", "a" * 64, 1000, 4000, approvals(other, "second"))
