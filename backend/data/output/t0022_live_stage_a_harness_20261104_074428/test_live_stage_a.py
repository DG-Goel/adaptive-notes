import json
from pathlib import Path
import subprocess
import sys
import time

import httpx
import pytest

from admission import Admission, Hold
from live_stage_a import MODEL, URL, execute, request_plan
from control import digest, encode

KEY = "fixture-key"


@pytest.fixture(autouse=True)
def block_live_transport(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Real HTTP transport requested in offline test")
    monkeypatch.setattr(httpx, "HTTPTransport", blocked)


def admission(**changes):
    payload, _, _ = request_plan()
    now = time.time()
    values = dict(decision="PASS", stage="A", provider="Groq", model=MODEL, source_id="T0022",
                  run_id="fixture-run", organization="fixture-org", project="fixture-project",
                  operator="fixture-operator", authorization="offline test",
                  credential_id="fixture-key-v1", credential_sha256=digest(KEY.encode()),
                  request_sha256=digest(encode(payload)), data_as_of=now, verified_at=now,
                  control_until=now + 300, traffic="controlled", coordination_evidence="fixture lease",
                  authoritative_limits=True, complete_limit_inventory=True,
                  complete_usage_inventory=True, windows=[
                      dict(scope="organization", metric=metric, limit=limit, used=0, outstanding=0,
                           evidence="fixture authoritative counter")
                      for metric, limit in [("RPM", 30), ("RPD", 1000), ("TPM", 8000), ("TPD", 200000)]])
    values.update(changes)
    return values


def envelope():
    facts = json.loads((Path(__file__).resolve().parent.parent /
                        "t0022_offline_prototype_20261103_225328/reference_facts.json").read_text(encoding="utf-8"))
    return {"model": MODEL, "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(facts)}}]}


def dispatch(tmp_path, values=None, status=200, body=None):
    calls = []
    def mock(request):
        assert str(request.url) == URL and request.method == "POST"
        assert json.loads(request.content) == request_plan()[0]
        assert request.headers["authorization"] == "Bearer " + KEY
        calls.append(request)
        return httpx.Response(status, content=body if body is not None else encode(envelope()))
    record = Admission.model_validate(values if values is not None else admission())
    return calls, lambda: execute(record, KEY, tmp_path, transport=httpx.MockTransport(mock))


@pytest.mark.parametrize("field,value", [
    ("provider", "other"), ("model", "other"), ("source_id", "JAVA_CHUNK_000"),
    ("traffic", "unknown"), ("traffic", "uncontrolled"), ("complete_usage_inventory", False),
])
def test_bad_admission_schema(field, value):
    with pytest.raises(ValueError):
        Admission.model_validate(admission(**{field: value}))


@pytest.mark.parametrize("metric", ["RPM", "RPD", "TPM", "TPD"])
def test_exhausted_quota(tmp_path, metric):
    values = admission()
    for row in values["windows"]:
        if row["metric"] == metric:
            row["used"] = row["limit"]
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match=metric):
        run()
    assert not calls


def test_missing_daily_usage(tmp_path):
    values = admission()
    values["windows"] = values["windows"][:-1]
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match="daily"):
        run()
    assert not calls
    values = admission()
    values["windows"][-1].pop("used")
    with pytest.raises(ValueError):
        Admission.model_validate(values)


@pytest.mark.parametrize("change,match", [
    ({"scope": "project", "metric": "TPM", "limit": 4000}, "project TPM"),
    ({"scope": "organization", "metric": "OTPM", "limit": 4000}, "organization OTPM"),
])
def test_additional_caps(tmp_path, change, match):
    values = admission()
    values["windows"].append(dict(change, used=0, outstanding=0, evidence="fixture"))
    calls, run = dispatch(tmp_path, values)
    with pytest.raises(Hold, match=match):
        run()
    assert not calls


def test_plan_rejects_oversized_cap(tmp_path, monkeypatch):
    import live_stage_a
    original = live_stage_a.PREFLIGHT.read_text(encoding="utf-8")
    changed = tmp_path / "PREFLIGHT.md"
    changed.write_text(original.replace('"max_tokens_planned": 4000', '"max_tokens_planned": 4001'), encoding="utf-8")
    monkeypatch.setattr(live_stage_a, "PREFLIGHT", changed)
    with pytest.raises(Hold, match="Output cap"):
        request_plan()


