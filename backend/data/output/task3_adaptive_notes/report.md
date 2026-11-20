# Task 3 — downstream integration and quality assurance

## Outcome
638 applicable offline regression tests passed, zero failed, zero skipped. An earlier development run had 15 failures caused by synthetic knowledge IDs not matching the existing required FCT_/PRC_ contract; those fixtures were corrected and the final combined suite passed. No live API calls were made. Eight synthetic cross-domain preview/evaluation pairs were generated. An actual TXT parser → mocked strict extraction → notes test also passed. No claim about live model quality, PDF/DOCX/PPTX conversion quality, OCR correctness or multimodal understanding follows from these tests.

## Dependency and integration audit
Current path: source/primary-context mapping → strict extraction → ID normalization → new exact consolidation → existing content analysis → existing deterministic selector → conservative representation safety filter → existing assembler → hardened Markdown renderer → five independent quality gates. Existing structural and semantic evaluator regressions run alongside the new gate report. Existing deterministic semantic checks are heuristics, not entailment proof.

Task 2 metadata survives in a provenance sidecar and consolidated knowledge. Presentation/assembly models carry source IDs but not the full extraction metadata. The new report therefore retains primary/contextual mappings, original knowledge fields, original metadata and original-to-final ID mapping rather than pretending the presentation model independently holds every evidence association. Coverage uses primary IDs. Context-only S/C synthetic fixtures demonstrate one primary source covered and one contextual source not counted. In the runner, raw extraction/checkpoints remain intact; consolidation produces additional notes and manifests. Failed/incomplete runs still cannot claim extraction completion. Existing historical request identity, checkpoint recovery and quota/Stage A logic are unchanged.

## Consolidation
Only exact substantive equality within a category and document/section scope merges. All specific fields, qualifications, conditions, procedure order and formula strings participate in equality. Different provenance is unioned, original metadata retained, and every retain/merge decision logged. Duplicate IDs first use the existing audited normalizer. Cross-category items remain distinct. Overlapping procedures, paraphrases, different numerical values/experimental conditions, contradictory descriptions and algebraically equivalent but textually different formulas remain retained. Similarity is used only to propose review pairs, never to delete or establish semantic equivalence. General conflict detection remains a manual-review limitation; review pair counts are not counts of proven contradictions.

## Representations and rendering
All nine explicit rendering contracts pass synthetic tests: standard text, definition, comparison, flowchart, timeline, cause/effect, hierarchy, example and formula. Every malformed empty payload test reports a noncomplete result and reason. Existing selector and structural-schema tests also pass.

Audit found that selector comparison builders can synthesize Property/Subject/Object placeholders and timeline builders can synthesize Event labels. The guarded notes path falls back to source text when no explicit safe typed structure establishes the selected form; it retains the item and logs why. It does not claim universal automatic comparison/timeline construction. Hierarchies require an explicit is_a/part_of relationship, causal diagrams require explicit causal relationships, processes require procedure steps. Legacy selector APIs remain available; consumers wanting these safeguards must use build_preview/the integrated runner. Secondary presentations are disabled in this guarded path to avoid unreviewed duplication.

Renderer changes: source headings escaped, table pipes/newlines escaped, raw HTML escaped in text, dynamic literal fences for formulas, quoted entity-encoded Mermaid labels without the previous 50-character truncation, numeric flowchart node IDs beyond 26 steps, and original presentation payload retained when rendering falls back. These are deterministic syntax protections, not browser-level security certification or a full Mermaid parser validation. Code/math notation is retained in literal blocks. Fields omitted from a selected display are appended as labeled literal supplemental details; this prioritizes preservation, though the JSON presentation needs usability refinement before publication.

## Five independent gates
1. Extraction completion: PASS only when supplied required/completed chunk sets match; FAIL otherwise. The runner supplies its durable operation outcomes. It does not infer teaching completeness from chunk completion.
2. Structural validity: checks rendered item-ID retention; existing typed schemas and regression evaluators provide additional structural tests. This is not a complete Markdown/Mermaid grammar validator.
3. Evidence/semantic faithfulness: mechanical provenance errors fail; otherwise NEEDS_REVIEW. No semantic entailment PASS is fabricated.
4. Educational completeness: NEEDS_REVIEW, with primary sources lacking knowledge and loss/mapping diagnostics. Topic coverage is NOT_EVALUATED because no independently reviewed topic inventory exists.
5. Notes usability: NEEDS_REVIEW with rendering warnings/fallback reasons. No fabricated readability or educational score.

All generated notes carry UNVERIFIED PREVIEW. Structural item retention alone never certifies claim support or completeness. Supported/partially supported/unsupported/contradicted claim counts remain null; inconclusive counts reflect unreviewed items, not classified model errors. Original fields and examples are preserved, with remaining manual comparison required for topic-level gaps and qualification interpretation.

## Documents tested and actual outcomes
Eight controlled synthetic domains: programming, mathematics, biology, history, qualified research findings, technical procedures, presentation-derived text and ambiguous OCR-derived text. Each sample has two canonical units, one primary chunk, one context-only unit and one fact before/after consolidation. These are small policy/engineering examples, not realistic comprehensive notes evaluations. Cross_document_evaluation.json records counts, representation distribution, all five gates and inconclusive knowledge counts per domain. Samples use standard text where no richer supported structure exists. Separate tests cover exact repetition, paraphrases, different meanings, contradictory descriptions, formula strings, conditional findings, preserved procedure prerequisites/outcomes and all nine rendering payloads. No failed/incomplete synthetic work is hidden: the dedicated incomplete-chunk tests return gate 1 FAIL.

## Exact code files modified
- app/extraction/consolidation.py (new)
- app/evaluation/notes_pipeline.py (new)
- app/rendering/renderer.py
- run_authorized_java.py (post-extraction preview integration)
- tests/test_notes_quality_pipeline.py (new)

Artifacts: this report, eight *_preview.md, eight *_quality.json, cross_document_evaluation.json, next_request_unapproved.json, manual_review_checklist.md. Final regression XML: ../task3_complete.xml.

## Safety and next experiment
Recorded frozen Stage A/control Python hashes match. No credentials, approval inventory, organization databases, token usage or uncertain-request history were changed by implementation. Existing mocked safety regressions passed. The exact representative payload/hash is prepared in next_request_unapproved.json using the current Task 2 policy and model. It has PENDING approval fields, no PASS record and no executable authorization. Its token estimate fits the configured request ceiling; actual quota availability still requires live-state admission. Full current configuration fingerprint and run-bound manifest must be regenerated before any later authorized experiment because this task does not authorize one. The manual checklist specifies claim review, all five gates and criteria for expansion.

Ready for a separately authorized small engineering experiment, with manual review. Not ready to label full-document notes semantically verified or educationally complete. Remaining research/engineering limitations include general entailment and conflict resolution, topic inventories, semantic paraphrase equivalence, long-range context, rich typed comparison/timeline construction, OCR/visual uncertainty, polished supplemental layout and actual diagram-engine validation. The reusable pipeline, audit records, conservative fallback path and offline regression baseline are implemented; these unresolved qualities are explicitly exposed rather than scored as passed.
