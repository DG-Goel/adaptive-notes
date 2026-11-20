# Task 5 implementation and offline findings

## Root-cause reconstruction
| Failure | Evidence and responsible stage | Implemented correction / limitation |
|---|---|---|
| Incorrect FizzBuzz | T0041 explicitly demonstrates a wrong ordering; T0042 repairs it. PRC_0332 lost this role at extraction; assembly rendered an ordinary procedure. EXP_0094 and EXM_0131/0132 already contain explanation/corrections. | Source-backed instructional roles and links, wrong-demonstration warning, shared section and role ordering. No invented correction. |
| Mortgage fragment | FRM_0003 retains only principal times interest from T0031. Source continues across T0032/T0033 and points at a visual expression. Extraction lost completeness; formula renderer implied completion. | VISUAL_CONTEXT_REQUIRED review; fragment shown with warning instead of complete formula. Missing visual formula remains unresolved. |
| Reconstructed code | EXM_0117 and other examples turn spoken demonstrations into literal declarations/comments absent verbatim from source. Mechanical field references do not detect semantic reconstruction. | Literal-substring check plus typed code review; student display uses available exact source passages. Original snippets remain in the audit; no compilation is claimed. |
| One Main Content section | Assembler ignored available section metadata; selection contract lacked section/position fields. Many transcript items also have no headings. | Propagate section/position, prefer explicit headings/sections, use accepted names or neutral source anchors; preserve source order. |
| Repetition | 75 similarity candidates; old exact merge correctly avoided unsafe semantic deletion. | Exported all candidates, initial text-level adjudication of 12, remainder pending. Zero similarity-based deletions. |
| Unsupported claims | Exact source matching validates location, not entailment or conditions. | Structured review statuses, exact review quotes/targets, unresolved-critical publication blocks. Most content remains NOT_REVIEWED. |
| Assembly loss / audit leakage | Format-specific displays omit some original fields; JSON preservation blocks clutter student output. | Keep every item/field in sidecars; display readable additional details, omit machine audit JSON from student view; verify rendered IDs. |

## Delivered changes
Optional educational review metadata supports nine instructional roles and sourced correction/explanation/alternative/prerequisite/continuation links. Review quotes and targets are validated; unspecified or invalid review never implies correctness. Formula status and code origin are separate from syntax/runtime/semantic correctness. Complete-formula annotations require available supporting literal expression; unreviewed formulas remain uncertain. Procedures do not default to correct demonstrations.

The canonical extraction prompt now explicitly preserves instructional errors and source-stated relations, prohibits incomplete complete-looking formulas and reconstructing literal code. No schema or grounding requirement was relaxed. These prompt changes produce new payload/configuration hashes and need fresh request records before later live use; historical manifests and provider accounting were not edited.

## Exact implementation files
app/models/educational_review.py; app/models/knowledge.py; app/representation/models.py; app/representation/selector.py; app/assembly/models.py; app/assembly/assembler.py; app/rendering/renderer.py; app/evaluation/educational_safeguards.py; app/evaluation/notes_pipeline.py; app/extraction/canonical_grounding.py; rebuild_educational_preview.py; tests/test_educational_safeguards.py.
Unset knowledge review fields preserve the original serialized shape, including the 473-item historical baseline.

## Corrected reference preview
Authoritative Task 5 offline output: delivery_preview/notes.md. All 376 original items remain in reviewed_knowledge.json and the audit report. 48 topic/source sections replace one Main Content section; 10 are neutral source labels, so these are not 48 verified textbook chapters. All 376 IDs render. Internal JSON blocks in student view: zero. The preview is longer (about 14,955 vs 11,602 words) because exact source passages replace unsupported code reconstruction. Organization is safer, but substantial editorial work remains.

There are 376 item-content review records, not an atomic-field audit: 371 NOT_REVIEWED, one SUPPORTED, two PARTIALLY_SUPPORTED, one CONTRADICTED (original flawed procedure, now labeled), one INCONCLUSIVE. These are assistant source-comparison annotations, not independent human certification. 33 automated flags and four supplied review concerns are reported separately. Zero UNSUPPORTED-status records does not establish zero unsupported claims.

Readiness: NEEDS_MORE_CORRECTION. Extraction completion NOT_EVALUATED for this offline rebuild; structure PASS; semantic faithfulness FAIL due unresolved critical concerns; completeness/usability NEEDS_REVIEW. Educational topic coverage remains unmeasured without a reviewed topic inventory. New overall/category scores remain null; the previous provisional 50/100 is not automatically raised.

## Deduplication and coverage
All 75 actual pairs are exported with both texts/provenance and classifications in duplicate_review.json. Initial review identifies distinct concepts and one possible equivalent final-variable definition; no uncertain merge was applied. All 376 items, 42 examples and 14 procedures remain in the audit, even when unsafe literal display is replaced by source explanation. Source-ID representation is not proof of complete teaching coverage. New tests flag missing topic inventory entries and deliberately lost rendered IDs.

## Targeted re-extraction
Four bounded draft requests covering source T0022/T0023 and T0041/T0042 are proposed in targeted_reextraction_proposal.json. They are NOT authorized or dispatched by Task 5. Existing FizzBuzz corrections were available offline, so no API call is needed just to label them. Recovering the full mortgage expression requires the original visual source before any justified model request; external textbook knowledge must not fill the gap.

## Tests and limitations
Cross-domain tests cover mathematical mistakes, science misconceptions, revised historical claims, rejected research hypotheses, troubleshooting, literal Python/JavaScript/C-like snippets, source fidelity negatives, formula statuses, chapter order, unknown corrections, missing topics, invalid review evidence and lost rendering. Fixtures test engineering behavior, not real OCR/PDF quality or live-model improvement. An historical-preview regression verifies retained item count, error→explanation→correction ordering, visual-formula warning, blocked reconstructed literal, and no audit JSON. General entailment, exhaustive duplicate adjudication, long-range context and independent quality review remain unresolved.

Initial broad suite: 707 passed, one compatibility failure; after preserving legacy serialization, 708 passed. Later presentation checks: 112 passed after correcting a Markdown-escaping assertion. The delivery suite was interrupted by the session transition before a final XML was saved; a fresh verification run is recorded separately on November 9. This Task 5 report documents offline work only; the subsequent user-authorized live rerun has its own directory.
