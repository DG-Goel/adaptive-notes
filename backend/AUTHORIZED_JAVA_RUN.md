# Five-friend rotation (explicit opt-in)

`prepare_java_authorization.py --rotate-five` creates a fresh exact-request plan
for the five operator-confirmed friend-owned organizations. Primary chunks rotate
1 → 2 → 3 → 4 → 5; approved truncation recovery stays on the parent's organization.
The runner verifies every assignment, credential fingerprint and request record.
Each organization retains its own 85% quota accounting in both existing ledgers.
Quota waits do not switch organizations. A 429, uncertain request or permanent
validation failure stops the run by default. The explicit
`--continue-validation-failures` evaluation option can leave a confirmed, nontruncated
HTTP 200 validation failure unresolved and attempt independent remaining chunks.
It never redispatches that failed request and never applies to 429, uncertain
outcomes, admission failures or uncertain outcomes; approved truncation recovery remains on its assigned organization. Missing accepted chunks keep the
overall run incomplete. Successful checkpoints resume without redispatch.
The default preparer remains single-slot. Frozen Stage A files are unchanged.

# Current extraction format (November 7)

New manifests explicitly select `grounded_fields_v2`, Groq strict `json_schema`,
`openai/gpt-oss-120b`, and `reasoning_effort=low`. The compact wire format attaches
excerpt references to each substantive field. Conversion preserves the application's
required knowledge fields and validates exact source quotations using the existing
strict validator. Unsupported optional fields are null only in the wire format and
are omitted during conversion. Unknown references or missing evidence still fail.

The token estimate includes the full response schema, system instructions and source.
The configured 3,000-token completion reserve is never reduced for these requests;
source-preserving splitting makes requests fit the unchanged 6,800-token ceiling.
The original java.txt currently produces 32 initial requests, with bounded contingent
splits. Explicitly excluded noneducational excerpts are audited; empty extraction
requires exclusions covering every excerpt. Exclusions are model classifications,
not independently verified judgments. Unaccounted excerpts are recorded for review.

Approval expiry remains null (until revoked), and all historical quota charges remain.
A changed policy requires a newly hash-bound authorization manifest. Existing frozen
Stage A/B artifacts are not edited. Strict schema conformance does not establish
semantic correctness or complete coverage; actual notes still require quality review.

Final combined regression suite: 436 tests passed, including frozen Stage A/control tests. Strict parsing no longer applies fuzzy quotation repair before validation. Excerpt-level coverage diagnostics expose excluded and unaccounted passages for quality review. The November 7 live verification was blocked before
execution by automatic approval review of transcript egress to Groq. No new live
success or completed notes are claimed for this format.

# Authorized Java runner

New authorization manifests use `reserve_preferred_v1`. They split before dispatch
until every request reserves the full configured completion allowance (3,000 tokens for grounded_fields_v2) within the
6,800-token combined budget. Large individual source units split at whitespace
boundaries with exact canonical source IDs and character spans; the planner verifies
that the initial requests reconstruct every source unit without gaps or overlap.
If no bounded, lossless split fits, preparation stops before spending tokens.

Manifests also approve up to two smaller recovery levels per initial request.
Recovery children execute only after a durable parent failure proves output
truncation: HTTP 400 `json_validate_failed` with the provider's completion-limit
diagnostic, or response finish reason `length`. Other HTTP 400 errors, evidence
failures, uncertain requests and quota HOLDs do not trigger splitting retries.
Parents remain charged and auditable. Children have distinct payload hashes and
request IDs and repeat all credential, source, quota and Stage A checks. Resume
reconstructs that branch from the ledger and skips successful checkpoints.

This prevents reduced-output-budget dispatch and bounds recovery; it cannot
guarantee that an LLM always returns complete or correct JSON. Smallest unsplittable
failures remain incomplete with an explicit explanation. The increased number of
requests still obeys minute/day ceilings and may require additional waiting.

`run_authorized_java.py --authorization-dir <directory>` performs offline manifest validation.
Add `--live` to run approved requests. The program selects NOTES 1 from the approved
manifest without changing the globally enabled slots. Quota accounting uses the
persistent scheduler and Stage A databases. Never delete these databases to retry.

The runner checks source/prompt/request hashes, loads the per-request credential
approvals, waits for rolling quota capacity, saves raw successful HTTP responses,
checkpoints validated chunks, normalizes knowledge IDs, renders complete or explicitly
partial notes, and runs deterministic semantic heuristics. A rerun skips successful
checkpoints; a successful operation with a missing checkpoint is reconstructed from its hash-bound raw response without redispatch. Failed or uncertain operations are never silently resent. Incomplete live execution returns a nonzero process exit.

The production splitter can be selected with `prepare_java_authorization.py --split-depth 1`.
It preserves source order and source-unit coverage and creates fresh exact-request
approvals. This is a changed request plan, not a retry of the same failed request.

Real results on November 6: two requests reached Groq through NOTES 1. The original
chunk exhausted JSON generation capacity (HTTP 400). The smaller chunk returned HTTP
200 but failed exact source-quote validation. The full document remains incomplete.
See `data/output/java_real_evaluation_20261106_152955/final_test_report.md`.

No model/prompt/schema relaxation was used to accept the rejected output. Further
quality remediation should use the saved response for offline reproduction first.
An earlier preparation report claiming that verified available quota and the fixed
T0022 payload are mandatory predates the new document authorization implementation.
