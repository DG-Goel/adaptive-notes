"""Offline source-evidence contracts; quote matching never proves entailment."""
import json
from unittest.mock import patch

import pytest

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.models.knowledge import ExtractionChunk, KnowledgeDocument


TEXT = "A value is an expression. Repeat repeat. int x = 1; float or double."


def setup(raw, *, strict=True, text=TEXT, sid="T0022", category="concepts"):
    extractor = KnowledgeExtractor(MockLLMProvider(), verbose=False, strict_evidence=strict)
    extractor.valid_source_ids = {"T0022", "T0023"}
    extractor._evidence_sources = {"T0022": text, "T0023": "Different source."}
    chunk = ExtractionChunk(chunk_id="JAVA_CHUNK_000", source_units=[sid],
                            text_content=f"[{sid}] {text}")
    return extractor, chunk, json.dumps({category: [raw]})


def concept():
    return {"concept_name": "expression", "content": "A value is an expression.",
            "aliases": [], "source_unit_ids": ["T0022"]}


def evidence(fields=None, quote="A value is an expression.", sid="T0022"):
    return [{"source_id": sid, "quote": quote,
             "fields": fields if fields is not None else ["/concept_name", "/content"]}]


def parse(raw, **kwargs):
    extractor, chunk, response = setup(raw, **kwargs)
    return extractor._parse_response(response, chunk, "JAVA")[0]


@pytest.mark.parametrize("problem", ["missing", "empty", "fabricated", "cross_source",
                                      "outside_chunk", "missing_field", "wrong_case",
                                      "unknown_field", "wrong_shape"])
def test_strict_rejects_invalid_evidence(problem):
    raw = concept()
    raw["source_evidence"] = evidence()
    if problem == "missing":
        del raw["source_evidence"]
    elif problem == "empty":
        raw["source_evidence"] = []
    elif problem == "fabricated":
        raw["source_evidence"] = evidence(quote="Invented quotation")
    elif problem == "cross_source":
        raw["source_unit_ids"] = ["T0022", "T0023"]
        raw["source_evidence"] = evidence(sid="T0023")
    elif problem == "outside_chunk":
        raw["source_unit_ids"] = ["T0023"]
        raw["source_evidence"] = evidence(sid="T0023", quote="Different source.")
    elif problem == "missing_field":
        raw["source_evidence"] = evidence(fields=["/content"])
    elif problem == "wrong_case":
        raw["source_evidence"] = evidence(quote="a value is an expression.")
    elif problem == "unknown_field":
        raw["source_evidence"] = evidence(fields=["/nonexistent"])
    else:
        raw["source_evidence"] = {"quote": TEXT}
    with pytest.raises(ValueError, match="Source evidence validation failed"):
        parse(raw)


def test_unique_quote_offsets_and_round_trip():
    raw = concept()
    raw["source_evidence"] = evidence()
    item = parse(raw)
    record = item.extraction_metadata["source_grounding"]
    quote = record["evidence"][0]
    assert quote["source_id"] == "T0022"
    assert quote["start_char"] == 0
    assert quote["end_char"] == len("A value is an expression.")
    assert record["mechanically_valid"]
    assert record["semantic_entailment_verified"] is False
    doc = KnowledgeDocument(document_id="JAVA", source_filename="java.txt",
                            extraction_timestamp="test", concepts=[item], total_items=1)
    restored = KnowledgeDocument.model_validate_json(doc.model_dump_json())
    assert restored.concepts[0].extraction_metadata == item.extraction_metadata


@pytest.mark.parametrize("text,quote,count", [
    ("repeat repeat", "repeat", 2), ("aaaa", "aaa", 2),
])
def test_ambiguous_and_overlapping_quotes_have_no_invented_offsets(text, quote, count):
    raw = concept()
    raw["source_evidence"] = evidence(quote=quote)
    row = parse(raw, text=text).extraction_metadata["source_grounding"]["evidence"][0]
    assert row["match_count"] == count
    assert row["start_char"] is None
    assert row["end_char"] is None


def test_non_strict_legacy_missing_evidence_is_unchanged():
    item = parse(concept(), strict=False)
    assert item.extraction_metadata is None
    assert item.source_unit_ids == ["T0022"]


def test_non_strict_invalid_evidence_is_diagnostic_not_a_silent_filter():
    raw = concept()
    raw["source_evidence"] = evidence(quote="fabricated")
    item = parse(raw, strict=False)
    assert item.content == raw["content"]
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"] is False
    assert item.extraction_metadata["source_grounding"]["evidence"] == []


def test_existing_metadata_is_preserved():
    raw = concept()
    raw["source_evidence"] = evidence()
    extractor, chunk, _ = setup(raw)
    item = extractor._create_concept(raw, chunk, "JAVA")
    item.extraction_metadata = {"existing": {"preserve": True}}
    extractor._attach_source_evidence(item, raw, chunk)
    assert item.extraction_metadata["existing"] == {"preserve": True}


