# Task 6 — source-faithfulness repair and offline quality assessment

## Decision
**NEEDS_MORE_CORRECTION.** No Groq API calls, full reruns, automatic recovery authorizations, provider-usage edits or historical artifact overwrites occurred. The separate authoritative preview is student_notes/notes.md. New overall quality score remains unassigned.

## Root-cause matrix
| Defect | Source-to-output trace | Component / correction |
|---|---|---|
| Corrected FizzBuzz missing T0042 | T0041 describes desired output and wrong ordering; T0042 explicitly moves combined condition first. PRC_0397 /steps/3 cited T0041 only. | Evidence association repaired with the exact relevant T0042 passage; T0041 retained. Source T0029 was also inspected and added for Scanner package/terminal initialization. Primary work remains T0041; added sources are contextual evidence. |
| Error/correction disconnected | EXM_0174 labels incorrect results, EXP_0127 explains the mistake, EXM_0175 gives corrected ordering. | Source-backed instructional roles/links group error, explanation and correction in derived presentation. No absent correction invented. |
| Mortgage P*R fragment | T0031 continues into another expression/exponent; T0033 describes division; no full visual equation is available. FRM_0007 was formatted like a complete equation. | Keep VISUAL_CONTEXT_REQUIRED and available fragment. Missing visual source remains a real gap. No external mortgage formula supplied. |
| Arithmetic false positives | T0023 explicitly speaks the expressions and results 16/26. Both were warned only because no reviewed metadata existed. | Two expressions reviewed COMPLETE/SUPPORTED as paraphrased mathematics, not literal source code. Operand metadata remains separately reviewable; renderer label now says Symbols and operands. |
| Literal code reconstruction | Raw examples add declarations, variable names, comments and sometimes illustrative values not literally present. Earlier detector only covered examples and treated some behavior prose as literal-code claims. | Audit all substantive fields; distinguish code-like signal from literal-code form. Explicit reviewed paraphrases need not be verbatim. Source-only literal reconstructions remain withheld, original text preserved. |
| Lost qualifications | FCT_0352 makes nesting an absolute bad practice; DEF_0075 blurs DRY with a blanket ban. T0042 discusses trade-offs. | Two derived text revisions restore source-stated scope; original strings, exact source and reviewer rationale remain in changes.json. |
| Excessive quotation / verbosity | Old fallback copied long source excerpts repeatedly; source-level audit evidence became student prose. | Supporting quotes remain in field/presentation audit. Reviewed behavioral prose is retained; unsafe literal snippets get concise explicit review gaps, not repeated source walls. |
| Potential consolidation evidence loss | Generic exact merge unioned IDs but only actively exposed the first item's grounding evidence (other metadata was nested history). | Exact consolidation now unions/deduplicates all active evidence and retains validation errors; semantic certification remains false. Actual 92 candidates are not auto-deleted. |
| Failed work obscured by rendering | Source references/complete rendering could imply coverage despite two rejected operations. | Offline rebuild uses actual required primary IDs and durable accepted operations: extraction completion remains FAIL. |

## Field-level audit and review scope
1,237 substantive field leaves were screened across all eight knowledge categories. Exact paths include common content, names, definition/explanation text, individual procedure steps, formula/variable descriptions, examples and relationships. defect_inventory.json preserves original output, derived output, canonical source IDs, supporting quotes, status, severity, responsible stage where established, reviewer rationale and remaining review needs. student_notes/presentation_mapping.json traces representation strings to knowledge fields; render_manifest.json maps note spans to IDs. This mapping is not a proof of semantic entailment for Markdown.

The queue has 80 UNSUPPORTED literal-fidelity field records, corresponding to 40 snippets repeated in content/example_text—not 80 independently wrong algorithms. 37 reviewed fields are SUPPORTED, two PARTIALLY_SUPPORTED, and 1,118 NOT_REVIEWED. Review statuses concern specified fields and scope; reviewed literal-fidelity failures do not imply that every snippet's technical behavior is false. Numeric/qualification/negation signals remain heuristic. High-risk material is prioritized, never automatically accepted. Most semantic work is still unresolved.

## The 51 flagged examples
All 51 are enumerated with source passages and dispositions in code_fidelity_audit.json: 40 unsupported literal reconstructions, eight behavior-paraphrase false positives under the old literal-code interpretation, three partially supported/ambiguous examples. The latter three were revised from available source: remove an unstated illustrative number, remove an invented trim example string, and restore the otherwise qualification in the nested divisibility alternative. None is labeled as compiled code. No complete literal source snippets were established for this flagged set, so compilation was not used as a substitute for source fidelity.

Technical prose mentioning calls is now screened as HIGH risk, not automatically treated as a literal reproduction. Only literal-code forms or explicit adverse review dispositions trigger withholding. Procedure-step and other code-bearing fields are included in the queue. Positive/negative tests distinguish reviewed paraphrase from literal reproduction across multiple programming-language forms.

## Formula precision
formula_validation.json records the three cases. FRM_0014 and FRM_0015 have source-supported complete arithmetic expressions/results. FRM_0007 remains visually dependent and incomplete. Formula-shaped mathematical assignments are not automatically classified as code. Completeness annotations require explicit reviewed source evidence; other assumptions, variable descriptions or units are not thereby certified.

