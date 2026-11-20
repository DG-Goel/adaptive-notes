"""Offline recovery workflow tests; provider requests are always mocked."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import recover_t0018_exhaustive as recovery
from app.models.knowledge import Concept, KnowledgeDocument
from app.models.source import SourceDocument, SourceUnit


def source():
    return SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[SourceUnit(source_id=sid, document_id="JAVA", position=i,
                    type="paragraph", content_role="content", text="First topic. Second topic.")
                      for i, sid in enumerate(["T0017", "T0018"], 1)])


def knowledge(sid="T0017", content="First topic.", identifier="CON_0001"):
    return KnowledgeDocument(document_id="JAVA", source_filename="java.txt",
        extraction_timestamp="2026-11-01", total_items=1,
        concepts=[Concept(knowledge_id=identifier, document_id="JAVA",
                          source_unit_ids=[sid], content=content, concept_name=content)])


def review(document, disposition="INCLUDE"):
    return {"items": [{
        "category": cat, "item_index": index,
        "item_fingerprint": recovery.fingerprint(item.model_dump(mode="json")),
        "disposition": disposition, "reason": "Individually compared with source",
        "reviewer": "test reviewer", "full_item_reviewed": True,
        "source_evidence": [{"source_id": item.source_unit_ids[0], "quote": "First topic."}],
    } for cat, index, item in recovery.entries(document)]}


def smoke(s):
    return {"provider": "Groq", "model": recovery.MODEL, "real_request": True,
        "status": "PASSED", "command": "recorded command", "timestamp": "2026-11-01",
        "source_fingerprint": recovery.fingerprint(s.model_dump(mode="json")),
        "response_metadata": {"model": recovery.MODEL, "finish_reason": "stop",
                             "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}},
        "knowledge": knowledge().model_dump(mode="json"),
        "manual_review": {"approved": True, "reviewer": "tester", "reason": "Reviewed full extraction"}}


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def boundaries(s):
    unit = s.source_units[1]
    return {"source_fingerprint": recovery.fingerprint(unit.model_dump(mode="json")),
        "reviewer": "tester", "reviewed": True,
        "segments": [
            {"start": 0, "end": 13, "reason": "Sentence boundary", "context_preserved": True},
            {"start": 13, "end": len(unit.text), "reason": "Complete next topic", "context_preserved": True},
        ]}


def result(sid="T0018", valid=True):
    document = knowledge(sid)
    document.extraction_metadata = {
        "extraction_successful": valid, "scheduled_roots": 1, "failed_roots": int(not valid),
        "skipped_roots": 0, "root_outcomes": [{"outcome": "SUCCESS" if valid else "FAILED"}],
    }
    return document


def test_smoke_gate_precedes_provider_construction_and_output_creation(tmp_path):
    s = write(tmp_path / "sources.json", source().model_dump(mode="json"))
    b = write(tmp_path / "base.json", knowledge(content="Other").model_dump(mode="json"))
    t = write(tmp_path / "t17.json", knowledge().model_dump(mode="json"))
    args = ["--sources", str(s), "--base", str(b), "--t0017", str(t),
            "--output", str(tmp_path / "fresh"), "--execute-t0018"]
    with patch.object(recovery, "GroqProvider") as provider:
        with pytest.raises(ValueError, match="smoke"):
            recovery.main(args)
        provider.assert_not_called()
    assert not (tmp_path / "fresh").exists()


@pytest.mark.parametrize("field,value", [("model", "other"), ("provider", "Other"),
                                        ("real_request", False), ("status", "FAILED")])
def test_smoke_gate_rejects_wrong_model_provider_and_unverified_evidence(tmp_path, field, value):
    evidence = smoke(source())
    evidence[field] = value
    path = write(tmp_path / "smoke.json", evidence)
    with pytest.raises(ValueError, match="BLOCKED"):
        recovery.require_smoke(path, source())


def test_valid_smoke_evidence_and_stale_source(tmp_path):
    path = write(tmp_path / "smoke.json", smoke(source()))
    assert recovery.require_smoke(path, source())["model"] == recovery.MODEL
    changed = source()
    changed.source_units[0].text = "Changed"
    with pytest.raises(ValueError, match="match"):
        recovery.require_smoke(path, changed)


def test_explicit_paths_and_no_overwrite(tmp_path):
    with pytest.raises(SystemExit):
        recovery.main([])
    with pytest.raises(ValueError, match="overwrite"):
        recovery.main(["--sources", "s", "--base", "b", "--t0017", "t", "--output", str(tmp_path)])
    with pytest.raises(SystemExit):
        recovery.main(["--sources", "s", "--base", "b", "--t0017", "t",
                       "--output", "fresh", "--model", "another-model"])


def test_review_is_item_specific_and_default_pending():
    k, s, base = knowledge(), source(), knowledge(content="Other")
    decisions, report = recovery.review_items(k, s, base, canonical_id="T0017")
    assert decisions[0].action == "pending"
    assert report["items"][0]["original_item"] == k.concepts[0].model_dump(mode="json")
    rows = review(k)
    decisions, _ = recovery.review_items(k, s, base, rows, canonical_id="T0017")
    assert decisions[0].action == "include"
    rows["items"][0]["item_fingerprint"] = "stale"
    with pytest.raises(ValueError, match="Stale"):
        recovery.review_items(k, s, base, rows, canonical_id="T0017")


def test_exact_duplicate_requires_consolidation_and_distinct_items_get_unique_ids():
    s, k, base = source(), knowledge(), knowledge()
    with pytest.raises(ValueError, match="duplicate"):
        recovery.review_items(k, s, base, review(k), canonical_id="T0017")
    rows = review(k, "EXACT_DUPLICATE")
    rows["items"][0]["target_id"] = "CON_0001"
    decisions, _ = recovery.review_items(k, s, base, rows, canonical_id="T0017")
    merged = recovery.merge_recovered_knowledge(base, k, s, artifact_id="r", decisions=decisions)
    assert merged.document.total_items == 1
    distinct = knowledge(content="Second topic.")
    rows = review(distinct)
    rows["items"][0]["source_evidence"][0]["quote"] = "Second topic."
    decisions, _ = recovery.review_items(distinct, s, base, rows, canonical_id="T0017")
    merged = recovery.merge_recovered_knowledge(base, distinct, s, artifact_id="r", decisions=decisions)
    assert merged.document.total_items == 2
    assert len({item.knowledge_id for item in merged.document.get_all_items()}) == 2


def test_review_rejects_bad_evidence_and_provenance():
    k, s = knowledge(), source()
    rows = review(k)
    rows["items"][0]["source_evidence"][0]["quote"] = "Invented source text"
    with pytest.raises(ValueError, match="exact source"):
        recovery.review_items(k, s, knowledge(content="Other"), rows, canonical_id="T0017")
    with pytest.raises(ValueError, match="provenance"):
        recovery.review_items(knowledge("T0018"), s, knowledge(), canonical_id="T0017")


def test_source_boundaries_preserve_every_character_and_context():
    s = source()
    parts = recovery.segments_for(s.source_units[1], boundaries(s))
    assert "".join(part["text"] for part in parts) == s.source_units[1].text
    assert len(recovery.segments_for(s.source_units[1])) == 1
    invalid = boundaries(s)
    invalid["segments"][0]["end"] = 3
    with pytest.raises(ValueError, match="within a word"):
        recovery.segments_for(s.source_units[1], invalid)
    invalid = boundaries(s)
    invalid["segments"][1]["end"] -= 1
    with pytest.raises(ValueError, match="omits"):
        recovery.segments_for(s.source_units[1], invalid)


@pytest.mark.parametrize("partial", [False, True])
def test_segment_accounting_canonical_provenance_and_partial_preservation(partial):
    s = source()
    with patch("groq.Groq"):
        provider = recovery.GroqProvider(api_key="test-only", use_multi_key=False)
    documents = [result(), result(valid=not partial)]
    before = s.model_dump()
    with patch.object(recovery.KnowledgeExtractor, "extract", side_effect=documents) as extract:
        candidate, records = recovery.extract_t0018(s, provider, smoke_evidence=smoke(s), manifest=boundaries(s))
    assert extract.call_count == 2
    assert s.model_dump() == before
    assert all(call.args[0].source_units[0].source_id == "T0018" for call in extract.call_args_list)
    assert candidate.total_items == 2
    assert len({item.knowledge_id for item in candidate.get_all_items()}) == 2
    assert all(item.source_unit_ids == ["T0018"] for item in candidate.get_all_items())
    assert [row["outcome"] for row in records] == ["SUCCESS", "FAILED" if partial else "SUCCESS"]
    assert recovery.finalize_status(candidate, records, {"items": []}, None, s) == (
        "PARTIAL" if partial else "PENDING_REVIEW")


def test_zero_items_and_unresolved_segments_never_report_recovered():
    empty = knowledge()
    empty.concepts = []
    empty.update_statistics()
    assert recovery.finalize_status(empty, [{"outcome": "SUCCESS"}], {"items": []}, {}, source()) == "FAILED"
    assert recovery.finalize_status(knowledge(), [{"outcome": "NOT_ATTEMPTED"}],
                                    {"items": []}, {}, source()) == "PARTIAL"


def test_topic_review_required_for_recovered():
    s, candidate = source(), knowledge("T0018")
    _, report = recovery.review_items(candidate, s, knowledge(content="Other"),
                                      review(candidate), canonical_id="T0018")
    topic = {"review_fingerprint": recovery.fingerprint({
                "candidate": candidate.model_dump(mode="json"), "source": s.model_dump(mode="json")}),
             "complete": True, "source_reviewed_in_full": True, "reviewer": "tester", "unresolved_gaps": [],
             "topics": [{"reason": "Covered", "knowledge_ids": ["CON_0001"],
                         "source_id": "T0018", "source_quote": "First topic."}]}
    assert recovery.finalize_status(candidate, [{"outcome": "SUCCESS"}], report, topic, s) == "RECOVERED"
    topic["unresolved_gaps"] = ["Missing example"]
    assert recovery.finalize_status(candidate, [{"outcome": "SUCCESS"}], report, topic, s) == "PENDING_REVIEW"


def test_offline_runner_preserves_historical_inputs(tmp_path):
    s = write(tmp_path / "sources.json", source().model_dump(mode="json"))
    b = write(tmp_path / "base.json", knowledge(content="Other").model_dump(mode="json"))
    t = write(tmp_path / "t17.json", knowledge().model_dump(mode="json"))
    before = {path: path.read_bytes() for path in (s, b, t)}
    with patch.object(recovery, "GroqProvider") as provider:
        assert recovery.main(["--sources", str(s), "--base", str(b), "--t0017", str(t),
                              "--output", str(tmp_path / "new")]) == 2
        provider.assert_not_called()
    assert all(path.read_bytes() == raw for path, raw in before.items())


def test_all_real_t0017_items_validate_and_remain_individually_pending():
    root = Path(__file__).resolve().parents[1]
    original = root / "data/output/java_transcript_validation/validation_20261101_143618/recovered_T0017_20261101_153250.json"
    base_dir = root / "data/output/complete_e2e_validation/validation_20261101_174430"
    k = KnowledgeDocument.model_validate(recovery.load(original))
    s = SourceDocument.model_validate(recovery.load(base_dir / "source_units.json"))
    base = KnowledgeDocument.model_validate(recovery.load(base_dir / "knowledge_corrected_v2.json"))
    raw = original.read_bytes()
    decisions, report = recovery.review_items(k, s, base, canonical_id="T0017")
    assert len(decisions) == report["items_checked"] == 23
    assert all(decision.action == "pending" for decision in decisions)
    assert original.read_bytes() == raw

def test_direct_helper_also_enforces_smoke_and_no_fallback():
    with patch("groq.Groq"):
        provider = recovery.GroqProvider(api_key="test-only", use_multi_key=False)
    bad = smoke(source())
    bad["real_request"] = False
    with patch.object(recovery.KnowledgeExtractor, "extract") as extract:
        with pytest.raises(ValueError, match="BLOCKED"):
            recovery.extract_t0018(source(), provider, smoke_evidence=bad)
        extract.assert_not_called()
    provider.model = "other-model"
    with pytest.raises(ValueError, match="requires Groq"):
        recovery.extract_t0018(source(), provider, smoke_evidence=smoke(source()))


def test_exception_retains_completed_segment_results_and_marks_unattempted():
    s = source()
    with patch("groq.Groq"):
        provider = recovery.GroqProvider(api_key="test-only", use_multi_key=False)
    with patch.object(recovery.KnowledgeExtractor, "extract",
                      side_effect=[result(), RuntimeError("controlled failure")]):
        candidate, records = recovery.extract_t0018(
            s, provider, smoke_evidence=smoke(s), manifest=boundaries(s))
    assert candidate.total_items == 1
    assert [row["outcome"] for row in records] == ["SUCCESS", "FAILED"]
    recovery.validate_candidate(candidate, records, s)


@pytest.mark.parametrize("tamper", ["text", "items", "accounting"])
def test_replayed_candidate_evidence_is_validated(tamper):
    s = source()
    with patch("groq.Groq"):
        provider = recovery.GroqProvider(api_key="test-only", use_multi_key=False)
    with patch.object(recovery.KnowledgeExtractor, "extract", return_value=result()):
        candidate, records = recovery.extract_t0018(s, provider, smoke_evidence=smoke(s))
    recovery.validate_candidate(candidate, records, s)
    if tamper == "text":
        records[0]["text"] = "changed"
    elif tamper == "items":
        candidate.concepts[0].content = "Invented"
    else:
        records[0]["accounting"]["failed_roots"] = 1
    with pytest.raises(ValueError, match="Candidate"):
        recovery.validate_candidate(candidate, records, s)
