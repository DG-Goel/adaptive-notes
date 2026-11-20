from dataclasses import replace
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest

from control import (Ledger, Limit, MockReply, OfflineScenario, QuotaEvidence,
                     Refused, digest, encode)
from stage_a import execute_a
from stage_b import approve_b, execute_b
from fixtures import A, B, review_field


@pytest.fixture(autouse=True)
def network_disabled(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network disabled in offline tests")
    for name in ("socket", "getaddrinfo", "create_connection"):
        monkeypatch.setattr(socket, name, blocked)
    with pytest.raises(AssertionError, match="Network disabled"):
        socket.create_connection(("example.invalid", 443))


def evidence():
    return QuotaEvidence("Groq", "fixture-org", "openai/gpt-oss-120b", time.time(),
                         (Limit("minute", 30, 0, 8000, 0),
                          Limit("day", 1000, 0, 100000, 0)), True, True, True)


def scenario(payload, **options):
    return OfflineScenario(MockReply(encode(payload).decode(), request_id="mock-1"),
                           evidence(), **options)


def start_a(ledger):
    return execute_a(ledger, scenario(A), "fixture-org", "offline test authorization")


def approve(ledger):
    raw = (ledger.directory / "A_facts.json").read_bytes()
    coverage = dict(final_pi_error="f001", pi_to_PI="f002", division_type_mismatch="f003",
                    declaration_repair="f004", float_double_alternatives="f005", increment_1_to_2="f006")
    approve_b(ledger, "fixture-reviewer", digest(raw),
              [row["fact_id"] for row in A["facts"]], coverage)


def test_separate_entry_points_and_isolation(tmp_path):
    ledger = Ledger(tmp_path, "run")
    assert start_a(ledger)["publishable_items"] == ()
    assert ledger.events("B") == []
    b = scenario(B)
    with pytest.raises(Refused, match="approval"):
        execute_b(ledger, b, "fixture-org", review_field)
    assert b.calls == 0
    approve(ledger)
    result = execute_b(ledger, b, "fixture-org", review_field)
    assert b.calls == 1 and len(result["items"]) == 9
    assert result["publishable_items"] == ()
    assert ledger.disposition("B") == "confirmed_response"
    assert dict(ledger.events("B"))["confirmed_response"]["request_id"] == "mock-1"


def test_wrong_approval_hash(tmp_path):
    ledger = Ledger(tmp_path, "run")
    start_a(ledger)
    with pytest.raises(Refused, match="hash"):
        approve_b(ledger, "reviewer", "wrong", [], {})


def test_modified_artifact_invalidates_approval(tmp_path):
    ledger = Ledger(tmp_path, "run")
    start_a(ledger)
    approve(ledger)
    path = tmp_path / "A_facts.json"
    path.write_bytes(path.read_bytes() + b" ")
    b = scenario(B)
    with pytest.raises(Refused, match="modified"):
        execute_b(ledger, b, "fixture-org", review_field)
    assert b.calls == 0


@pytest.mark.parametrize("change", [
    lambda _: None,
    lambda e: replace(e, verified_at=time.time() - 60),
    lambda e: replace(e, exclusive_traffic_control=False),
    lambda e: replace(e, coordinated_usage=False),
    lambda e: replace(e, authoritative_limits=False),
    lambda e: replace(e, organization="wrong"),
    lambda e: replace(e, limits=(Limit("minute", 1, 1, 8000, 0),)),
    lambda e: replace(e, limits=(Limit("minute", 30, 0, 8000, 7999),)),
])
def test_quota_fail_closed(tmp_path, change):
    ledger = Ledger(tmp_path, "run")
    mock = scenario(A)
    mock.evidence = change(mock.evidence)
    with pytest.raises(Refused):
        execute_a(ledger, mock, "fixture-org", "offline")
    assert mock.calls == 0 and ledger.disposition("A") == "unclaimed"


def test_b_rechecks_quota_and_preserves_a(tmp_path):
    ledger = Ledger(tmp_path, "run")
    start_a(ledger)
    approve(ledger)
    path = tmp_path / "A_facts.json"
    original = path.read_bytes()
    b = scenario(B)
    b.evidence = None
    with pytest.raises(Refused, match="Quota"):
        execute_b(ledger, b, "fixture-org", review_field)
    assert b.calls == 0 and path.read_bytes() == original


def test_timeout_consumes_authorization(tmp_path):
    ledger = Ledger(tmp_path, "run")
    mock = scenario(A, timeout=True)
    with pytest.raises(Refused, match="uncertain"):
        execute_a(ledger, mock, "fixture-org", "offline")
    assert ledger.disposition("A") == "uncertain"
    assert [kind for kind, _ in ledger.events("A")] == [
        "authorized_and_claimed", "dispatch_attempt", "uncertain_outcome"]
    with pytest.raises(Refused, match="consumed"):
        execute_a(Ledger(tmp_path, "run"), mock, "fixture-org", "offline")
    assert mock.calls == 1


@pytest.mark.parametrize("finish,status", [("length", 200), ("stop", 429)])
def test_incomplete_a_and_429_stop(tmp_path, finish, status):
    ledger = Ledger(tmp_path, "run")
    mock = OfflineScenario(MockReply(encode(A).decode(), finish, status_code=status), evidence())
    with pytest.raises(ValueError):
        execute_a(ledger, mock, "fixture-org", "offline")
    assert mock.calls == 1
    assert not (tmp_path / "A_facts.json").exists()
    with pytest.raises(Refused, match="consumed"):
        start_a(ledger)


def test_b_failure_has_no_result(tmp_path):
    ledger = Ledger(tmp_path, "run")
    start_a(ledger)
    approve(ledger)
    with pytest.raises(ValueError):
        execute_b(ledger, scenario({"facts": []}), "fixture-org", review_field)
    assert (tmp_path / "A_facts.json").exists()
    assert not (tmp_path / "B_review_result.json").exists()


WORKER = """
import os, socket, sys, time
def blocked(*args, **kwargs):
    raise AssertionError('Network disabled in subprocess')
socket.socket = socket.create_connection = socket.getaddrinfo = blocked
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from control import Ledger, Refused
root = Path(sys.argv[2])
ledger = Ledger(root, 'run')
mode = sys.argv[3]
if mode == 'race':
    (root / ('ready-' + str(os.getpid()))).touch()
    deadline = time.monotonic() + 10
    while not (root / 'go').exists():
        if time.monotonic() > deadline:
            sys.exit(9)
        time.sleep(.01)
try:
    ledger.claim('A', {'authorization': 'offline subprocess'})
except Refused:
    sys.exit(2)
if mode == 'dispatch-crash':
    ledger.event('A', 'dispatch_attempt', {'offline': True})
os._exit(7 if mode.endswith('crash') else 0)
"""


def worker(path, mode):
    return subprocess.Popen([sys.executable, "-B", "-c", WORKER,
                             str(Path(__file__).parent), str(path), mode])


def test_concurrent_process_claims(tmp_path):
    ledger = Ledger(tmp_path, "run")
    processes = [worker(tmp_path, "race") for _ in range(2)]
    try:
        deadline = time.monotonic() + 10
        while len(list(tmp_path.glob("ready-*"))) != 2 and time.monotonic() < deadline:
            time.sleep(.01)
        assert len(list(tmp_path.glob("ready-*"))) == 2
        (tmp_path / "go").touch()
        assert sorted(p.wait(timeout=15) for p in processes) == [0, 2]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    assert len(ledger.events("A")) == 1


@pytest.mark.parametrize("mode,status", [
    ("claim-crash", "claimed_without_dispatch"),
    ("dispatch-crash", "uncertain"),
])
def test_crash_consumes_claim(tmp_path, mode, status):
    assert worker(tmp_path, mode).wait(timeout=15) == 7
    ledger = Ledger(tmp_path, "run")
    assert ledger.disposition("A") == status
    mock = scenario(A)
    with pytest.raises(Refused, match="consumed"):
        execute_a(ledger, mock, "fixture-org", "offline")
    assert mock.calls == 0
