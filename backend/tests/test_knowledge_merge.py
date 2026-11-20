"""Preservation, collision and reviewed-merge regression tests."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app.extraction.knowledge_merge import (
    CATEGORIES, MergeDecision, compare_preservation, merge_recovered_knowledge,
    normalize_knowledge_ids, resolve_knowledge_reference, validate_provenance,
)
from app.models.knowledge import Concept, KnowledgeDocument
from app.models.source import SourceDocument, SourceUnit


def item(identifier="CON_0001", content="Original", sources=None):
    return Concept(
        knowledge_id=identifier, document_id="JAVA", concept_name=content,
        content=content, source_unit_ids=sources if sources is not None else ["T0017"],
        section="Strings", page_range=(1, 1), aliases=["alias"],
        extraction_metadata={"evidence": "unchanged"},
    )


def doc(*items):
    return KnowledgeDocument(
        document_id="JAVA", source_filename="java.txt",
        extraction_timestamp="2026-11-01T00:00:00",
        concepts=list(items), total_items=len(items), source_units_processed=2,
        extraction_metadata={"completeness": 0.5},
    )


def source():
    return SourceDocument(
        document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[
            SourceUnit(source_id=sid, document_id="JAVA", type="paragraph",
                       text="Original evidence", position=index, content_role="content")
            for index, sid in enumerate(["T0017", "T0018"], 1)
        ],
    )


def test_deterministic_allocation_reserves_future_ids_and_preserves_input():
    original = doc(item(), item(content="Distinct"), item("CON_0002", "Third"))
    before = original.model_dump(mode="json")
    result = normalize_knowledge_ids(original, artifact_id="base")
    assert [value.knowledge_id for value in result.document.concepts] == [
        "CON_0001", "CON_0003", "CON_0002",
    ]
    assert original.model_dump(mode="json") == before
    assert result.preservation.passed
    assert result.preservation.reassigned_count == 1
    assert result.model_dump() == normalize_knowledge_ids(original, artifact_id="base").model_dump()
    again = normalize_knowledge_ids(result.document, artifact_id="normalized")
    assert again.document == result.document
    assert again.preservation.reassigned_count == 0
    result.document.concepts[0].aliases.append("new")
    assert original.concepts[0].aliases == ["alias"]


def test_identical_colliding_items_are_both_preserved():
    result = normalize_knowledge_ids(doc(item(), item()), artifact_id="base")
    assert result.document.total_items == 2
    assert len({value.knowledge_id for value in result.document.concepts}) == 2
    assert result.preservation.passed


def test_reference_resolution_requires_locator_for_collision():
    result = normalize_knowledge_ids(doc(item(), item(content="Other")), artifact_id="base")
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_knowledge_reference(result.mappings, artifact_id="base", old_id="CON_0001")
    assert resolve_knowledge_reference(
        result.mappings, artifact_id="base", old_id="CON_0001",
        category="concepts", item_index=1,
    ) == "CON_0002"
    with pytest.raises(ValueError, match="Missing"):
        resolve_knowledge_reference(result.mappings, artifact_id="wrong", old_id="CON_0001")


@pytest.mark.parametrize("field,value", [
    ("content", "changed"), ("concept_name", "changed"), ("knowledge_type", "fact"),
    ("source_unit_ids", ["T0018"]), ("document_id", "OTHER"),
    ("section", "changed"), ("page_range", (2, 2)),
    ("aliases", []), ("extraction_metadata", {"changed": True}),
])
def test_preservation_rejects_non_id_changes(field, value):
    original = doc(item())
    result = normalize_knowledge_ids(original, artifact_id="base")
    setattr(result.document.concepts[0], field, value)
    assert not compare_preservation(original, result.document, result.mappings).passed


def test_preservation_rejects_unapproved_id_changes_and_missing_items():
    original = doc(item(), item(content="Other"))
    result = normalize_knowledge_ids(original, artifact_id="base")
    result.document.concepts[0].knowledge_id = "CON_9000"
    assert not compare_preservation(original, result.document, result.mappings).passed
    result.document.concepts.pop()
    assert not compare_preservation(original, result.document, result.mappings).passed


def test_preservation_checks_document_metadata_and_mapping_completeness():
    original = doc(item())
    result = normalize_knowledge_ids(original, artifact_id="base")
    result.document.source_filename = "changed.txt"
    assert not compare_preservation(original, result.document, result.mappings).passed
    assert not compare_preservation(original, original, []).passed
    assert not compare_preservation(original, original, result.mappings * 2).passed


@pytest.mark.parametrize("invalid_id", ["", "bad", "DEF_0001"])
def test_invalid_existing_ids_fail_closed(invalid_id):
    with pytest.raises(ValueError, match="Invalid knowledge ID"):
        normalize_knowledge_ids(doc(item(invalid_id)), artifact_id="base")


@pytest.mark.parametrize("problem", ["empty", "missing", "item_document", "source_document", "duplicate_source", "canonical", "filename"])
def test_provenance_validation(problem):
    knowledge, evidence = doc(item()), source()
    if problem == "empty":
        knowledge.concepts[0].source_unit_ids = []
    elif problem == "missing":
        knowledge.concepts[0].source_unit_ids = ["T9999"]
    elif problem == "item_document":
        knowledge.concepts[0].document_id = "OTHER"
    elif problem == "source_document":
        evidence.source_units[0].document_id = "OTHER"
    elif problem == "duplicate_source":
        evidence.source_units.append(evidence.source_units[0].model_copy(deep=True))
    elif problem == "filename":
        knowledge.source_filename = "other.txt"
    report = validate_provenance(
        knowledge, evidence, required_source_id="T0018" if problem == "canonical" else None,
    )
    assert not report.valid
    assert report.errors


def test_reviewed_merge_preserves_inputs_and_distinct_items():
    base = doc(item())
    recovered = doc(item(content="Distinct", sources=["T0018"]))
    before_base, before_recovered = base.model_dump(), recovered.model_dump()
    result = merge_recovered_knowledge(
        base, recovered, source(), artifact_id="recovery",
        decisions=[MergeDecision(category="concepts", item_index=0, action="include",
                                 reason="Distinct and reviewed against T0018")],
        required_source_id="T0018",
    )
    assert result.provenance.valid
    assert result.document.total_items == 2
    assert result.document.concepts[1].knowledge_id == "CON_0002"
    assert result.document.concepts[1].source_unit_ids == ["T0018"]
    assert base.model_dump() == before_base
    assert recovered.model_dump() == before_recovered


def test_consolidation_requires_exact_equality_and_preserves_source_union():
    base, recovered = doc(item()), doc(item(sources=["T0018"]))
    decision = MergeDecision(category="concepts", item_index=0, action="consolidate",
                             target_id="CON_0001", reason="Exact duplicate, reviewed")
    result = merge_recovered_knowledge(
        base, recovered, source(), artifact_id="recovery", decisions=[decision],
    )
    assert result.document.total_items == 1
    assert result.document.concepts[0].source_unit_ids == ["T0017", "T0018"]
    assert base.concepts[0].source_unit_ids == ["T0017"]
    recovered.concepts[0].content = "Different"
    with pytest.raises(ValueError, match="exact"):
        merge_recovered_knowledge(base, recovered, source(), artifact_id="recovery", decisions=[decision])


@pytest.mark.parametrize("action", ["exclude", "pending"])
def test_invalid_candidates_remain_accounted_for_in_decisions(action):
    recovered = doc(item(sources=["invalid"]))
    decision = MergeDecision(category="concepts", item_index=0, action=action,
                             reason="Source evidence unresolved")
    result = merge_recovered_knowledge(
        doc(item()), recovered, source(), artifact_id="recovery", decisions=[decision],
    )
    assert result.document.total_items == 1
    assert result.decisions == [decision]
    assert not result.mappings


def test_merge_rejects_missing_duplicate_or_invalid_decisions_and_unnormalized_base():
    base, recovered = doc(item()), doc(item(content="Other"))
    decision = MergeDecision(category="concepts", item_index=0, action="include", reason="Reviewed")
    for decisions in ([], [decision, decision]):
        with pytest.raises(ValueError, match="Exactly one"):
            merge_recovered_knowledge(base, recovered, source(), artifact_id="r", decisions=decisions)
    recovered.concepts[0].source_unit_ids = ["invalid"]
    with pytest.raises(ValueError, match="provenance"):
        merge_recovered_knowledge(base, recovered, source(), artifact_id="r", decisions=[decision])
    with pytest.raises(ValueError, match="Normalize"):
        merge_recovered_knowledge(doc(item(), item()), doc(), source(), artifact_id="r", decisions=[])


def test_real_473_item_baseline_preservation(tmp_path):
    path = Path(__file__).resolve().parents[1] / (
        "data/output/complete_e2e_validation/validation_20261101_174430/knowledge_corrected_v2.json"
    )
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    original = KnowledgeDocument.model_validate(raw)
    result = normalize_knowledge_ids(original, artifact_id=path.as_posix())
    normalized = result.document.model_dump(mode="json")
    changed = []
    for category in CATEGORIES:
        assert len(raw[category]) == len(normalized[category])
        for index, (before, after) in enumerate(zip(raw[category], normalized[category])):
            before_fields, after_fields = dict(before), dict(after)
            before_id, after_id = before_fields.pop("knowledge_id"), after_fields.pop("knowledge_id")
            assert before_fields == after_fields
            if before_id != after_id:
                changed.append((category, index, before_id, after_id))
    assert {key: value for key, value in raw.items() if key not in CATEGORIES} == {
        key: value for key, value in normalized.items() if key not in CATEGORIES
    }
    assert result.preservation.passed
    assert result.preservation.before_count == result.preservation.after_count == 473
    assert result.preservation.before_unique_ids == 466
    assert result.preservation.after_unique_ids == 473
    assert result.preservation.reassigned_count == len(changed) == 7
    assert {entry[2] for entry in changed} == {
        "CON_0001", "CON_0002", "CON_0003", "CON_0004", "CON_0005", "DEF_0007", "DEF_0008",
    }
    assert len(original.get_all_items()) == len(result.document.get_all_items()) == 473
    assert path.read_bytes() == raw_bytes
    assert validate_provenance(result.document, SourceDocument.model_validate_json(
        (path.parent / "source_units.json").read_text(encoding="utf-8")
    )).valid
    # Independent JSON round-trip of the evidence, including every per-item comparison.
    evidence = tmp_path / "preservation.json"
    evidence.write_text(result.preservation.model_dump_json(indent=2), encoding="utf-8")
    saved = json.loads(evidence.read_text(encoding="utf-8"))
    assert saved["passed"] and all(row["passed"] for row in saved["item_comparisons"])
    assert saved["before_non_id_digest"] == saved["after_non_id_digest"]
    assert sha256(path.read_bytes()).hexdigest() == sha256(raw_bytes).hexdigest()
