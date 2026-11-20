# Task 9 — Review-desk validation and independent semantic-review pilot

The review desk was exercised in a permitted browser over an approved, read-only host-loopback server. Two necessary software issues were corrected: reviewer navigation/warning presentation, and replay of old decisions after withdrawal. The 30-bundle pilot is prepared and **AWAITING INDEPENDENT HUMAN REVIEW**, following the user's explicit preference. No actual pilot judgment was fabricated, no educational content was rewritten, and the full document remains NOT VERIFIED.

## Browser findings and targeted corrections

The original mortgage packet exposed approximately 17,500 characters of repeated scope/citation JSON. Its decision controls were approximately 6,542 pixels below the viewport, and the visual-context limitation appeared inside metadata rather than as a prominent warning. The revised desk shows deduplicated exact quotations as source cards, retains original records in expandable metadata, provides direct item/source and previous/next navigation, and links directly to review controls. At the measured 720-pixel viewport, the save control was visible at y=479.5–518.7 after using that link. Unsent form entries survive switching between bundles in the current tab.

Prominent warnings now distinguish incomplete formulas, reconstructed literal code, adverse dispositions, missing evidence and partial/inconclusive support. The 30-bundle header explicitly says awaiting human review. Source cards preserve primary versus contextual identity; neighbor context remains explicitly unauthorized for new evidence use. Search covers quotations as well as claims and IDs, and filters correctly handle zero results. A selected packet outside the current filter remains clearly identified rather than silently changing the decision target.

Actual browser checks passed for search, quote search, status/priority filters, empty results, item/source navigation, neighbor context, error/correction warnings, unsent form retention, and local draft/export controls. Missing identity and affirmative review without valid evidence were rejected in synthetic fixtures. A deliberately contradictory synthetic fixture displayed its warning. No real pilot decision was entered. Browser console checks reported no page errors on the pilot desk. Evidence is in browser_checks.json, baseline_browser.png and review_desk_validated.png.

The original sandboxed listener was unreachable because socket access was restricted. The explicitly authorized local test-server workflow was run on host loopback with approval, serving only named review HTML pages on 127.0.0.1, with no directory listing, POST or credential/source-tree access. No browser warning, local-file URL policy or security barrier was bypassed. The test listener was stopped after testing.

One automation download-wait call returned after 910.0029 seconds. The exported file was successfully retrieved and validated, but this observation is not a reliable browser-download performance measurement and is not human review time. Two selector/key automation attempts required different supported page actions; they did not create judgments. Testing was limited to the available in-app desktop browser; cross-browser/mobile and independent-person usability have not been established.

## Exact accounting

| Measure | Reconciled result |
| --- | ---: |
| Original knowledge items | 458 |
| Task 7 recovered source-supported items | 11 |
| Additional Task 8 item | 1 — PRC_5001 |
| Total Task 8 items preserved | 470 |
| Substantive field records | 1,265 |
| Exact-evidence bundles | 849 |
| NOT_REVIEWED field records | 1,066 |
| Existing SUPPORTED field dispositions | 102 |
| Reviewed subset item IDs | 46 |
| Distinct displayed reviewed fields | 62 |
| Item schemas with all substantive field dispositions SUPPORTED | 24 |
| Atomic factual claims | Not established |

PRC_5001 is the source-backed do-while construction procedure recovered offline in Task 8 from T0045. Its six fields and provenance are recorded in Task 8 changes.json and review_input_knowledge.json. It was not a new successful API request. The 46 displayed item IDs include partially retained items and the equivalence cross-reference; they are not 46 fully reviewed item schemas. Even the 24 all-supported schemas carry existing source-comparison dispositions, not independent whole-document certification. accounting.json recomputes these counts from actual rows/mappings.

## Thirty-bundle selection and evidence packets

The manifest records the seed, canonical source version, baseline workspace hash, population of 849 bundles, member fields and every selection rationale. Selection starts with predeclared difficult/critical categories, adds one hash-ranked unreviewed draw per available knowledge category, then fills with hash-ranked unreviewed bundles to exactly 30 unique bundles / 47 fields. This is a purposeful review pilot, not a representative population accuracy estimator.

The sample includes known nonliteral code and embedded procedure fragments; the incomplete mortgage equation; source-factual uncertainty and overgeneralization; deliberately incorrect demonstrations and their explanations/corrections; contrasting mathematical expressions; conditions/qualifications; multi-source associations; recovered points/procedures; definitions, explanations, numeric claims and lower-priority material. All available named critical categories are represented, but 30 bundles cannot cover every known problematic instance. The complete remaining-disposition inventory remains separate.