@pytest.mark.parametrize("category,raw", [
    ("concepts", {**concept(), "aliases": ["value"]}),
    ("definitions", {"term": "expression", "definition_text": "A value.",
                     "context": "Java", "content": "A value."}),
    ("explanations", {"topic": "expression", "explanation_text": "A value.",
                      "explanation_type": "functional", "content": "A value."}),
    ("examples", {"exemplifies": "expression", "example_text": "int x = 1;",
                  "example_type": "numerical", "content": "int x = 1;"}),
    ("facts", {"fact_text": "A value.", "fact_type": "empirical", "content": "A value."}),
    ("formulas", {"formula_text": "x = 1", "variables": {"x/y~": "value"},
                  "conditions": "float or double", "derivation": "A value.", "content": "x = 1"}),
    ("procedures", {"procedure_name": "example", "steps": ["First", "Second"],
                    "prerequisites": ["value"], "outcomes": "value", "content": "example"}),
    ("relationships", {"relationship_type": "requires", "subject": "expression",
                       "object": "value", "description": "A value.", "content": "A value."}),
])
def test_all_populated_substantive_fields_require_evidence(category, raw):
    raw = {**raw, "source_unit_ids": ["T0022"]}
    extractor, chunk, _ = setup(raw, category=category)
    creator = getattr(extractor, "_create_" + {
        "concepts": "concept", "definitions": "definition", "explanations": "explanation",
        "examples": "example", "facts": "fact", "formulas": "formula",
        "procedures": "procedure", "relationships": "relationship",
    }[category])
    item = creator(raw, chunk, "JAVA")
    fields = sorted(extractor._substantive_fields(item))
    raw["source_evidence"] = evidence(fields=fields)
    parsed = parse(raw, category=category)
    assert parsed.extraction_metadata["source_grounding"]["mechanically_valid"]
    raw["source_evidence"] = evidence(fields=fields[1:])
    with pytest.raises(ValueError, match="Missing evidence for fields"):
        parse(raw, category=category)
    if category == "formulas":
        assert "/variables/x~1y~0" in fields
    if category == "procedures":
        assert "/steps/0" in fields and "/steps/1" in fields


def test_strict_pipeline_indexes_original_source_and_keeps_accounting():
    from app.models.source import SourceDocument, SourceUnit
    raw = concept()
    raw["source_evidence"] = evidence()
    extractor = KnowledgeExtractor(
        MockLLMProvider(default_response=json.dumps({"concepts": [raw]})),
        verbose=False, strict_evidence=True,
    )
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
                            source_units=[SourceUnit(source_id="T0022", document_id="JAVA",
                                type="paragraph", content_role="content", text=TEXT, position=1)])
    result = extractor.extract(source)
    assert result.total_items == 1
    assert result.extraction_metadata["successful_roots"] == 1
    assert result.concepts[0].extraction_metadata["source_grounding"]["mechanically_valid"]


@pytest.mark.parametrize("scenario,required", [
    ("mention-only", "does not support explaining decrement"),
    ("spoken arithmetic", "Never reconstruct code"),
    ("literal code", "retain that exact snippet"),
    ("computed results", "Do not compute results"),
    ("alternatives", 'Preserve conditions, alternatives and scope'),
    ("incomplete passage", "never complete a missing sentence"),
])
def test_prompts_explicitly_constrain_transcript_failure_modes(scenario, required):
    user_prompt = build_extraction_prompt("[T0022] Source text.", "JAVA_CHUNK_000")
    assert required in EXTRACTION_SYSTEM_PROMPT
    assert required not in user_prompt  # One authoritative contract, not duplicated.
    assert "up to ~50" in user_prompt
    assert user_prompt.count('"source_evidence"') == 1
    assert "Empty categories are normal" in EXTRACTION_SYSTEM_PROMPT
    from app.extraction.prompts import CATEGORY_FIELDS
    assert len(CATEGORY_FIELDS) == 8
    assert all("- " + category + ":" in user_prompt for category in CATEGORY_FIELDS)


def test_matching_quote_does_not_establish_semantic_support():
    raw = concept()
    raw["content"] = "Decrement always decreases by one."
    raw["source_evidence"] = evidence(quote="We mention decrement.")
    item = parse(raw, text="We mention decrement.")
    report = item.extraction_metadata["source_grounding"]
    assert report["mechanically_valid"]
    assert report["semantic_entailment_verified"] is False


def test_quote_must_also_be_visible_in_actual_chunk():
    raw = concept()
    raw["source_evidence"] = evidence()
    extractor, chunk, response = setup(raw)
    chunk.text_content = "[T0022] Different visible text."
    with pytest.raises(ValueError, match="supplied source text"):
        extractor._parse_response(response, chunk, "JAVA")


def test_ambiguous_source_identifier_fails_strict_pipeline():
    from app.models.source import SourceDocument, SourceUnit
    raw = concept()
    raw["source_evidence"] = evidence()
    extractor = KnowledgeExtractor(
        MockLLMProvider(default_response=json.dumps({"concepts": [raw]})),
        verbose=False, strict_evidence=True, max_retries=0,
    )
    unit = SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph",
                      content_role="content", text=TEXT, position=1)
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
                            source_units=[unit, unit.model_copy(update={"position": 2})])
    result = extractor.extract(source)
    assert result.total_items == 0
    assert result.extraction_metadata["failed_roots"] == 1
    assert "Source evidence validation failed" in result.extraction_metadata["chunk_attempts"][0]["error"]


