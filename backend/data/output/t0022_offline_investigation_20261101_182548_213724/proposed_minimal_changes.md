# Proposed minimal changes — NOT IMPLEMENTED

Exact implementation scope proposed for review:

1. app/extraction/prompts.py — build_extraction_prompt, SOURCE_GROUNDING_RULES, category-line assembly using CATEGORY_FIELDS.
   - Add an optional explicit canonical-source-ID argument after existing arguments, retaining compatibility. The extractor supplies actual chunk source-unit IDs; they are not synthesized or derived from scheduling labels.
   - Mark chunk_id as scheduling metadata that must never populate source_unit_ids or evidence.source_id. Explicitly enumerate allowed canonical IDs and point to their source markers. Preserve source text and canonical markers unchanged.
   - State COMMON REQUIRED once; each category explicitly requires COMMON + additional fields. Keep content and its evidence, the sole complete example, all eight category contracts, and the empty skeleton.
   - Use that existing example to contrast canonical source identity with non-citable scheduling identity; do not add another populated category template.
   - Compact semantic consolidation guidance: inventory explicitly stated teaching facts, preserve separate errors, group directly related cause/repair, distinguish instance names from aliases, and retain distinct examples/definitions only when they add information.
   - One exact quotation may list several independent field paths only if it supports each. Do not omit /content or auto-expand parent paths. Retain all conservative grounding restrictions and source-conditional coverage rules.

2. app/extraction/extractor.py — _extract_from_chunk and _parse_response; add a small private strict raw-response-contract check.
   - _extract_from_chunk passes an explicit canonical source-unit allowlist to prompt assembly. Root and child requests already use this function; no splitter change.
   - In strict_evidence=True, validate explicit raw common/subtype required fields and their types before constructors/default filling and source-ID filtering. Errors identify category/index, missing content or invalid references. Decide any empty-string policy explicitly before implementation; do not silently change legacy or semantic thresholds.
   - Preserve strict_evidence=False constructor defaults. Do not derive acceptable raw content or repair incorrect IDs in strict mode.
   - Keep _substantive_fields and _attach_source_evidence unchanged. Missing /content evidence, parent collection substitutions, bad quotations and noncanonical IDs still fail.
   - Do not modify retry loops, accounting, token-budget calls/policy, provider behavior, thresholds or truncation handling.

3. tests/test_extraction_grounding.py — add strict raw-contract, source/chunk identity, exact fixture and prompt-contract regressions. Read historical fixtures without mutation. Do not treat mocked responses as model-quality evidence.

4. tests/test_extraction_unit.py — update complete-message/request expectations and test unchanged legacy behavior for missing-content defaults. Cover root/child prompt assembly through existing interfaces without a real request.

No additions or edits are proposed to provider adapters, ingestion, source/knowledge schemas, chunker, splitter, token_budget.py, runner, recovery, representation selection or semantic verifier. No new extraction architecture or automatic postprocessing deletion.

Sequence: agree the shared raw contract, align prompt and strict raw checks, run focused mocked/local regressions, inspect full prompt/budget and preservation evidence, then request a separate readiness review. Existing budget/output allowance must be computed unchanged; no manual increase or instruction/source truncation.

Risks: probabilistic compliance, stricter raw validation exposing more malformed responses, ambiguous transcript context and accidental over-consolidation. Roll back only the approved implementation/test diff if necessary, keeping historical and new investigation artifacts intact. No live request is implied by approval of these changes.
