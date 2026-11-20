# Guarded live Stage A harness

**Stage A HOLD · Stage B HOLD · Release NO-GO**

## Request and control path

[request_plan.json](request_plan.json) contains the complete exact request and the unchanged budget calculation. The CLI pins POST https://api.groq.com/openai/v1/chat/completions, Groq openai/gpt-oss-120b, temperature 0, JSON object mode, non-streaming on-demand service, and max_completion_tokens=4000. Groq documents max_completion_tokens as the supported completion limit. The reviewed system and user strings are checked against a pinned hash and the complete frozen T0022 source. The computed input estimate is 1,007 tokens and allocation is 5,007 tokens. [Groq API reference](https://console.groq.com/docs/api-reference)

A synchronous HTTPX client sends one POST using the explicitly selected GROQ_STAGE_A_API_KEY. There is no SDK retry layer, transport retries are zero, redirects are disabled and environment proxy settings are ignored. The request consumes a shared quota claim and a per-run stage claim before dispatch. HTTP failures including 401, 403 and 429 stop the run. A timeout or transport failure records uncertainty and keeps the claim consumed. Abrupt termination can leave a pending reservation and still prevents redispatch.

Raw response and diagnostics are preserved in the run directory. The existing strict Stage A validator checks JSON shape, finish reason, fact IDs, source membership and contiguous quotes. Duplicate JSON keys and non-JSON constants are refused before that validator. Exclusive writes and the saved SHA-256 bind the checkpoint. Success returns awaiting manual review and zero publishable items. Semantic support and the required teaching-point coverage are human review obligations. The harness contains no Stage B invocation or publication route.

## Admission and limitations

Use [admission.schema.json](admission.schema.json) for a real, operator-signed-off JSON record. PASS and an authorization reference are required. Bind the selected credential by inventory ID and SHA-256 in the protected admission record. Credential material and the credential hash are excluded from run artifacts. The operator must establish the credential's organization and project from authoritative account evidence.

The gate requires organization RPM, RPD, TPM and TPD rows with explicit current usage and outstanding commitments. Include stricter project ceilings and any configured split input/output limits. The operator attests that all applicable limits and usage have been accounted for. Missing daily usage blocks admission. The configured Free Tier ceilings are 30 RPM, 1,000 RPD, 8,000 TPM and 200,000 TPD. Lower supplied ceilings take precedence. The default token margin of 0.85 yields 6,800 TPM and 170,000 TPD admission ceilings. Operators may reduce the margin. Request-count ceilings use the full configured limits.

The transaction checks external usage, outstanding commitments and local reservations plus the proposed request before inserting the claim. It uses the same quota.sqlite for all runs in this harness. Confirmed attempts are charged at least their full allocation until the local rolling minute/day windows expire. Unresolved claims remain charged indefinitely. External counters and local claims can overlap. The calculation deliberately double-counts possible overlap to remain conservative. The ledger covers only this harness's claims. Other experiment and organization traffic must be included in external evidence.

The gate requires fresh data at most 15 seconds old and at least 90 seconds remaining on the traffic-control attestation immediately before dispatch. The operator must maintain control through completion or reconciliation. An HTTPX timeout is an inactivity limit and does not prove that server execution ended. Any missing or unbounded traffic, incomplete account evidence, or uncertain headroom means HOLD. Operator attestations are trusted input and do not independently authenticate provider quota or reserve organization capacity. Protect the shared ledger from replacement or cloning.

## Future command

Only after separate Stage A authorization and current quota review, run from C:/Projects/adaptive-notes/backend with the selected credential securely supplied in GROQ_STAGE_A_API_KEY and the verified admission record at C:/Projects/adaptive-notes/backend/data/output/t0022_live_stage_a_harness_20261104_074428/admission.json:

```powershell
.\.venv\Scripts\python.exe -B data/output/t0022_live_stage_a_harness_20261104_074428/live_stage_a.py --execute-live --admission data/output/t0022_live_stage_a_harness_20261104_074428/admission.json
```

The admission record is deliberately absent until an operator supplies actual evidence. The request hash to bind is in request_plan.json. The CLI also supports --show-request for offline inspection.

## Validation and files

New files are admission.py, live_stage_a.py, test_live_stage_a.py, request_plan.json, admission.schema.json, preservation_validation.json and this report. Existing code and artifacts were only read. All 574 saved protected hashes matched.

An initial test invocation stopped during collection because the test imported the shared control module before the harness added its module path. The import order was corrected. The focused suite then passed 28 tests in 4.68 seconds. The final combined run passed **68 tests in 10.74 seconds**:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_live_stage_a_harness_20261104_074428/regression_work data/output/t0022_live_stage_a_harness_20261104_074428/test_live_stage_a.py data/output/t0022_safety_infrastructure_20261104_003405/test_control.py data/output/t0022_offline_prototype_20261103_225328/test_prototype.py
```

HTTP tests injected MockTransport and blocked the real transport constructor. Subprocess tests exercised SQLite claim contention only. No live request or actual Stage A experiment ran.