def test_missing_evidence_rejects_strict_pipeline_without_changing_legacy_mode():
    from app.models.source import SourceDocument, SourceUnit
    raw = concept()
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph",
                                  content_role="content", text=TEXT, position=1)])
    for strict, expected_count in [(False, 1), (True, 0)]:
        extractor = KnowledgeExtractor(
            MockLLMProvider(default_response=json.dumps({"concepts": [raw]})),
            verbose=False, max_retries=0, strict_evidence=strict,
        )
        result = extractor.extract(source)
        assert result.total_items == expected_count
        assert result.extraction_metadata["failed_roots"] == int(strict)


def test_exact_audited_dictionary_key_bypass_is_rejected():
    raw = {
        "formula_text": "x", "content": "x",
        "variables": {"Invented claim without support": ""},
        "source_unit_ids": ["T0022"],
        "source_evidence": [{"source_id": "T0022", "quote": "x",
                             "fields": ["/content", "/formula_text"]}],
    }
    with pytest.raises(ValueError, match="/variables/Invented claim without support"):
        parse(raw, text="x", category="formulas")


def test_populated_dictionary_key_requires_evidence_even_when_value_empty():
    raw = {"formula_text": "x", "content": "x", "variables": {"x/y~": ""},
           "source_unit_ids": ["T0022"],
           "source_evidence": evidence(fields=["/content", "/formula_text", "/variables/x~1y~0"], quote="x")}
    item = parse(raw, text="x", category="formulas")
    assert "/variables/x~1y~0" in KnowledgeExtractor._substantive_fields(item)
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False


def test_empty_optional_dictionary_creates_no_artificial_requirements():
    raw = {"formula_text": "x", "content": "x", "variables": {},
           "source_unit_ids": ["T0022"],
           "source_evidence": evidence(fields=["/content", "/formula_text"], quote="x")}
    assert KnowledgeExtractor._substantive_fields(parse(raw, text="x", category="formulas")) == {
        "/content", "/formula_text"}


def test_generic_nested_dictionary_keys_are_not_ignored():
    item = parse(concept(), strict=False)
    # Simulate a future dictionary-backed substantive field without changing schemas.
    payload = {"content": "x", "nested": {"a/b": {"c~": ""}}, "optional": {}}
    with patch.object(type(item), "model_dump", return_value=payload):
        fields = KnowledgeExtractor._substantive_fields(item)
    assert fields == {"/content", "/nested/a~1b", "/nested/a~1b/c~0"}


@pytest.mark.parametrize("value", [None, [], {}, "bad", [None]])
def test_explicit_invalid_evidence_records_legacy_diagnostics(value):
    raw = concept()
    raw["source_evidence"] = value
    item = parse(raw, strict=False)
    assert item.content == raw["content"]
    assert item.source_unit_ids == ["T0022"]
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"] is False
    assert item.extraction_metadata["source_grounding"]["validation_errors"]
    with pytest.raises(ValueError, match="Source evidence validation failed"):
        parse(raw, strict=True)


def test_compact_skeleton_is_valid_json_and_all_eight_categories_are_empty():
    from app.extraction.prompts import RESPONSE_SKELETON
    prompt = build_extraction_prompt("[T0022] Source.", "test")
    tail = prompt.split("RESPONSE SKELETON (empty arrays are valid; replace only supported categories)", 1)[1].lstrip()
    skeleton, _ = json.JSONDecoder().raw_decode(tail)
    assert skeleton == RESPONSE_SKELETON
    assert set(skeleton) == {"concepts", "definitions", "explanations", "examples",
                             "facts", "formulas", "procedures", "relationships"}
    assert all(value == [] for value in skeleton.values())
    extractor, chunk, _ = setup(concept())
    assert extractor._parse_response(json.dumps(skeleton), chunk, "JAVA") == []


def test_category_contracts_match_all_existing_type_specific_schema_fields():
    from app.extraction.prompts import CATEGORY_FIELDS
    from app.models.knowledge import (KnowledgeItem, Concept, Definition, Explanation,
        Example, Fact, Formula, Procedure, Relationship)
    types = [Concept, Definition, Explanation, Example, Fact, Formula, Procedure, Relationship]
    for (category, contract), schema in zip(CATEGORY_FIELDS.items(), types):
        type_fields = set(schema.model_fields) - set(KnowledgeItem.model_fields)
        assert set(contract["required"]) | set(contract["optional"]) == type_fields
        assert not set(contract["required"]) & set(contract["optional"])


