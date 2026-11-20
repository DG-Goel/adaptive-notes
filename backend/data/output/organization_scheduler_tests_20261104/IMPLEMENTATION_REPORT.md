# Five-organization scheduler implementation report

2026-11-04. Implementation only. Stage A HOLD. Stage B HOLD. Release NO-GO.

## Result and exact files

Five new source/test/documentation files were added. No existing implementation or test file was modified:

1. C:\Projects\adaptive-notes\backend\app\extraction\organization_scheduler.py
2. C:\Projects\adaptive-notes\backend\app\extraction\organization_extraction.py
3. C:\Projects\adaptive-notes\backend\app\extraction\ORGANIZATION_SCHEDULER.md
4. C:\Projects\adaptive-notes\backend\tests\test_organization_scheduler.py
5. C:\Projects\adaptive-notes\backend\tests\test_organization_extraction.py

This report, added_files.diff, preservation.json and synthetic pytest workspaces are new artifacts under this report directory. No real admission.json, credential_approval.json, environment edit, live request or production extraction was created/run. All mocked operations used synthetic credentials/evidence and isolated temporary SQLite databases.

## Architecture and behavior

The opt-in chunk adapter uses the existing Groq SDK, provider error classifier/response guard, exact extraction prompt, unchanged budget calculation and actual strict raw-contract/evidence parser. It is not imported by any existing runner or Stage A/B harness. One frozen configuration pins Groq openai/gpt-oss-120b, temperature 0, json_object, strict evidence, and no fallback for every organization. Extraction output allowances and the existing 85% per-request budget policy are unchanged.

Explicit five-slot configuration and custodian-reviewed organization/project identity replace assumptions about multiple API keys. Enabled credentials must match reviewed fingerprints. Duplicate organizations/slots/fingerprints fail. Keys stay in runtime memory and are excluded from SQLite, status and audit records. The documentation supplies placeholder environment variables and registration/repair instructions. No credential is automatically inferred to belong to an organization.

The new organization aggregate admission ceiling is 70% for requests and tokens. It operates separately from extraction budgeting and may refuse an unchanged allocation. Each organization has independently charged usage and reservations in a shared transactional SQLite database. All four organization windows, applicable project/split windows, complete inventories, fresh evidence, controlled/accounted traffic and request-specific authorization/configuration bindings are mandatory. Unknown, estimated or exhausted quota never dispatches. Evidence remains operator-attested, not provider-authenticated or cryptographically signed.

The cursor persists and advances only after successful strict extraction. One active operation globally makes success-ordered rotation deterministic under concurrency. Competing processes receive HOLD. Duplicate operation IDs, duplicate physical dispatch markers and duplicate reconciliation are refused. Crash claims have no automatic expiry. Uncertain attempts retain reservations indefinitely. Every retry is independently reserved on the same organization and requires fresh admission.

401 and 403 persistently block the organization pending explicit reviewed repair. 429 records cooldown and stops with retryable=False, preventing outer retry rotation. Permanent request/model errors stop. Transient errors have bounded same-organization retries; SDK and transport retries are disabled. Unknown failures stop. Malformed/truncated/empty output, wrong model and invalid strict evidence return no items and do not advance the cursor.

Audit tables capture selections, bindings, dispatch intent, each attempt's reservations and actual/reasoning usage, HTTP status, finish reason, timing, retries, sanitized provider diagnostics and final mechanical validation/extraction outcome. Status exposes five slots without keys and does not call stale evidence current availability. It can calculate a non-reserving next-candidate snapshot using fresh request-specific admissions.

## Tests

Commands ran from C:\Projects\adaptive-notes\backend using its .venv Python. No real API integration tests were invoked. New adapter tests use HTTPX MockTransport through the real SDK serializer, while an autouse fixture rejects construction of real HTTPTransport. SQLite tests include spawned processes.

