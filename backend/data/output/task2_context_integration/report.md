# Task 2: context-aware extraction integration

## Implementation
New opt-in `context_grounded_v3` policy uses the existing model and Groq strict schema. Existing policies remain available; historical authorizations are not rewritten. No approvals were created and no credentials or live state were changed.

`document_plan` binds Task 1 adjacent context to each initial, fitted and recovery chunk. Serialized chunk metadata retains primary IDs separately from context IDs/text/limitations. Context is reselected after splitting and the complete prompt plus schema enters token estimation. `prepare_request` serializes labeled excerpt roles and both ID lists. `extract_chunk` recomputes context from canonical source units, so runtime context must match the approved payload hash. The extractor uses a bounded evidence view for strict validation, while the prompt stays exactly equal to the approved prompt. Saved-response recovery uses the same evidence view. No contextual units enter primary work counts.

The Stage A path still recomputes and compares the document plan and exact payload. Configuration fingerprints now include context policy/selection and claim-review code. A new policy, context change or source change therefore requires a newly prepared manifest and fresh authorization. None was issued in this task. Synthetic request_evidence.json records the actual request builder output and input/output budget; it is explicitly unapproved.

## Evidence contract
Every knowledge item must cite at least one primary excerpt. Context-only topics and context-only exclusions fail. Multiple valid references can support individual fields across the boundary. The union evidence view preserves canonical IDs and exact source text; the normal strict raw-contract validator runs before model constructors. Unknown IDs/quotes and missing field evidence remain errors. Cited-and-excluded contradictions remain rejected, including the unchanged November 7 response. Common content must exactly equal the main category text for definitions, explanations, examples, facts and formulas; this prevents divergent duplicate representations.

Primary IDs are copied into accepted item metadata; coverage reporting uses those IDs rather than contextual evidence IDs. Context overlap cannot count as independently processed primary work. Context-only extraction is rejected to limit overlap duplication. This does not prove semantic nonduplication for two paraphrased items that both cite a primary excerpt; that still requires review/consolidation.

## Universal prompts and schema
The prompt retains Task 1 mixed/noisy/incomplete/uncertain source handling and adds explicit primary ownership, contextual-evidence permissions, conditions and field consistency. The field-evidence wire schema is retained to avoid duplicating schema overhead. New labeled request serialization is deterministic. Schema and all context text are included in the budget; existing source-preserving output-reserve fitting and bounded truncation recovery remain in place. Context limit is 1,000 characters, whole adjacent units only. Oversized neighbors are reported rather than truncated silently. Long-range dependencies and context within a split source fragment need further work; the selector currently works at canonical-unit adjacency, not fragment adjacency.

## Mechanical versus semantic validation
Mechanical validation confirms syntax, required fields, exact evidence location, field coverage, primary ownership and common/category consistency. It does NOT prove that the quotation entails the claim. All v3 items remain semantic_verified=false. Claim review emits conservative signals for numbers absent from cited evidence, potentially lost may/under/only/if/approximately qualifiers and mismatched negation. These identify candidates for unsupported, partial or contradicted claims; they are not final classifications. False positives and missed paraphrases are possible. Added context never promotes a claim to semantic_verified=true. General claim-level entailment, formula/code validity and complete qualification preservation require independent review; no offline heuristic can establish universal semantic support.

## Files modified
- app/models/knowledge.py
- app/extraction/source_context.py
- app/extraction/context_grounding.py (new)
- app/extraction/claim_review.py (new)
- app/extraction/organization_scheduler.py (configuration schema/fingerprinting only)
- app/extraction/organization_extraction.py
- app/extraction/document_authorization.py
- app/extraction/saved_response_recovery.py
- run_authorized_java.py (coverage attribution only)
- tests/test_authorized_runner.py
- tests/test_context_grounding.py (new)

## Validation and remaining readiness
Cross-domain synthetic fixtures cover mathematics, biology, history, qualified research, technical instructions and Java. Tests check actual request context, deterministic hashing, changed-context hashes, multiple references, canonical IDs, context-only item/exclusion rejection, missing raw fields, text inconsistency and conservative semantic signals. The mocked SDK runner executes the v3 plan and checkpoint/resume path. Task 1 fixtures retain PDF/PPTX/OCR policy coverage without claiming real parser quality.

No Groq requests, live extraction, credential activation or authorizations. Historical frozen files match recorded hashes. The model/provider and quota/Stage A enforcement are unchanged. Task 3 has not begun. The request integration is ready for review and fresh authorization, while semantic quality, paraphrase deduplication, long-range dependencies and real-format/model performance remain limitations. Do not infer live quality improvement from these fixtures.

Final applicable offline regression suite: 494 passed, 0 failed, 0 skipped (46.99 seconds). Machine-readable results: ../task2_offline_final.xml. The suite includes mocked SDK execution, strict evidence, Task 1 source policy, source splitting, saved response recovery, serialization, quota accounting and frozen Stage A/control regressions.