def test_single_evidence_example_omits_optional_fields_and_has_only_valid_paths():
    from app.extraction.prompts import EVIDENCE_EXAMPLE
    prompt = build_extraction_prompt("[T0022] Source.", "test")
    marker = "Example source [EXAMPLE_ONLY]: An expression is a piece of code that produces a value."
    example, _ = json.JSONDecoder().raw_decode(prompt.split(marker, 1)[1].lstrip())
    assert example == EVIDENCE_EXAMPLE
    assert "aliases" not in example
    extractor = KnowledgeExtractor(MockLLMProvider(), strict_evidence=True, verbose=False)
    extractor.valid_source_ids = {"EXAMPLE_ONLY"}
    extractor._evidence_sources = {"EXAMPLE_ONLY": "An expression is a piece of code that produces a value."}
    chunk = ExtractionChunk(chunk_id="example", source_units=["EXAMPLE_ONLY"],
        text_content="[EXAMPLE_ONLY] An expression is a piece of code that produces a value.")
    item = extractor._parse_response(json.dumps({"concepts": [example]}), chunk, "test")[0]
    actual_paths = set(example["source_evidence"][0]["fields"])
    assert actual_paths == extractor._substantive_fields(item)
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False


def test_full_t0022_source_and_grounding_contract_survive_with_smaller_messages():
    from pathlib import Path
    from app.extraction.chunker import ContentChunker
    from app.extraction.prompts import SOURCE_GROUNDING_RULES
    from app.extraction.token_budget import TokenBudgetManager
    from app.models.source import SourceDocument
    baseline = Path(__file__).resolve().parents[1] / "data/output/groq_strict_smoke_20261101_224317_936110"
    old = json.loads((baseline / "assembled_messages.json").read_text(encoding="utf-8"))
    source = SourceDocument.model_validate_json((baseline / "source_units.json").read_text(encoding="utf-8"))
    chunk = ContentChunker().chunk(source.source_units, source.document_id)[0]
    prompt = build_extraction_prompt(chunk.text_content, chunk.chunk_id)
    assert source.source_units[0].text in prompt
    assert prompt.count(source.source_units[0].text) == 1
    assert SOURCE_GROUNDING_RULES == EXTRACTION_SYSTEM_PROMPT
    assert "AUTHORITATIVE SOURCE-GROUNDING CONTRACT" not in prompt
    assert len(prompt) < len(old["user"])
    assert len(EXTRACTION_SYSTEM_PROMPT) < len(old["system"])
    manager = TokenBudgetManager()
    previous = manager.calculate_budget(old["user"], system_text=old["system"])
    current = manager.calculate_budget(prompt, system_text=EXTRACTION_SYSTEM_PROMPT)
    assert current.input_tokens < previous.input_tokens
    assert current.max_output_tokens <= 4000
    assert current.max_output_tokens == min(4000, current.tpm_limit - current.input_tokens)
    assert current.is_safe


def test_compaction_preserves_all_grounding_restrictions():
    required = [
        "No invented information", "Never reconstruct code or formulas",
        "declarations, comments, casts, outputs, aliases, or relationships",
        "Do not compute results unless explicitly stated",
        "Preserve conditions, alternatives and scope", "float or double",
        "universal rule", "required prerequisite", "uncertainty",
        "transcription ambiguity", "never complete a missing sentence",
        "Omission is preferable", "Mechanical quotation matching is not semantic entailment",
        "Populated dictionary keys require evidence", "Empty categories are normal",
        "Omit unsupported optional fields entirely", "only JSON Pointer paths to populated",
    ]
    assert all(phrase in EXTRACTION_SYSTEM_PROMPT for phrase in required)


