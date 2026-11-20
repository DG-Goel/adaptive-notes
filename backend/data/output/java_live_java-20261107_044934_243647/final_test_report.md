# Actual full-scale attempt — November 7, 2026

## Outcome
Partial live execution. Across two newly authorized configurations, 8 real requests reached Groq, all returned HTTP 200, zero HTTP 429, zero automatic retries. The first configuration failed on its first chunk because common content differed from the category text. Its exact response and usage remain at ../java_live_java-20261107_044142_852892/.

An explicitly announced canonical wire correction removes duplicated main text from five response categories and projects the application's required content from the evidenced main field. It does not drop application-required fields or accept mismatched historical output. Offline tests passed before fresh exact-request authorizations and the second run.

The second run accepted 6 of 47 initial chunks and generated a 34-item unverified partial preview. Request java-20261107_044934_243647-0042 (chunk 7) returned a procedure step with refs=[]; strict validation rejected it. No full-document completion or quality pass is claimed. All source material after the failure remains pending. Six source IDs having accepted items does not prove complete coverage of those units or the transcript.

## API accounting
Combined actual input: 22,948 tokens; output: 5,937; total: 28,885. Combined measured runner duration: approximately 384.984 seconds, including quota waits. Usage is provider-reported for all eight attempts. Existing historical usage remains charged separately. The runner waited within the 85% total ceilings on NOTES 1 only; it did not require external available-capacity verification or rotate organizations.

## Corrections and tests
- Added canonical_grounding.py and the canonical_grounded_v4 policy to preserve one canonical evidenced text per claim. Updated planner, extraction adapter and saved-response validation for that policy.
- Updated the authorization preparer to explicitly bind the current canonical policy, same model, low reasoning and full 3,000-token output reserve.
- After chunk 7 failed, strengthened the API schema with minItems=1 on references and minLength=1 on text, matching existing strict local requirements. The saved failure is still rejected. This latest schema change has not yet been verified against Groq and invalidates the previous request manifest; no identical failed-request retry was issued.
- Added projection/empty-reference tests and canonical mocked runner/resume coverage. Single-request preparation tests use a fresh in-memory configuration fingerprint without rewriting historical preparation artifacts.
- Final affected suite: 317 passed, zero failed/skipped (54.65 seconds), plus the pre-run 180 and 112-test checks. No claim of disjoint total test counts.

## Why the full extraction did not finish
The real model still generated unsupported procedure structure and imperfect source associations. API success and structured JSON do not establish grounded knowledge. The validation failure plus semantic issues in accepted previews prevent a full quality claim. Schema nonempty-reference constraints address one known structural failure, but do not establish that a supplied reference truly supports a claim. Repeatedly submitting fresh full plans would re-spend successful work without resolving semantic support. The accepted six checkpoints and all raw evidence are retained for source-bound continuation planning; no unsafe checkpoint transfer or fabricated successful operation was created.

## Educational review
See quality_evaluation.json for explicit subset findings. The first JDK fact cites a truncated excerpt that stops before the complete name. The System definition adds explanatory material absent from its primary source segment and needs context-level verification. Installation facts retain transcript filler. Broad every-program/every-statement/always-static statements need scope and technical review. No claim-count total or weighted educational score is invented from this partial assistant review. Complete-document coverage, cross-topic continuity and examples cannot be assessed yet. General semantic grounding, paraphrase consolidation and polished structure remain unresolved; these were not fixed merely by making JSON conform.

## Deliverables
partial_notes.md: actual real-model preview, clearly marked UNVERIFIED.
extraction_results.json: accepted raw knowledge before downstream conservative consolidation.
consolidated_notes.json / consolidated_render_manifest.json: audited downstream preview mapping.
source_coverage.json and evidence_coverage.json: source and excerpt diagnostics.
notes_quality_gates.json: five independent gates; incomplete extraction cannot pass.
request_audit.json, quota_report.json, errors.json: actual operations, usage and failure.
combined_attempt_summary.json: both attempts summarized without hiding the first failure.
quality_evaluation.json: partial evidence/quality review, score null.
../full_extraction_corrections.xml: final regression results.

## Remaining work
A new plan is required for the strengthened schema. Continue only with genuine source-bound prior-work accounting and full semantic review, retaining strict rejection for unsupported content. Complete extraction and quality validation have not been achieved. The operator's existing approval and total-quota policy remain valid; external quota visibility and credential expiry are not blockers.
