# Missing common content

All 21 raw items omit content and /content evidence. The raw HTTP JSON proves this is not a parser/SDK field-removal defect.

KnowledgeItem requires content: str. The prompt states that every populated object requires content, source_unit_ids and source_evidence. Its single complete example includes content. Thus the prompt is logically consistent with the model, but every category line independently says required and lists only subtype fields. A model can misread these as complete field sets, overlooking the shared inheritance paragraph. This is a likely presentation/compliance cause, not proven internal causality. JSON object mode sends no JSON Schema to enforce required keys.

The parser constructs model objects rather than directly validating raw items against KnowledgeItem. _create_concept falls back to concept_name for missing content; definition/explanation/example/fact constructors use their main text; procedure uses its name; relationship defaults to empty text. Required model-field presence is therefore satisfied by application defaults before evidence checking.

Confirmed raw-contract enforcement gap from code inspection: strict evidence checks normalized substantive fields, not explicit raw content presence. A hypothetical item missing content but supplying valid /content evidence for the derived value can pass those mechanical checks. This is not claimed to have happened in the latest test: all items lack /content evidence, and original execution rejects length before parsing. Existing offline diagnostics reject all 21.

Minimal proposal: in strict mode, validate explicit raw common/subtype required fields and types before constructors/filtering, with category/index/missing-key diagnostics. Keep strict_evidence=False defaults unchanged. Do not waive /content evidence or accept a parent path.

For concise output, make category lines explicitly COMMON + additional fields. Keep content and subtype main text required. One exact quote may list both /content and the applicable main-text path only if it supports both. Every populated alias, step, prerequisite and dictionary key still needs its independent escaped path. Do not omit required fields, derive away evidence requirements, or introduce a new evidence indirection schema to save tokens.