## Failed requests 4 and 45
failed_request_analysis.json records actual request IDs, primary/context IDs, context limitations, budgets, exact schema hashes, strict flag, schema validation and accepted-neighbor comparison. Mappings establish missing primary T0004 and T0045 rather than assuming request number equals source ID. The primary topics include project/SDK setup and input-reading/loop behavior; overlap with accepted neighbors means not every such topic is necessarily absent globally.

Both responses are known HTTP400 json_validate_failed, categorized permanent_request; diagnostics report missing required formulas. Actual provider usage/finish reason is unavailable. Stored diagnostic messages are bounded to about 1,022 characters; full original raw error bodies were not retained. Therefore neither the complete failed generation nor token exhaustion can be established from these logs.

Strict json_schema/strict:true was enabled. Draft 2020-12 validation passes, and objects have all properties required and additionalProperties:false. Accepted neighboring requests used the identical schema. Groq documents strict support for openai/gpt-oss-120b and those closed/required constraints, while also acknowledging reports of 400 errors: https://console.groq.com/docs/structured-outputs . The documentation inspected does not explicitly enumerate every constraint used here; provider subset compatibility and internal failure cause remain uncertain. Static schema validity is not proof of provider behavior. No unsupported assertion of token exhaustion or definitive provider bug is made.

The smallest proposed experiment is two lossless source-boundary fragments per failed parent, keeping model, strict schema and output reserve. targeted_recovery_plan.json has four new request identities/hashes (different payloads from failed parents) with PENDING_SEPARATE_AUTHORIZATION and no PASS record. A payload may match an unused historical contingency if identical, but that does not authorize activating it for this failure. Splitting is a complexity-reduction hypothesis, not a demonstrated fix. No failed request was replayed or switched to another organization.

## Consolidation and coverage
All 92 actual candidate pairs are exported with both contents and their source evidence in duplicate_review.json. Semantic equivalence/contradiction was not independently adjudicated, so each is honestly UNRESOLVED and retained. No similarity-only merge, no fabricated duplicate-removal count. This remains outstanding editorial work.

All 458 original items and their original field versions remain available. All 458 IDs are represented, but 46 items have fields held from ordinary student presentation pending review. This is explicitly reported; ID retention is not claimed as full factual-content display. Missing primary sources remain T0004/T0045. Topic completeness remains unestablished without a reviewed topic inventory.

## Preview comparison and gates
Original: 22,090 words, 46 sections. Corrected: approximately 18,112 words, 46 sections, zero internal JSON blocks. Reduction is about 18%, achieved through source-evidence separation and reviewed prose rather than a word target. No distinct supported fact was similarity-deleted. Withheld unsafe or uncertain fields remain in the audit and are visibly flagged. Chapter-level editorial refinement, long-range context and semantic deduplication remain needed.

Extraction completion FAIL; structural validity PASS; semantic faithfulness FAIL; educational completeness FAIL (missing work plus withheld fields); notes usability NEEDS_REVIEW. Repaired rendering does not hide these failures. No VERIFIED_STUDY_NOTES or new overall quality score is assigned. This is not a fresh live-model evaluation.

## Exact implementation files modified
- app/models/educational_review.py: field-level review modes and additional instructional relation kinds.
- app/evaluation/field_faithfulness.py (new): substantive-field paths, screening, literal/prose distinction and risk queue.
- app/evaluation/citation_repair.py (new): exact-evidence association and explicit versioned text edits.
- app/evaluation/educational_safeguards.py: precise formula handling, reviewed paraphrase support and all-field safety dispositions.
- app/evaluation/notes_pipeline.py: field queue and withheld-content coverage reporting.
- app/extraction/consolidation.py: preserve evidence from each exact duplicate contributor.
- app/rendering/renderer.py: neutral symbols/operands label.
- repair_saved_knowledge.py (new): non-overwriting offline rebuild and presentation audit.
- tests/test_field_faithfulness.py (new): cross-domain source review, code in procedures, formulas, citation permissions, consolidation evidence, targeted planning and actual saved-run repair.

No model, provider, production prompt, quota rule, credential approval or Stage A authorization changed in Task 6. Original November 9 artifacts and provider ledgers are checked byte-for-byte against the pre-task snapshot.

## Tests and limitations
Broad regression batch: 719 passed, 0 failed/skipped. Final targeted batch after arithmetic/formula and saved-benchmark refinements: 85 passed, 0 failed/skipped. Final renderer/field batch: 43 passed, 0 failed/skipped. These batches overlap and are not added as independent test totals. They include strict evidence, all nine representation contracts, authorization, quotas, uncertain recovery, historical baselines and frozen Stage A/control checks. Synthetic cross-domain fixtures do not certify real OCR, document parsing or model semantic quality.

Remaining critical/unresolved work: literal reconstructions retained only for review, substantial unreviewed fields, incomplete mortgage visual evidence, two missing primary extractions, all 92 duplicate adjudications, and independent topic/semantic/readability review. The prepared targeted recovery needs separate approval and source/context review. Current readiness remains NEEDS_MORE_CORRECTION; neither a full rerun nor VERIFIED_STUDY_NOTES is justified by these offline corrections.