def test_complete_outgoing_request_configuration_is_preserved():
    from app.extraction.llm_provider import GroqProvider
    from app.extraction.prompts import EVIDENCE_EXAMPLE
    from app.models.source import SourceDocument, SourceUnit
    from unittest.mock import Mock
    example = dict(EVIDENCE_EXAMPLE)
    example["source_unit_ids"] = ["T0022"]
    example["source_evidence"] = [
        {**EVIDENCE_EXAMPLE["source_evidence"][0], "source_id": "T0022"}]
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph",
             content_role="content", text="An expression is a piece of code that produces a value.", position=1)])
    with patch("groq.Groq") as constructor:
        client = constructor.return_value
        client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps({"concepts": [example]})), finish_reason="stop")],
            model="openai/gpt-oss-120b", usage=Mock(prompt_tokens=100, completion_tokens=100, total_tokens=200))
        provider = GroqProvider(model="openai/gpt-oss-120b", api_key="unit-test-only", use_multi_key=False)
        extractor = KnowledgeExtractor(provider, strict_evidence=True, verbose=False,
                                       max_retries=0, max_split_depth=0)
        chunk = extractor.chunker.chunk(source.source_units, source.document_id)[0]
        user = build_extraction_prompt(
            chunk.text_content, chunk.chunk_id, allowed_source_ids=chunk.source_units
        )
        budget = extractor.token_budget.calculate_budget(user, system_text=EXTRACTION_SYSTEM_PROMPT)
        result = extractor.extract(source)
    assert result.total_items == 1
    assert result.concepts[0].extraction_metadata["source_grounding"]["mechanically_valid"]
    client.chat.completions.create.assert_called_once_with(
        model="openai/gpt-oss-120b",
        messages=[{"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                  {"role": "user", "content": user}],
        temperature=0.0, max_tokens=budget.max_output_tokens,
        response_format={"type": "json_object"})
    assert provider.key_pool is None
    assert extractor.strict_evidence is True


def test_empty_failed_generation_is_permanent_one_attempt_no_rotation():
    import httpx
    from groq import BadRequestError
    from app.extraction.llm_provider import GroqProvider
    from app.models.source import SourceDocument, SourceUnit
    body = {"error": {"message": "Failed to validate JSON. Please adjust your prompt.",
                     "type": "invalid_request_error", "code": "json_validate_failed",
                     "failed_generation": ""}}
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph",
             content_role="content", text="An expression produces a value.", position=1)])
    with patch("groq.Groq") as constructor:
        client = constructor.return_value
        response = httpx.Response(400, request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"))
        client.chat.completions.create.side_effect = BadRequestError(
            body["error"]["message"], response=response, body=body)
        provider = GroqProvider(model="openai/gpt-oss-120b", api_key="unit-test-only", use_multi_key=False)
        # Test that even a retry-capable outer loop stops at the permanent provider error.
        extractor = KnowledgeExtractor(provider, strict_evidence=True, verbose=False, max_retries=2)
        result = extractor.extract(source)
    client.chat.completions.create.assert_called_once()
    constructor.assert_called_once()
    assert provider.last_error_metadata["error_code"] == "json_validate_failed"
    assert provider.last_error_metadata["category"] == "permanent_request"
    assert provider.last_error_metadata["retryable"] is False
    assert provider.key_pool is None
    assert body["error"]["failed_generation"] == ""
    assert result.total_items == 0
    assert result.extraction_metadata["total_attempts"] == 1
    assert result.extraction_metadata["retry_attempts"] == 0
    assert result.extraction_metadata["split_chunks"] == []
    assert result.extraction_metadata["failed_roots"] == 1


# Real validator regressions: parent collection evidence never covers children.
def procedure_with_arrays():
    return {"procedure_name": "Process", "content": "Read, transform, save.",
            "steps": ["Read", "Transform", "Save"],
            "prerequisites": ["Input", "Permission"], "source_unit_ids": ["T0022"]}


def test_three_steps_and_multiple_prerequisites_require_individual_paths():
    raw = procedure_with_arrays()
    paths = ["/procedure_name", "/content", "/steps/0", "/steps/1", "/steps/2",
             "/prerequisites/0", "/prerequisites/1"]
    raw["source_evidence"] = evidence(fields=paths)
    item = parse(raw, category="procedures")
    assert KnowledgeExtractor._substantive_fields(item) == set(paths)
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False


@pytest.mark.parametrize("missing", ["/steps/0", "/steps/1", "/steps/2",
                                     "/prerequisites/0", "/prerequisites/1"])
def test_one_missing_array_element_is_rejected(missing):
    raw = procedure_with_arrays()
    paths = ["/procedure_name", "/content", "/steps/0", "/steps/1", "/steps/2",
             "/prerequisites/0", "/prerequisites/1"]
    raw["source_evidence"] = evidence(fields=[p for p in paths if p != missing])
    with pytest.raises(ValueError, match=missing):
        parse(raw, category="procedures")


@pytest.mark.parametrize("parent", ["/steps", "/prerequisites"])
def test_parent_collection_path_cannot_replace_element_paths(parent):
    raw = procedure_with_arrays()
    paths = ["/procedure_name", "/content", "/steps/0", "/steps/1", "/steps/2",
             "/prerequisites/0", "/prerequisites/1"]
    raw["source_evidence"] = evidence(fields=[p for p in paths if not p.startswith(parent + "/")] + [parent])
    with pytest.raises(ValueError, match="invalid substantive field paths"):
        parse(raw, category="procedures")


def test_multiple_aliases_each_need_evidence_and_parent_is_invalid():
    raw = concept()
    raw["aliases"] = ["value", "term"]
    paths = ["/concept_name", "/content", "/aliases/0", "/aliases/1"]
    raw["source_evidence"] = evidence(fields=paths)
    assert parse(raw).extraction_metadata["source_grounding"]["mechanically_valid"]
    raw["source_evidence"] = evidence(fields=paths[:-1])
    with pytest.raises(ValueError, match="/aliases/1"):
        parse(raw)
    raw["source_evidence"] = evidence(fields=["/concept_name", "/content", "/aliases"])
    with pytest.raises(ValueError, match="invalid substantive field paths"):
        parse(raw)


@pytest.mark.parametrize("path", ["/aliases/0", "/context", "/prerequisites/0"])
def test_evidence_for_omitted_optional_field_is_rejected(path):
    raw = concept()
    raw.pop("aliases")
    raw["source_evidence"] = evidence(fields=["/concept_name", "/content", path])
    with pytest.raises(ValueError, match="invalid substantive field paths"):
        parse(raw)


def test_rfc6901_formula_dictionary_key_evidence_is_exact():
    raw = {"formula_text": "a/b~", "content": "a/b~", "variables": {"a/b~": "value"},
           "source_unit_ids": ["T0022"]}
    raw["source_evidence"] = evidence(fields=["/formula_text", "/content", "/variables/a~1b~0"])
    assert parse(raw, category="formulas").extraction_metadata["source_grounding"]["mechanically_valid"]
    raw["source_evidence"] = evidence(fields=["/formula_text", "/content", "/variables/a/b~"])
    with pytest.raises(ValueError, match="invalid substantive field paths"):
        parse(raw, category="formulas")


def test_nested_dictionary_and_array_paths_are_validated_without_schema_changes():
    raw = concept()
    extractor, chunk, _ = setup(raw)
    item = extractor._create_concept(raw, chunk, "JAVA")
    # The current Formula dictionary is flat; simulate a future nested field only here.
    payload = {"content": "x", "nested": {"a/b~": {"c/~": ["one", "two"]}}}
    paths = ["/content", "/nested/a~1b~0", "/nested/a~1b~0/c~1~0",
             "/nested/a~1b~0/c~1~0/0", "/nested/a~1b~0/c~1~0/1"]
    raw["source_evidence"] = evidence(fields=paths)
    with patch.object(type(item), "model_dump", return_value=payload):
        extractor._attach_source_evidence(item, raw, chunk)
        assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
        raw["source_evidence"] = evidence(fields=paths[:-1])
        with pytest.raises(ValueError, match="/nested/a~1b~0/c~1~0/1"):
            extractor._attach_source_evidence(item, raw, chunk)


def test_saved_smoke_procedure_parent_mismatch_and_path_only_repair():
    from pathlib import Path
    from app.extraction.chunker import ContentChunker
    from app.models.source import SourceDocument
    directory = Path(__file__).resolve().parents[1] / "data/output/groq_compact_smoke_20261101_173556_937901"
    source = SourceDocument.model_validate_json((directory / "source_units.json").read_text(encoding="utf-8"))
    raw = json.loads((directory / "parsed_response.json").read_text(encoding="utf-8"))["procedures"][0]
    extractor = KnowledgeExtractor(MockLLMProvider(), strict_evidence=True, verbose=False)
    extractor.valid_source_ids = {"T0022"}
    extractor._evidence_sources = {"T0022": source.source_units[0].text}
    chunk = ContentChunker().chunk(source.source_units, source.document_id)[0]
    with pytest.raises(ValueError, match="invalid substantive field paths"):
        extractor._parse_response(json.dumps({"procedures": [raw]}), chunk, "JAVA")
    raw["source_evidence"][0]["fields"] = ["/procedure_name", "/content", "/steps/0", "/steps/1", "/steps/2"]
    item = extractor._parse_response(json.dumps({"procedures": [raw]}), chunk, "JAVA")[0]
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
    # The reconstructed casting example still exists: fixing paths proves no entailment.
    assert "(double) numerator" in item.steps[0]
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False


def test_prompt_explicit_array_contract_and_quality_contrasts():
    required = ["individual paths for every populated alias, step, prerequisite",
                "a parent collection path such as /steps never substitutes",
                "RFC 6901", "/variables/a~1b~0", "/steps/2", "/prerequisites/1",
                "/aliases/1", "Omitted arrays have no paths", "Match the whole claim",
                "not an unstated % symbol", "not an added", "truncates fractional part",
                "Preserve each once", "rather than duplicating", "x starting at 1 and printing 2",
                "declaration repair", "float-or-double alternatives", "pi-to-PI correction"]
    assert all(phrase in EXTRACTION_SYSTEM_PROMPT for phrase in required)
    user = build_extraction_prompt("[T0022] Complete source.", "test")
    assert "AUTHORITATIVE SOURCE-GROUNDING CONTRACT" not in user
    assert user.count('"source_evidence"') == 1


# Synthetic payloads below exercise raw shape and evidence mechanics, not entailment.
STRICT_CASES = [
    ("concepts", {"concept_name": "x"}, ["/concept_name"]),
    ("definitions", {"term": "x", "definition_text": "x"}, ["/term", "/definition_text"]),
    ("explanations", {"topic": "x", "explanation_text": "x"}, ["/topic", "/explanation_text"]),
    ("examples", {"exemplifies": "x", "example_text": "x"}, ["/exemplifies", "/example_text"]),
    ("facts", {"fact_text": "x"}, ["/fact_text"]),
    ("formulas", {"formula_text": "x"}, ["/formula_text"]),
    ("procedures", {"procedure_name": "x", "steps": ["x"]}, ["/procedure_name", "/steps/0"]),
    ("relationships", {"relationship_type": "x", "subject": "x", "object": "x"},
     ["/relationship_type", "/subject", "/object"]),
]


def strict_payload(specific, paths):
    return {**specific, "content": "x", "source_unit_ids": ["T0022"],
            "source_evidence": evidence(fields=["/content", *paths], quote="x")}


@pytest.mark.parametrize("category,specific,paths", STRICT_CASES)
def test_all_eight_categories_inherit_valid_common_fields(category, specific, paths):
    raw = strict_payload(specific, paths)
    item = parse(raw, category=category, text="x")
    assert item.content == "x"
    assert item.source_unit_ids == ["T0022"]
    assert item.extraction_metadata["source_grounding"]["mechanically_valid"]
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False
    prompt = build_extraction_prompt("[T0022] x", "JAVA_CHUNK_000", allowed_source_ids=["T0022"])
    assert f"- {category}: required COMMON + " in prompt
    assert "Category requirements add to COMMON; they never replace it" in prompt


@pytest.mark.parametrize("category,specific,paths", STRICT_CASES)
@pytest.mark.parametrize("missing", ["content", "source_unit_ids", "source_evidence"])
def test_all_eight_categories_reject_missing_common_fields_before_construction(category, specific, paths, missing):
    raw = strict_payload(specific, paths)
    del raw[missing]
    extractor, chunk, response = setup(raw, category=category, text="x")
    with patch.object(extractor, "_create_concept", side_effect=AssertionError("constructor ran")):
        with pytest.raises(ValueError, match=f"/{category}/0/{missing}: missing required field"):
            extractor._parse_response(response, chunk, "JAVA")
    assert extractor.knowledge_id_counter == 0


@pytest.mark.parametrize("category,specific,paths,missing", [
    (category, specific, paths, name)
    for category, specific, paths in STRICT_CASES for name in specific
])
def test_required_subtype_fields_are_not_filled_from_defaults(category, specific, paths, missing):
    raw = strict_payload(specific, paths)
    del raw[missing]
    extractor, chunk, response = setup(raw, category=category, text="x")
    with pytest.raises(ValueError, match=f"/{category}/0/{missing}: missing required field"):
        extractor._parse_response(response, chunk, "JAVA")
    assert extractor.knowledge_id_counter == 0


@pytest.mark.parametrize("category,specific,paths", STRICT_CASES)
def test_explicit_empty_content_is_distinct_from_missing_and_is_not_filled(category, specific, paths):
    raw = strict_payload(specific, paths)
    raw["content"] = ""
    raw["source_evidence"] = evidence(fields=paths, quote="x")
    item = parse(raw, category=category, text="x")
    assert item.content == ""
    assert "/content" not in KnowledgeExtractor._substantive_fields(item)
    assert item.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False
    del raw["content"]
    with pytest.raises(ValueError, match="/content: missing required field"):
        parse(raw, category=category, text="x")


@pytest.mark.parametrize("value", [None, 1, False, [], {}])
def test_wrong_type_common_content_is_rejected_as_supplied_not_missing(value):
    raw = concept()
    raw["content"] = value
    raw["source_evidence"] = evidence()
    with pytest.raises(ValueError, match="/content: expected string") as error:
        parse(raw)
    assert "missing required field" not in str(error.value)


@pytest.mark.parametrize("item_id,evidence_id", [
    ("JAVA_CHUNK_000", "JAVA_CHUNK_000"), ("T0022", "JAVA_CHUNK_000"),
    ("JAVA_CHUNK_000", "T0022"), ("T0023", "T0023"),
])
def test_strict_raw_contract_rejects_scheduling_or_unsupplied_sources(item_id, evidence_id):
    raw = concept()
    raw["source_unit_ids"] = [item_id]
    raw["source_evidence"] = evidence(sid=evidence_id)
    extractor, chunk, response = setup(raw)
    with pytest.raises(ValueError, match="invalid canonical"):
        extractor._parse_response(response, chunk, "JAVA")
    assert extractor.knowledge_id_counter == 0
    assert raw["source_unit_ids"] == [item_id]  # Never rewrite the response.


def test_strict_raw_contract_is_atomic_when_later_category_is_invalid():
    good = concept()
    good["source_evidence"] = evidence()
    bad = strict_payload({"relationship_type": "x", "subject": "x"}, ["/relationship_type", "/subject"])
    extractor, chunk, _ = setup(good)
    with patch.object(extractor, "_create_concept", side_effect=AssertionError("constructor ran")):
        with pytest.raises(ValueError, match="/relationships/0/object: missing required field"):
            extractor._parse_response(json.dumps({"concepts": [good], "relationships": [bad]}), chunk, "JAVA")
    assert extractor.knowledge_id_counter == 0


def test_missing_content_cannot_be_hidden_by_evidence_for_a_constructor_default():
    raw = concept()
    del raw["content"]
    raw["source_evidence"] = evidence()
    with pytest.raises(ValueError, match="/content: missing required field"):
        parse(raw)


def test_all_required_content_paths_remain_required_after_raw_contract_passes():
    for category, specific, paths in STRICT_CASES:
        raw = strict_payload(specific, paths)
        raw["source_evidence"] = evidence(fields=paths, quote="x")
        with pytest.raises(ValueError, match="Missing evidence for fields: /content"):
            parse(raw, category=category, text="x")


def test_saved_twenty_one_item_response_is_rejected_without_mutation():
    from pathlib import Path
    directory = Path(__file__).resolve().parents[1] / "data/output/groq_repaired_t0022_smoke_20261101_175834_117672"
    original = (directory / "parsed_response.json").read_text(encoding="utf-8")
    data = json.loads(original)
    extractor, chunk, _ = setup(concept())
    with pytest.raises(ValueError) as error:
        extractor._parse_response(original, chunk, "JAVA")
    assert "invalid canonical source ID" in str(error.value)
    assert str(error.value).count("/content: missing required field") == 21
    assert extractor.knowledge_id_counter == 0
    # A separate synthetic copy with fixed IDs still fails missing content.
    for rows in data.values():
        for row in rows:
            row["source_unit_ids"] = ["T0022"]
            for entry in row["source_evidence"]:
                entry["source_id"] = "T0022"
    with pytest.raises(ValueError, match="/content: missing required field"):
        extractor._parse_response(json.dumps(data), chunk, "JAVA")
    assert (directory / "parsed_response.json").read_text(encoding="utf-8") == original


@pytest.mark.parametrize("data", [[], None, {"concepts": None}, {"concepts": [None]}])
def test_strict_raw_contract_rejects_invalid_container_shapes(data):
    extractor, chunk, _ = setup(concept())
    with pytest.raises(ValueError, match="Strict raw contract"):
        extractor._parse_response(json.dumps(data), chunk, "JAVA")
    assert extractor.knowledge_id_counter == 0


def test_late_evidence_failure_does_not_publish_earlier_valid_items():
    from app.models.source import SourceDocument, SourceUnit
    good = strict_payload({"concept_name": "x"}, ["/concept_name"])
    bad = strict_payload({"fact_text": "x"}, ["/fact_text"])
    bad["source_evidence"] = evidence(fields=["/content"], quote="x")
    provider = MockLLMProvider(default_response=json.dumps({"concepts": [good], "facts": [bad]}))
    extractor = KnowledgeExtractor(provider, strict_evidence=True, verbose=False,
                                   max_retries=0, max_split_depth=0)
    source = SourceDocument(document_id="JAVA", filename="java.txt", page_count=1,
        source_units=[SourceUnit(source_id="T0022", document_id="JAVA", type="paragraph",
                                  content_role="content", text="x", position=22)])
    result = extractor.extract(source)
    assert result.total_items == 0
    assert result.get_all_items() == []
    assert result.extraction_metadata["failed_roots"] == 1
    assert "Missing evidence for fields: /fact_text" in result.extraction_metadata["chunk_attempts"][0]["error"]
    assert provider.call_count == 1


def test_manually_authored_consolidation_reference_preserves_distinct_t0022_facts():
    """A reference contract fixture, not proof of actual model consolidation/entailment."""
    from pathlib import Path
    from app.models.source import SourceDocument
    from app.extraction.chunker import ContentChunker
    directory = Path(__file__).resolve().parents[1] / "data/output/groq_repaired_t0022_smoke_20261101_175834_117672"
    source = SourceDocument.model_validate_json((directory / "source_units.json").read_text(encoding="utf-8"))
    text = source.source_units[0].text
    final_error = "cannot assign a value to final variable pi"
    cause = "we have a compilation error because on the left side we declared an integer but here the result of this expression is a double"
    repair = "so to fix this problem we need to change this to double"
    alternatives = "if you want to get a floating-point number here you need to convert these numbers to a float or a double"
    naming = "pi is a final variable or a constant now by convention we use all capital letters to name constants so this should be PI"
    increment = "we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2"
    assert all(q in text for q in [final_error, cause, repair, alternatives, naming, increment])
    def fact(claim, quote):
        return {"fact_text": claim, "content": claim, "source_unit_ids": ["T0022"],
                "source_evidence": evidence(fields=["/fact_text", "/content"], quote=quote)}
    division = "In this example: " + alternatives + "; " + cause + "; " + repair
    data = {"facts": [fact("In this example, " + final_error, final_error),
                      fact("By convention the demonstrated pi should be named PI.", naming)],
            "explanations": [{"topic": "compilation error", "content": division,
                "explanation_text": division, "source_unit_ids": ["T0022"],
                "source_evidence": [
                    *evidence(fields=["/topic", "/content", "/explanation_text"], quote=cause),
                    *evidence(fields=["/content", "/explanation_text"], quote=repair),
                    *evidence(fields=["/content", "/explanation_text"], quote=alternatives)]}],
            "examples": [{"exemplifies": "increment operator", "content": increment,
                "example_text": increment, "source_unit_ids": ["T0022"],
                "source_evidence": evidence(fields=["/exemplifies", "/example_text", "/content"], quote=increment)}]}
    extractor = KnowledgeExtractor(MockLLMProvider(), strict_evidence=True, verbose=False)
    extractor.valid_source_ids = {"T0022"}
    extractor._evidence_sources = {"T0022": text}
    chunk = ContentChunker().chunk(source.source_units, source.document_id)[0]
    items = extractor._parse_response(json.dumps(data), chunk, "JAVA")
    assert len(items) == 4
    assert final_error in data["facts"][0]["content"]
    assert repair not in data["facts"][0]["content"]
    assert cause in division and repair in division and alternatives in division
    assert final_error not in division
    assert "pi should be named PI" in data["facts"][1]["content"]
    assert all("aliases" not in row for rows in data.values() for row in rows)
    assert "we set it to 1" in increment and "we get 2" in increment
    assert len({i.content for i in items}) == 4
    assert all(i.extraction_metadata["source_grounding"]["mechanically_valid"] for i in items)
    assert all(i.extraction_metadata["source_grounding"]["semantic_entailment_verified"] is False for i in items)
    for phrase in ["Keep the two errors separate", "declaration repair does not fix final-variable assignment",
                   "naming, never an alias", "Aliases require source-stated synonyms, not instance names",
                   "avoid redundant term-only items", "Preserve each once with its source scope"]:
        assert phrase in EXTRACTION_SYSTEM_PROMPT