@pytest.mark.parametrize("status", [401, 403, 429, 307])
def test_http_failure_consumes_claim(tmp_path, status):
    calls, run = dispatch(tmp_path, status=status)
    with pytest.raises(Hold, match=f"HTTP {status}"):
        run()
    with pytest.raises(Hold, match="exists|consumed"):
        run()
    assert len(calls) == 1
    assert not (tmp_path / "fixture-run/A_facts.json").exists()


@pytest.mark.parametrize("kind", ["length", "bad_envelope", "bad_content", "stitched_quote", "wrong_source"])
def test_invalid_response(tmp_path, kind):
    data = envelope()
    choice = data["choices"][0]
    facts = json.loads(choice["message"]["content"])
    if kind == "length":
        choice["finish_reason"] = "length"
    elif kind == "stitched_quote":
        facts["facts"][0]["quote"] = "cannot assign ... change this to double"
    elif kind == "wrong_source":
        facts["facts"][0]["source_id"] = "JAVA_CHUNK_000"
    choice["message"]["content"] = "{" if kind == "bad_content" else json.dumps(facts)
    calls, run = dispatch(tmp_path, body=b"{" if kind == "bad_envelope" else encode(data))
    with pytest.raises(Hold, match="incomplete or invalid"):
        run()
    assert len(calls) == 1 and not (tmp_path / "fixture-run/A_facts.json").exists()


def test_success_no_stage_b_and_checkpoint_exclusive(tmp_path):
    calls, run = dispatch(tmp_path)
    result = run()
    checkpoint = Path(result["checkpoint"])
    original = checkpoint.read_bytes()
    assert digest(original) == result["sha256"] and result["publishable_items"] == 0
    from control import Ledger
    ledger = Ledger(checkpoint.parent, "fixture-run")
    assert dict(ledger.events("A"))["awaiting_manual_review"]["artifact_hash"] == result["sha256"]
    assert ledger.events("B") == []
    with pytest.raises(FileExistsError):
        ledger.artifact("A_facts.json", b"replacement")
    with pytest.raises(Hold, match="exists|consumed"):
        run()
    assert len(calls) == 1 and checkpoint.read_bytes() == original


def test_shared_ledger_charges_previous_run(tmp_path):
    _, first = dispatch(tmp_path)
    first()
    calls, second = dispatch(tmp_path, admission(run_id="second"))
    with pytest.raises(Hold, match="TPM"):
        second()
    assert not calls


def test_timeout_claim_not_released(tmp_path):
    def timeout(request):
        raise httpx.ReadTimeout("fixture", request=request)
    record = Admission.model_validate(admission())
    with pytest.raises(Hold, match="uncertain"):
        execute(record, KEY, tmp_path, transport=httpx.MockTransport(timeout))
    # A distinct run is also denied by the unresolved allocation in the common ledger.
    calls, second = dispatch(tmp_path, admission(run_id="next"))
    with pytest.raises(Hold, match="TPM"):
        second()
    assert not calls


@pytest.mark.parametrize("same_run", [True, False])
def test_concurrent_process_claims(tmp_path, same_run):
    worker = """
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from admission import Admission, Hold, QuotaLedger
from live_stage_a import request_plan
root, record_path = Path(sys.argv[2]), Path(sys.argv[3])
record = Admission.model_validate_json(record_path.read_bytes())
(root / (record_path.stem + '.ready')).touch()
deadline = time.monotonic() + 8
while not (root / 'go').exists():
    if time.monotonic() > deadline:
        sys.exit(9)
    time.sleep(.01)
try:
    QuotaLedger(root / 'quota.sqlite').claim(record, request_plan()[1], .85)
except Hold:
    sys.exit(2)
"""
    paths = [tmp_path / f"{i}.json" for i in range(2)]
    for i, path in enumerate(paths):
        path.write_bytes(encode(admission(run_id="same" if same_run else f"run-{i}")))
    processes = [subprocess.Popen([sys.executable, "-B", "-c", worker,
                                   str(Path(__file__).parent), str(tmp_path), str(p)]) for p in paths]
    try:
        deadline = time.monotonic() + 8
        while len(list(tmp_path.glob("*.ready"))) < 2 and time.monotonic() < deadline:
            time.sleep(.01)
        assert len(list(tmp_path.glob("*.ready"))) == 2
        (tmp_path / "go").touch()
        assert sorted(p.wait(timeout=15) for p in processes) == [0, 2]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
