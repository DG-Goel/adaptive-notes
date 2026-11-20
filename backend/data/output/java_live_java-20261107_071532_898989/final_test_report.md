# Five-friend rotation: implementation and actual live evaluation

## Result
Five-key live rotation is implemented and exercised with all five friend-owned organizations. All 48 initial primary chunks were attempted exactly once. 46 chunks were accepted, producing 385 knowledge items and an unverified notes preview. This is PARTIAL LIVE EXECUTION for accepted extraction, not a full extraction/quality pass.

Physical request assignment followed the approved 1,2,3,4,5 sequence. Slots 1–5 handled 10,10,10,9,9 requests respectively. Credentials were not switched to retry rejected, rate-limited or uncertain requests. Every physical dispatch used a credential-specific Stage A record, exact payload hash, canonical source binding, and the existing separate organization/shared quota ledgers. The default single-slot path and frozen gates remain supported.

## API and token accounting
48 real requests: HTTP 200 = 47, HTTP 400 = 1, HTTP 429 = 0. Automatic retries = 0. Reported input tokens = 143,857; reported output = 40,179; reported subtotal = 184,036. The 400 response supplied no usage, so total actual token consumption is UNKNOWN, not 184,036 exactly. Its conservative reservation remains charged. No quota history was cleared. The aggregate across five organizations is not treated as a single organization's allowance; each organization retains its own RPM25/RPD850/TPM6800/TPD170000 ceilings.

First durable claim to last completion: 878.674 seconds, including resume gaps, review/testing and quota waits. Sum of measured physical-call durations: 115.031 seconds. run_summary.json now distinguishes this total span from the last invocation's 5.281 seconds, avoiding the earlier misleading reset-on-resume duration.

## Rejections and recovery
1. Chunk 1 / ...-0000 / NOTES 1: model cited Q0006–Q0008 and simultaneously excluded them. Strict contradiction rejection remains. Original response is unchanged; no false successful checkpoint was created.
2. Chunk 18 / ...-0119 / NOTES 3: a character-count truncation heuristic rejected valid JSON containing escaped quotes. The guard now parses valid JSON before applying truncation heuristics. The saved receipt-hash-bound response passed strict offline revalidation and recovered WITHOUT a second API request. Original rejection and recovery events remain in the audit.
3. Chunk 47 / ...-0322 / NOTES 2: HTTP400 json_validate_failed; Groq reported missing required formulas in generated output. No accepted replacement was invented. Usage is unknown and conservatively charged. The failed request was not resent.

An explicit --continue-validation-failures evaluation option can proceed to a different, preauthorized primary request after a definitive HTTP200 validation rejection or HTTP400 json_validate_failed rejection. It cannot retry the failed request, and does not apply to 429, uncertain network outcomes, credential failures or admission HOLDs. Approved truncation recovery, when applicable, stays with the parent organization. Rejected work remains incomplete in the quality gates.

## Notes and coverage
partial_notes.md is the real-model preview, explicitly UNVERIFIED. There are 385 items before and after conservative consolidation. Representation distribution: standard_text255, definition_box82, example_callout39, formula_display2, flowchart7. Primary coverage has accepted items for 48 of 50 source IDs; T0001 and T0049 have no accepted knowledge. Having an item does not prove complete coverage of each source's teaching. No full topic coverage, semantic correctness or overall weighted score is inferred from these counts.

Five gates: extraction completion FAIL; structural validity PASS; semantic faithfulness NEEDS_REVIEW; educational completeness NEEDS_REVIEW; notes usability NEEDS_REVIEW. This task demonstrates working live rotation and broad processing, not a certificate of educational quality. Source-level omissions, qualification preservation, possible paraphrase/conflict pairs and factual support still require review. Semantic claims remain unverified.

## Tests and preservation
Final release suite: 394 passed, 0 failed/skipped. Covers real SDK with mocked HTTP, 1→5 rotation, saved-response recovery, strict schemas, organization quota isolation, legacy authorization, frozen Stage A/control files, 429/timeout stops, and independent continuation without cross-key retry. A development fixture initially returned HTTP200 for the intended HTTP400 test; corrected to exercise the real 400 branch and focused tests then passed. Additional resume-duration invariants are tested separately.

Original java.txt SHA-256 remains 54a017edc6b3465c37a6faf051a63dedd81437728df6b99276e998aedb127598. All baseline frozen Python hashes remain unchanged. No credentials or approval expiry dates were changed. No external available-capacity verification requirement was reintroduced. The five-friend ownership statement remains recorded in QUOTA_POLICY.md.

## Exact files changed
- app/extraction/stage_a_bridge.py: extensible registry guard, legacy single-organization behavior preserved.
- app/extraction/document_authorization.py: deterministic primary-slot assignments and same-slot recovery; explicit five-slot document gate.
- run_authorized_java.py: per-request identity selection, assignment validation on resume, safe independent continuation, accurate elapsed accounting.
- prepare_java_authorization.py: --rotate-five and credential-specific request/approval records.
- app/extraction/llm_provider.py: valid JSON is not rejected through quote/brace counting.
- tests/test_authorized_runner.py: five-key SDK rotation, resume, failure isolation/continuation and timing checks.
- tests/test_json_truncation_strings.py: quoted strings/code regression.
- QUOTA_POLICY.md and AUTHORIZED_JAVA_RUN.md: operating policy and commands.

## Artifacts and usage
Authorization directory: ../java_authorization_20261107_071532_898989/ (source-bound record for every request and recovery).
Actual run: this directory. Files include run_summary.json, request_audit.json, raw *.response.json, accepted chunk checkpoints, rotation_evaluation.json, errors.json, quota_report.json, extraction_results.json, partial_notes.md, consolidated_notes.json, consolidated_render_manifest.json, source_coverage.json, evidence_coverage.json and notes_quality_gates.json.
Release tests: ../five_rotation_release.xml.

For a new run, prepare_java_authorization.py --rotate-five creates fresh identities and exact request bindings. run_authorized_java.py --authorization-dir <directory> --live --continue-validation-failures enables the explicit full-document evaluation behavior. Reusing the existing authorization resumes without resending accepted or rejected operations; it does not repair the two rejected chunks. Repairing those gaps requires separately audited, source-bound work; do not erase failure history or silently accept contradictory evidence.
