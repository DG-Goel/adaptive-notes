# Full-document Java test: actual outcome

## Classification
**Blocked before live execution.** Zero new Groq requests, zero retries, zero live tokens consumed by this attempt, no response, and no notes generated. This report does not reclassify earlier experiments as part of the new run.

## Source and current request plan
Original source: C:/Projects/adaptive-notes/java.txt, 130532 bytes.
SHA-256: 54a017edc6b3465c37a6faf051a63dedd81437728df6b99276e998aedb127598
Production parser: 50 source units. Base chunker: 18 chunks. Current context_grounded_v3 plan: 37 initial requests plus 222 contingent smaller requests. Contingent authorization does not mean dispatch. The increase from 32 historical requests reflects context-aware prompt/schema budgeting. No counts were hardcoded, no synthetic source substituted, and planner coverage checks preserved canonical source order and exact primary spans. Draft manifest is manifest.draft.json; it is not an executable approval.

Model is unchanged: openai/gpt-oss-120b on Groq. Current production v3 prompt, strict JSON schema, low reasoning effort, temperature zero, no automatic SDK retries, full 3,000-token completion reserve. The policy/configuration and every exact payload/hash are saved in the draft manifest. This is an explicit new plan, not a silent reuse of the historical v2 prompt or Task 4 synthetic request. NOTES 1 alone is selected; no cross-organization rotation is planned.

## Exact blocker and its source
Section 4 of the latest attached task requires the stricter of scheduler ceilings and verified available provider capacity, accounting for outstanding reservations and organization-wide external traffic, and explicitly prohibits assuming unknown external usage is zero. The saved NOTES 1 inventory has quota_state=quota_unknown. No fresh complete provider-usage/available-capacity or traffic-coordination record was supplied. Local ledger history cannot prove absence of external callers.

The user previously requested total-limit/local-ledger admission; the latest attachment explicitly imposes the additional available-capacity requirement. The current document runner creates LocalQuotaAdmission, which enforces local/shared accounting but does not attest external usage. Dispatch through that path would not satisfy this new requirement. No quota_verified state, zero external usage, or Stage A PASS was fabricated. Existing VerifiedAdmission infrastructure requires genuine complete, fresh usage/traffic evidence; no dummy attestation was supplied.

To unblock: establish current provider limits/usage and outstanding organization/project commitments (including applicable split metrics), plus evidence that other organization traffic is controlled or accounted for. Bind genuine evidence to the new request/configuration and retain runtime admission checks. The runner must consume that verified-capacity admission rather than assume the local-only path meets the new condition. A fresh valid Stage A decision and reviewed configuration migration must then bind this new manifest. Existing request approval is recorded; the file, 85% ceilings and identity mapping do not need reconfirmation. No credential expiry window was added.

## Readiness findings
Key fingerprint matches recorded NOTES 1 identity; existing non-expiring identity review is valid. Enabled status is preserved. No request was active at inspection. Current provider acceptance and live model permission were not retested. The maximum planned initial reservation is 6799 tokens, below or equal to 6,800; no output allowance was reduced. This is policy fit, not proof of available capacity.

## API and extraction results
Requests attempted 0; HTTP successes/failures/429s 0; JSON failures 0; input/output/total new tokens 0; measured live execution duration 0; retries 0. All 37 initial requests remain unprocessed, with 0 accepted chunks. Assembly was not run. Known historical usage and attempts are separately reported in quota_report.json, with unknown historical usage explicitly retained as unknown. No failure-recovery or uncertain-request state was cleared.

## Quality results
No current notes exist to assess. Overall weighted score and all six category scores remain null/NOT_EVALUATED. quality_scores.json records the requested weights: completeness 30%, accuracy 25%, explanation 15%, organization/readability 10%, examples/code 10%, traceability 10%. No heuristic or human-reviewed score was invented. No generated_notes, extraction_results or source-to-notes coverage artifact is produced without the corresponding results. Source/request planning evidence is available; it is not educational coverage.

Upon a real admitted run, preserve each raw response and usage/latency/error record; run strict schema, evidence and exclusion checks; retain primary/context roles; consolidate conservatively; assemble an unverified preview; evaluate all five gates separately; and review every important claim/topic, code demonstration, qualification, omission and duplicate against the source. Missing or unsupported material must not be filled with invented notes. Permanent failure keeps the run partial.

## Artifact locations
- run_summary.json: actual blocked classification and zero live counts
- source_manifest.json: original source hash, parser/chunker counts and configuration
- manifest.draft.json: complete proposed source-bound request inventory
- request_audit.json: empty live-request list, clearly separated draft count
- quota_report.json: read-only local inventory/usage findings, unknown external usage
- quality_evaluation.md and quality_scores.json: unassessed results/rubric
- error_report.md: prerequisite failure and impact
- regressions.xml: offline regression results

No implementation was changed for this attempt. Frozen Python files changed: []. Existing source and ledger snapshots are checked separately. No live expansion or separate Task 4 one-request approval is implied by these draft artifacts.

Final offline regressions: 670 passed, 0 failed, 0 skipped (38.18 seconds). Preservation checks: {"source_unchanged": true, "organization_ledger_unchanged": true, "tests_passed": 670, "tests_failed": 0, "tests_skipped": 0, "live_requests": 0}
