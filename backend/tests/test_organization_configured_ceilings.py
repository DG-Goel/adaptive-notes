import pytest
import httpx

from tests.test_organization_scheduler import make, approvals
from tests.test_organization_extraction import setup
from app.extraction.organization_scheduler import SchedulerHold, METRICS
from app.extraction.organization_extraction import extract_chunk


@pytest.mark.parametrize("metric,ceiling", tuple(zip(METRICS, (25, 850, 6800, 170000))))
def test_configured_ceiling_with_larger_verified_provider_limit(tmp_path, metric, ceiling):
    scheduler = make(tmp_path)
    records = approvals(scheduler, "request")
    for org, admission in records.items():
        records[org] = admission.model_copy(update={"windows": tuple(
            row.model_copy(update={"limit": 1000000, "outstanding": ceiling if row.metric == metric else 0})
            for row in admission.windows)})
    with pytest.raises(SchedulerHold):
        scheduler.claim("request", "a" * 64, 100, 200, records)
    assert all(slot["configured_ceilings"] == dict(zip(METRICS, (25, 850, 6800, 170000)))
               for slot in scheduler.status()["slots"])


def test_production_prompt_fits_requested_tpm_ceiling(tmp_path):
    from tests.test_organization_extraction import envelope
    scheduler = make(tmp_path)
    chunk, sources, payload, records = setup(scheduler)
    items = extract_chunk(scheduler, "r", chunk, sources, "JAVA", records,
                          transport=httpx.MockTransport(lambda request: httpx.Response(200, json=envelope())))
    assert len(items) == 1


@pytest.mark.parametrize("total,allowed", [(6130, True), (6800, True), (6801, False)])
def test_exact_token_boundary(tmp_path, total, allowed):
    scheduler = make(tmp_path)
    if allowed:
        scheduler.claim("r", "a" * 64, total - 3000, 3000, approvals(scheduler))
    else:
        with pytest.raises(SchedulerHold):
            scheduler.claim("r", "a" * 64, total - 3000, 3000, approvals(scheduler))


def test_completed_usage_holds_until_minute_reset(tmp_path, monkeypatch):
    import time
    clock = [time.time()]
    monkeypatch.setattr("app.extraction.organization_scheduler.time.time", lambda: clock[0])
    scheduler = make(tmp_path, (1,))
    scheduler.claim("first", "a" * 64, 2800, 4000, approvals(scheduler, "first"))
    scheduler.record_attempt("first", usage={"prompt_tokens": 2800, "completion_tokens": 4000, "total_tokens": 6800})
    scheduler.finish("first", "success")
    with pytest.raises(SchedulerHold):
        scheduler.claim("next", "a" * 64, 2800, 4000, approvals(scheduler, "next"))
    clock[0] += 61
    scheduler.claim("next", "a" * 64, 2800, 4000, approvals(scheduler, "next"))


def test_minute_reset_preserves_uncertain_reservation(tmp_path, monkeypatch):
    import time
    scheduler = make(tmp_path, (1,))
    now = time.time()
    monkeypatch.setattr("app.extraction.organization_scheduler.time.time", lambda: now)
    scheduler.claim("r", "a" * 64, 2130, 4000, approvals(scheduler))
    scheduler.record_attempt("r", uncertain=True, category="transient_network")
    scheduler.finish("r", "uncertain")
    now += 86401
    with pytest.raises(SchedulerHold):
        scheduler.claim("next", "a" * 64, 2130, 4000, approvals(scheduler, "next"))


def test_full_java_document_at_actual_ceilings(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    from app.ingestion.transcript_parser import parse_transcript
    from app.extraction.chunker import ContentChunker
    from app.extraction.organization_extraction import prepare_request
    from app.extraction.organization_scheduler import digest
    document = parse_transcript(Path(__file__).resolve().parents[2] / "java.txt",
                                min_segment_words=50, max_segment_words=500, detect_timestamps=True)
    chunks = ContentChunker().chunk(document.source_units, document.document_id)
    import time
    clock = [time.time()]
    monkeypatch.setattr('app.extraction.organization_scheduler.time.time', lambda: clock[0])
    results = []
    for slot in range(1, 6):
        directory = tmp_path / str(slot)
        directory.mkdir()
        scheduler = make(directory, (slot,))
        for index, chunk in enumerate(chunks):
            clock[0] += 61
            request = f"slot-{slot}-chunk-{index}"
            try:
                payload, budget = prepare_request(chunk, scheduler.configuration)
            except SchedulerHold:
                results.append({'slot':slot,'chunk':chunk.chunk_id,'reserved_tokens':None,'outcome':'HOLD'})
                continue
            records = approvals(scheduler, request, digest(payload))
            assert budget.total_tokens == 6800
            def response(request):
                from tests.test_organization_extraction import envelope
                unit = next(unit for unit in document.source_units if unit.source_id == chunk.source_units[0])
                quote = unit.text
                content = {"concepts": [{"concept_name": quote.split()[0], "content": quote,
                    "source_unit_ids": [unit.source_id], "source_evidence": [
                        {"source_id": unit.source_id, "quote": quote, "fields": ["/concept_name", "/content"]}]}]}
                return httpx.Response(200, json=envelope(json.dumps(content)))
            try:
                extract_chunk(scheduler, request, chunk, document.source_units,
                              document.document_id, records, transport=httpx.MockTransport(response))
                outcome = "success"
            except SchedulerHold:
                outcome = "HOLD" if budget.total_tokens > 6800 else "validation_failed"
            results.append({"slot": slot, "chunk": chunk.chunk_id,
                            "reserved_tokens": budget.total_tokens, "outcome": outcome})
    assert len(chunks) == 18
    assert len(results) == len(chunks) * 5
    assert all(row['outcome'] in ('success','HOLD') for row in results)
    assert all(row['reserved_tokens'] is None or row['reserved_tokens']<=6800 for row in results)
    (tmp_path / "full_document_results.json").write_text(json.dumps(results, indent=2))