Initial attempts found a test helper import error, then pytest temporary-directory setup failures. The import was fixed without weakening assertions. A project-local test parent directory was created, and later runs used new unique basetemp subdirectories. Initial runnable suite: 56 passed. Expanded new suite: 67 passed in 9.36 seconds. An intermediate broader regression run: 550 passed in 19.61 seconds.

Final command:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/organization_scheduler_tests_20261104/final tests/test_organization_scheduler.py tests/test_organization_extraction.py tests/test_extraction_grounding.py tests/test_extraction_unit.py tests/test_extraction_reliability.py tests/test_groq_provider.py tests/test_groq_scheduler.py tests/test_scheduler_rotation.py tests/test_rotation_evidence.py tests/test_token_budget.py tests/test_chunk_splitting.py tests/test_adaptive_splitting_advanced.py tests/test_truncation_handling.py tests/test_serialization.py tests/test_recovery_workflow.py tests/test_semantic_verifier.py tests/test_semantic_verifier_procedures.py tests/test_semantic_regression.py tests/test_structural_evaluator.py data/output/t0022_stage_a_admission_v2_20261104_125816/test_live_stage_a.py data/output/t0022_stage_a_admission_v2_20261104_125816/test_admission_v2.py data/output/t0022_safety_infrastructure_20261104_003405/test_control.py data/output/t0022_offline_prototype_20261103_225328/test_prototype.py
```

**593 passed in 30.62 seconds, zero failures.** This comprises the new tests and listed relevant regression suites, not every repository test. Optional live integration and unrelated ingestion tests were not run. Existing assertions were not changed.

Coverage includes five-slot round robin and restart, disabled/missing/duplicate credentials and identities, immutable configuration, independent accounting, all four 70% ceilings, unknown traffic, missing daily/project/split metrics, timestamps and whitespace evidence, reservation reconciliation, reasoning accounting, uncertain outcomes, duplicate claims/dispatches, process contention, repairs/stale workers, 400/401/403/429, bounded transient retries, no same-operation rotation/fallback, identical outgoing requests, strict field/source/quote failures, truncation and sanitized audit/logs. Existing grounding, accounting, splitting, provider, semantic, structural, recovery-workflow and both stage safety tests passed.

## Diff and preservation review

The workspace is not a Git repository, so a full added-file unified diff was generated against empty files and reviewed instead of claiming a Git diff. added_files.diff contains all five added files (1198 lines). Python files also parsed successfully with ast.parse. preservation.json records added-file hashes and comparison against the existing 574-file protected baseline: **574 matched, zero changed**. Historical Stage A/B implementation files were read/tested, never edited. No prompt, schema, accounting, retry logic in the legacy path, budget policy, semantic threshold, frozen request or .env file was changed.

## Remaining limitations and decisions

- This does not solve the unavailable Free Tier organization-wide telemetry problem. Without genuine fresh admission evidence, all organizations remain non-dispatchable.
- Ownership/authorization assertions require trusted custodian/operator controls; hashes prove equality, not provider ownership. The library is not a defense against an operator who can rewrite all code, evidence and databases.
- Scheduling is safe under concurrency by serializing active operations; it is not a parallel throughput implementation. A crash may block scheduling pending separately reviewed recovery. Uncertain reservations are deliberately not automatically released.
- The adapter is a per-chunk operation. Document orchestration/assembly, cross-chunk ID handling and Stage A/B integration are not installed or approved. Stable request IDs must be retained by callers across retries; manufacturing a new operation ID is not legitimate retry handling.
- Local rolling accounting is conservative and cannot represent unobserved traffic or establish Groq's exact limiter algorithm. Different organizations do not make unknown usage verified.
- Exact quotes, schema and passing tests do not establish semantic faithfulness. Semantic and structural evaluation remain downstream requirements. No items are published by this adapter.
- Legacy provider/key-pool behavior remains unchanged for compatibility. The new opt-in path supplies the stronger no-rotation/error guarantees; it must not be confused with automatic hardening of every old entry point.

Implementation is ready for offline review only. No live request, Stage A execution, Stage B authorization or release is implied.
