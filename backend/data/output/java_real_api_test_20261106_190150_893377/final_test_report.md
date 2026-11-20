# Full Java real API test report

Classification: **Blocked before live execution**.

Source SHA-256: `54a017edc6b3465c37a6faf051a63dedd81437728df6b99276e998aedb127598`. Recomputed using the complete original file. Current parser produced 50 source units and 18 chunks. Chunk source references preserve parser order with no missing or duplicate IDs. This does not prove educational coverage or parser semantic fidelity.

## API and extraction results

Real requests: 0. Successful: 0. Failed: 0. HTTP 429: 0. JSON failures: 0. Retries: 0. Actual input/output/total tokens: 0/0/0. Live execution duration: 0 seconds. Preparation and offline regression duration: 30.11 seconds. API latency is unavailable.

Extracted chunks: 0/18. Not dispatched: 18. Extracted source units: 0/50. Final assembly: not run. Missing/duplicated note content and factual correctness: unevaluated.

## Exact blockers

- All production Java request payloads differ from the exact payload accepted by frozen Stage A. The bridge refuses them before provider dispatch.
- No current verified quota admission for these request hashes was supplied. Unknown external usage cannot be assumed zero.
- All five inventory entries and .env slots are disabled; verified_at and expires_at are null, every quota_state is quota_unknown, and the expected frozen Stage A credential_approval.json is absent. Existing organization/project mappings were preserved.
- Multi-organization provider permission is unestablished. No multi-organization live rotation was attempted.

The Stage A bridge checks payload equality before provider creation. Zero Java requests match the frozen request. A matching credential or fresh quota alone cannot resolve that mismatch. No frozen file, model, production prompt, quota ceiling, credential mapping, or live ledger was modified. This audit imports the offline request planner only and creates no provider client. No legacy runner was used to bypass admission.

The scheduler currently returns HOLD to callers rather than providing a document background queue. No worker or automatic reset/retry was invented. A future live orchestrator must preserve pending work and revalidate genuine evidence before dispatch, and cannot release uncertain reservations just because a window elapsed.

## Notes quality

No real notes were generated. Category and overall scores are unavailable. No prior output or mock test content was reused as real-run notes. See quality_evaluation_plan.md for the weighted rubric and evidence needed. Quality improvements cannot be established without real output.

## Artifacts and regressions

source_manifest.json, source_document.json, chunks.json, request_plans.json, quota_report.json, run_summary.json, preservation_manifest.json, regression_results.json, quality_evaluation_plan.md and error_report.md are actual preparation results. Regression logs and offline_* directories are explicitly offline fixtures, not real API evidence. request_plans.json contains production prompts with source text but no credentials or authorization records. There is no request audit or generated-notes/coverage/quality-score artifact because no corresponding live results exist.

- pipeline_scheduler: exit 0; see pipeline_scheduler.log.
- frozen_stage_a: exit 0; see frozen_stage_a.log.
- frozen_stage_ab: exit 0; see frozen_stage_ab.log.