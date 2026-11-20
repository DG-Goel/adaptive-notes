from copy import deepcopy
from unittest.mock import Mock

import pytest

from fixtures import A, B, CHUNK, FACTS, SOURCES, compact, mock_a, mock_b, review_fact, review_field
from prototype import MockResponse, run_offline


def exercise(a=None, b=None, finish_a="stop", finish_b="stop"):
    first = Mock(side_effect=mock_a) if a is None and finish_a == "stop" else Mock(
        return_value=MockResponse(compact(A if a is None else a), finish_a))
    second = Mock(side_effect=mock_b) if b is None and finish_b == "stop" else Mock(
        return_value=MockResponse(compact(B if b is None else b), finish_b))
    result = run_offline(SOURCES, CHUNK, first, second, review_fact, review_field, FACTS.keys())
    assert first.call_count == 1
    return result, second


def test_success_preserves_coverage_and_exact_evidence():
    result, second = exercise()
    assert result.status == "complete"
    assert second.call_count == 1
    assert len(result.items) == 9
    items = {item.content: item for item in result.items}
    for fid in ("f001", "f002", "f005", "f006"):
        assert FACTS[fid].claim in items
    procedure = next(item for item in result.items if item.knowledge_type == "procedure")
    assert FACTS["f003"].claim in procedure.content and FACTS["f004"].claim in procedure.content
    assert FACTS["f001"].claim not in procedure.content
    assert not any(getattr(item, "aliases", []) for item in result.items)
    for item in result.items:
        grounding = item.extraction_metadata["source_grounding"]
        assert grounding["mechanically_valid"] and not grounding["semantic_entailment_verified"]
        assert item.source_unit_ids == ["T0022"]
        for entry in grounding["evidence"]:
            assert entry["quote"] in SOURCES[entry["source_id"]]
    quotes = {entry["quote"] for entry in procedure.extraction_metadata["source_grounding"]["evidence"]}
    assert quotes == {FACTS["f003"].quote, FACTS["f004"].quote}


@pytest.mark.parametrize("field,value", [
    ("quote", "cannot assign a value ... change this to double"),
    ("source_id", CHUNK),
    ("fact_id", "bad"),
    ("scope", "universal"),
    ("claim", "Decrement decreases by one."),
    ("claim", "The compiler rejects assignment to every final variable after initialization."),
])
def test_invalid_a_never_calls_b(field, value):
    data = deepcopy(A)
    data["facts"][0][field] = value
    result, second = exercise(a=data)
    assert (result.status, result.stage, result.items) == ("failed", "A", ())
    second.assert_not_called()


def test_a_omission_and_b_coverage_loss():
    result, second = exercise(a={"facts": A["facts"][1:]})
    assert (result.status, result.stage, result.items) == ("incomplete", "A", ())
    second.assert_not_called()
    data = deepcopy(B)
    data["facts"].pop(1)
    result, second = exercise(b=data)
    assert (result.status, result.stage, result.items) == ("incomplete", "B", ())
    second.assert_called_once()


@pytest.mark.parametrize("mutation", [
    lambda row: row["evidence_refs"].update({"/content": ["f999"]}),
    lambda row: row["evidence_refs"].update({"/content": []}),
    lambda row: row["evidence_refs"].pop("/content"),
    lambda row: row.pop("steps"),
    lambda row: row.update(content="Decrement decreases by one."),
    lambda row: row.update(content="Always change integer declarations to double."),
    lambda row: row.update(source_unit_ids=[CHUNK]),
    lambda row: row["evidence_refs"].update({"/steps": ["f004"]}),
    lambda row: row["evidence_refs"].update({"/content": ["f001"]}),
])
def test_b_failure_rejects_entire_output(mutation):
    data = deepcopy(B)
    mutation(data["procedures"][0])
    result, second = exercise(b=data)
    second.assert_called_once()
    assert (result.status, result.stage, result.items) == ("failed", "B", ())


def test_duplicate_output_rejected():
    data = deepcopy(B)
    data["facts"].append(deepcopy(data["facts"][0]))
    result, _ = exercise(b=data)
    assert result.status == "failed" and "Duplicate" in result.error
    assert not result.items


@pytest.mark.parametrize("stage", ["A", "B"])
def test_valid_json_length_is_incomplete(stage):
    result, second = exercise(finish_a="length" if stage == "A" else "stop",
                              finish_b="length" if stage == "B" else "stop")
    assert (result.status, result.stage, result.items) == ("incomplete", stage, ())
    assert second.call_count == (stage == "B")


def test_all_eight_category_shapes_with_separate_synthetic_source():
    from app.extraction.prompts import CATEGORY_FIELDS
    from prototype import AtomicFact, stage_b

    rows = {
        "concepts": {"concept_name": "area"},
        "definitions": {"term": "area", "definition_text": "A measure of surface."},
        "explanations": {"topic": "area", "explanation_text": "Area is measured in square units."},
        "examples": {"exemplifies": "area", "example_text": "A unit square has area one."},
        "facts": {"fact_text": "A square has equal sides."},
        "formulas": {"formula_text": "A = s²", "variables": {"s/~": "side"}},
        "procedures": {"procedure_name": "Measure", "steps": ["Measure a side."]},
        "relationships": {"relationship_type": "is a", "subject": "square", "object": "rectangle"},
    }
    evidence_fields = {
        "formulas": ["/formula_text", "/variables/s~1~0"],
        "procedures": ["/procedure_name", "/steps/0"],
    }
    sources = {"S1": "Synthetic shape fixture."}
    facts = {}
    wire = {category: [] for category in CATEGORY_FIELDS}
    for index, (category, fields) in enumerate(rows.items(), 1):
        fid = f"f{index:03}"
        facts[fid] = AtomicFact(fact_id=fid, source_id="S1", claim=category,
                               quote=sources["S1"], scope="synthetic schema exercise")
        paths = evidence_fields.get(category, ["/" + key for key in fields])
        wire[category].append({**fields, "content": category,
                               "evidence_refs": {path: [fid] for path in ["/content", *paths]}})
    # Shape-only reviewer for this synthetic schema test. No semantic claim is made.
    items = stage_b(MockResponse(compact(wire)), facts, sources, "CHUNK", lambda *_: True)
    assert len(items) == 8
