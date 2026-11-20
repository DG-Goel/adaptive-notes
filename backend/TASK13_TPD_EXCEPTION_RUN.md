# Operator-authorized TPD-only run

The operator explicitly requested the full extraction with the daily quota bypassed and the remaining three limits retained. This means local TPD only; RPM, RPD and TPM remain at the current 85% ceilings (25, 850 and 6800). Provider-side limits remain authoritative.

`run_full_tpd_exception.py` resumes `data/output/multimodal_notes_category_full_20261110_135722_142723`. Its context-local exception applies to the scheduler, runner preflight and shared Stage A numeric quota comparisons. It does not change configuration fingerprints, credentials, request payloads, exact-source approvals, evidence validation or accounting. Default limits are restored when the context exits. The ordinary full-run command does not enable this exception.

Each newly claimed request records `operator_quota_exception` in the scheduler audit, including the exact operator instruction and run binding. A separate `tpd_exception_*.json` records the invocation. Existing charges and unknown-usage reservations remain intact. No automatic redispatch or provider-429 bypass is authorized.

Live log: `data/output/full_tpd_exception_live.log`. Parent `run_summary.json` and `execution_report.md` identify whether work is complete, partial or blocked. Successful HTTP responses can still fail mechanical evidence validation and remain unresolved.

Validation: 15 focused tests passed across `test_tpd_exception.py`, `test_quota_policy_current.py` and `test_category_orchestrator.py`. These check TPD-only scope, retained configured ceilings, restoration after exceptions, thread isolation, and stop behavior for provider 429 and incomplete primary work.

An additional 19 tests passed in `test_local_quota_accounting.py` and `test_stage_a_local_quota.py` (34 passing tests total). Tests use isolated temporary ledgers and do not alter the live accounting state.
