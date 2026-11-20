"""Coverage-matched local mock comparison and reproducible estimates."""
import json
import math
from pathlib import Path
from unittest.mock import Mock

from app.extraction.prompts import CATEGORY_FIELDS, EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from app.extraction.token_budget import TokenBudgetManager

from fixtures import A, B, CHUNK, FACTS, SOURCES, compact, mock_a, mock_b, review_fact, review_field
from prototype import parser_for, reconstruct, run_offline


def main():
    first = Mock(side_effect=mock_a)
    second = Mock(side_effect=mock_b)
    result = run_offline(SOURCES, CHUNK, first, second, review_fact, review_field, FACTS.keys())
    assert result.status == "complete"
    expanded = {}
    for category, rows in B.items():
        expanded[category] = []
        for row in rows:
            evidence = reconstruct(row["evidence_refs"], FACTS, SOURCES)
            expanded[category].append({**{k: v for k, v in row.items() if k != "evidence_refs"},
                                       "source_evidence": evidence,
                                       "source_unit_ids": sorted({e["source_id"] for e in evidence})})
    single = Mock(return_value=compact(expanded))
    parser, chunk = parser_for(SOURCES, CHUNK)
    prompt = build_extraction_prompt(chunk.text_content, CHUNK, allowed_source_ids=list(SOURCES))
    baseline = parser._parse_response(single(prompt), chunk, "JAVA")
    signature = lambda items: {(i.knowledge_type, i.content, compact(i.extraction_metadata)) for i in items}
    assert signature(baseline) == signature(result.items)
    manager = TokenBudgetManager()

    def estimate(system, user, output, calls):
        size = len(output.encode("utf-8"))
        input_tokens = manager.estimate_request_tokens(user, system)
        output_tokens = math.ceil(size / 3.5)
        return dict(input_tokens_estimated=input_tokens, visible_output_tokens_estimated=output_tokens,
                    total_excluding_reasoning_estimated=input_tokens + output_tokens,
                    output_bytes=size, mock_calls=calls)

    a_system = (
        "Return a JSON facts array. Each row has fact_id, source_id, claim, quote, scope and optional "
        "relationships with relation and target_id. Use exact contiguous source quotes and canonical IDs. "
        "Use concise scoped atomic claims. Preserve distinct compiler errors and repairs. "
        "Omit uncertainty, inferred behavior, reconstructed code and universal claims."
    )
    b_system = (
        "Use only these validated facts. Return all eight category arrays, with content and required "
        "category fields. Every populated field needs an evidence_refs JSON Pointer entry with fact IDs. "
        "Preserve scope and coverage. Consolidate related facts without adding claims. "
        "Keep compiler errors separate. Express naming corrections explicitly, never as aliases. "
        + compact(CATEGORY_FIELDS)
    )
    one = estimate(EXTRACTION_SYSTEM_PROMPT, prompt, compact(expanded), single.call_count)
    a = estimate(a_system, chunk.text_content, compact(A), first.call_count)
    b = estimate(b_system, compact(A), compact(B), second.call_count)
    full_b_system = (
        "Use only these validated facts. Return all eight category arrays and existing common and subtype "
        "fields. Copy canonical source IDs and exact quotes into source_evidence and cite every populated "
        "field by JSON Pointer. Preserve scope, coverage and distinct teaching events. "
        + compact(CATEGORY_FIELDS)
    )
    full_b = estimate(full_b_system, compact(A), compact(expanded), 1)
    report = dict(single_stage=one, stage_a=a, stage_b=b, full_schema_b_counterfactual=full_b,
                  two_stage_total_excluding_reasoning_estimated=
                  a["total_excluding_reasoning_estimated"] + b["total_excluding_reasoning_estimated"],
                  intermediate_bytes=a["output_bytes"], reviewed_reference_facts=len(FACTS),
                  accepted_items=len(result.items), equal_mechanical_outputs=True,
                  note="Hand-authored outputs. No observed reasoning, latency or model reliability.")
    directory = Path(__file__).parent
    for name, payload in (("reference_facts.json", A), ("mock_stage_b.json", B),
                          ("mock_single_stage.json", expanded), ("comparison.json", report)):
        with (directory / name).open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