pilot_desk.html, pilot_review_packets.md and pilot_evidence_packets.json expose exact claims, field membership, canonical quotes, bounded neighboring context, instructional relationships, warnings and existing mechanical/current review results. Existing assistant dispositions are visible as history and are not counted as independent pilot decisions. The selection and source versions are fixed before human review. pilot_decision_template.json contains placeholders only, and independent_pilot_decisions.json is empty.

## Import/export, history and stale-version validation

An actual browser download from the synthetic test desk contained one assistant-labelled INCONCLUSIVE transport record. It was imported into a synthetic-only directory using the normal CLI. Re-import retained one record. Seven invalid files were rejected before output creation: stale source, unknown status, missing identity, missing rationale, incomplete membership, a non-list payload and malformed JSON. Changing the synthetic source invalidated its recorded decision without rewriting the history. These are software transport tests, not real-document semantic findings.

A regression first reproduced a safety defect: after a withdrawal, re-importing the old approval appended it again and restored the old state. The fix makes the same review input idempotent, normalizing packet-member order and equivalent timestamp timezones for replay comparison. Earlier hashed history is preserved, a withdrawal stays effective, and genuinely new rationale/time follow-ups still append. This prevents accidental approval resurrection and duplicate review-count inflation. It does not authenticate a self-declared reviewer or automatically establish that a person reviewed a claim.

## Actual review results and efficiency

Completed independent bundles: **0**. Completed independent fields: **0**. Human pilot judgments: **0**. Actual supported/partial/unsupported/contradicted/inconclusive pilot decision counts are all zero. Confirmed critical educational defects from this independent pilot and time per human-reviewed bundle are unassigned because the pilot has not been conducted. Atomic claim counts remain unknown. The existing unreviewed backlog remains 1,066 fields.

There was one synthetic browser export/import, zero unexpected synthetic import errors, seven expected invalid-file rejections, and one synthetic source-version invalidation. The replay fix is a confirmed workflow defect repair; it is not a new confirmed educational-content correction. Existing Task 8 invalidations and historical assistant judgments are not recounted as Task 9 human reviews. review_efficiency.json separates all of these measures and leaves every semantic accuracy/quality score unassigned.

## Remaining defects and notes comparison

The existing 80 adverse literal-fidelity field records (40 reconstructed snippets), 12 partially supported fields and five inconclusive fields remain in remaining_critical_inventory.json with source evidence and scope. These are existing dispositions, not new independent judgments. The incomplete original mortgage visual, source-factual checks, qualification/evidence gaps and comprehensive educational-topic review remain outstanding. High risk is not proof of a defect, and a matching quote is not proof of factual truth.

No new semantic judgment justifies a Task 9 study-notes rewrite. Task 8 reviewed_study_notes_v8.md and comprehensive_review_draft_v8.md remain byte-for-byte unchanged, separate and explicitly limited. Educational retention, known corrections, topics, warnings, repetition, chapter organization, formula/code fidelity and readability therefore have no new content change to claim. notes_comparison.json records their paths and hashes. The interface improvement must not be reported as increased educational accuracy.

## Regression results, preservation and readiness

The final applicable offline suite passed **934 tests**, with 0 failures, 0 errors and 0 skips. The final overlapping review-targeted suite passed **55 tests**, with no failures/errors/skips. Do not add overlapping totals. The first replay regression failed before the fix; it now passes. An older synthetic test was adjusted to distinguish a genuine follow-up rationale from an identical replay. The broad suite retains strict source/evidence, authorization, quota, renderer and recovery regressions. Real-provider tests and the Windows-disabled Docling suites were explicitly excluded. The launcher denies network connections and removes API-key environment entries.

1267 historical/control files were verified unchanged, including all Task 8 artifacts and original evidence/history. No Groq/provider call, live extraction, authorization change or quota-accounting change was made. Production changes are confined to the review HTML/template renderer and the small replay-safety fix; no Java-specific production rule or new review framework was introduced.

**Next readiness: REVIEW DESK VALIDATED; INDEPENDENT PILOT AWAITING HUMAN REVIEW.** The next step is for the designated human to perform the 30-bundle review and export genuine decisions for version validation. Only those actual decisions can justify source-backed corrections and a separate notes preview. Full-document semantic, topic-completeness and usability release criteria remain unmet. No overall score is assigned.

human_review_handoff.md contains the local server, review and import steps. The package also includes the selection manifest, searchable desk, full packets, accounting, empty actual pilot ledger, synthetic transport evidence, remaining critical inventory, efficiency/notes comparison, regression logs/XML, screenshots and preservation checks.
