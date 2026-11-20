"""Real SDK serialization with mocked HTTP only; prohibit real HTTP transports."""
import json
import time

import httpx
import pytest

from app.extraction.organization_extraction import extract_chunk, prepare_request
from app.extraction.organization_scheduler import SchedulerHold, digest
from app.extraction.llm_provider import GroqProviderError
from app.models.source import SourceUnit
from app.models.knowledge import ExtractionChunk
from tests.test_organization_scheduler import make, approvals

TEXT = "A value is an expression."


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Real HTTP transport forbidden")
    monkeypatch.setattr(httpx, "HTTPTransport", blocked)
    monkeypatch.setattr("app.extraction.organization_extraction.time.sleep", lambda _: None)


def setup(s, request="r"):
    chunk = ExtractionChunk(chunk_id="JAVA_CHUNK_000", source_units=["T0022"], text_content="[T0022] " + TEXT)
    source = SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph", text=TEXT, position=0)
    payload, budget = prepare_request(chunk, s.configuration)
    # Larger verified fixture limits, not assumptions about real Free Tier capacity.
    admitted = approvals(s, request, digest(payload))
    for org, a in list(admitted.items()):
        from app.extraction.organization_scheduler import QuotaWindow, VerifiedAdmission
        rows = tuple(QuotaWindow(**{**w.model_dump(), "limit": 1000000}) for w in a.windows)
        admitted[org] = VerifiedAdmission(**{**a.model_dump(), "windows": rows})
    return chunk, [source], payload, admitted


def envelope(content=None, finish="stop", model="openai/gpt-oss-120b"):
    if content is None:
        content = json.dumps({"concepts": [{"concept_name": "expression", "content": TEXT, "source_unit_ids": ["T0022"],
            "source_evidence": [{"source_id": "T0022", "quote": TEXT, "fields": ["/concept_name", "/content"]}]}]})
    return {"id": "fixture", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300,
                      "completion_tokens_details": {"reasoning_tokens": 40}}}


def test_identical_requests_and_strict_validation_across_five(tmp_path):
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    bodies, auth = [], []
    def respond(req):
        bodies.append(json.loads(req.content))
        auth.append(req.headers["authorization"])
        return httpx.Response(200, json=envelope())
    for n in range(6):
        chunk, sources, payload, admitted = setup(s, f"r{n}")
        items = extract_chunk(s, f"r{n}", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
        assert len(items) == 1
        assert items[0].extraction_metadata["source_grounding"]["mechanically_valid"]
        assert items[0].extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False
    assert all(b == payload for b in bodies)
    assert auth == [f"Bearer test-secret-{i}" for i in [1,2,3,4,5,1]]


@pytest.mark.parametrize("status", [400, 401, 403, 429])
def test_permanent_and_rate_limit_no_rotation_or_outer_retry(tmp_path, status):
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    chunk, sources, payload, admitted = setup(s)
    calls = []
    def respond(req):
        calls.append(req.headers["authorization"])
        return httpx.Response(status, json={"error": {"code": "invalid_api_key" if status == 401 else "fixture_error",
                                                     "message": "test-secret-1"}}, headers={"Retry-After": "120"})
    with pytest.raises(GroqProviderError) as error:
        extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    assert error.value.retryable is False
    assert "test-secret" not in str(error.value)
    assert calls == ["Bearer test-secret-1"]
    with pytest.raises(SchedulerHold, match="already claimed"):
        extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    assert len(calls) == 1
    state = s.status()
    assert state["cursor"] == 1
    assert state["slots"][0]["last_outcome"] == "failed"
    if status in (401,403):
        assert state["slots"][0]["model_access"] == str(status)
    if status == 429:
        assert state["slots"][0]["cooldown_until"] >= time.time() + 119
        assert error.value.retry_after == 120
        assert state["slots"][0]["eligibility"] == "rate_limited"
        assert state["slots"][0]["quota_state"] == "quota_exhausted"


@pytest.mark.parametrize("kind", ["server", "network"])
def test_transient_bounded_same_org_and_accounted(tmp_path, kind):
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    chunk, sources, payload, admitted = setup(s)
    calls = []
    def respond(req):
        calls.append(req.headers["authorization"])
        if kind == "network":
            raise httpx.ConnectError("fixture", request=req)
        return httpx.Response(503, json={"error": {"message": "fixture"}})
    with pytest.raises(GroqProviderError) as error:
        extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    assert not error.value.retryable
    assert calls == ["Bearer test-secret-1"] * 3
    state = s.status()["slots"][0]
    assert state["last_outcome"] == "uncertain"
    assert len(state["attempts"]) == 3
    assert state["outstanding_reservations"] > 0


def test_transient_then_success(tmp_path):
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    chunk, sources, payload, admitted = setup(s)
    calls = []
    def respond(req):
        calls.append(req.headers["authorization"])
        return httpx.Response(503, json={"error": {"message": "fixture"}}) if len(calls) == 1 else httpx.Response(200, json=envelope())
    items = extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    assert len(items) == 1 and calls == ["Bearer test-secret-1"] * 2
    assert s.status()["cursor"] == 2
    assert s.status()["slots"][0]["outstanding_reservations"] > 0


@pytest.mark.parametrize("defect", ["missing_content", "bad_quote", "scheduling_source", "empty", "json", "length", "model", "secret", "duplicate"])
def test_failure_atomic_and_no_success_rotation(tmp_path, defect):
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    chunk, sources, payload, admitted = setup(s)
    reply = envelope()
    content = json.loads(reply["choices"][0]["message"]["content"])
    raw = content["concepts"][0]
    if defect == "missing_content":
        del raw["content"]
    elif defect == "bad_quote":
        raw["source_evidence"][0]["quote"] = "fabricated"
    elif defect == "scheduling_source":
        raw["source_unit_ids"] = ["JAVA_CHUNK_000"]
    elif defect == "empty":
        content = {}
    reply["choices"][0]["message"]["content"] = json.dumps(content)
    if defect in ("json", "secret", "duplicate"):
        reply["choices"][0]["message"]["content"] = {"json": "{", "secret": '"test-secret-1"', "duplicate": '{"facts":[],"facts":[]}'}[defect]
    if defect == "length":
        reply["choices"][0]["finish_reason"] = "length"
    if defect == "model":
        reply["model"] = "other"
    calls = []
    def respond(req):
        calls.append(1)
        return httpx.Response(200, json=reply)
    with pytest.raises(SchedulerHold):
        extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    assert calls == [1]
    assert s.status()["cursor"] == 1
    assert s.status()["slots"][0]["last_outcome"] == "validation_failed"


def test_sdk_error_diagnostics_are_sanitized_in_audit(tmp_path, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    s = make(tmp_path, scheduler_ceilings=(700000, 700000, 700000, 700000))
    chunk, sources, payload, admitted = setup(s)
    def respond(req):
        return httpx.Response(400, json={"error":{"code":"json_validate_failed", "message":"credential test-secret-1"}})
    with pytest.raises(GroqProviderError):
        extract_chunk(s, "r", chunk, sources, "JAVA", admitted, transport=httpx.MockTransport(respond))
    with s.transaction() as db:
        rows = [dict(r) for r in db.execute("SELECT * FROM audit_events")]
    assert any("json_validate_failed" in row["details"] for row in rows)
    assert "test-secret-1" not in json.dumps(rows) + caplog.text
