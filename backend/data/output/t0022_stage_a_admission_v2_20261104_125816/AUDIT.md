# Stage A admission remediation audit

**Stage A HOLD. Stage B HOLD. Release NO-GO.**

The revised harness lives in this directory. Earlier harnesses, audit files, source files and prototypes were preserved. The saved request plan is byte-identical to the previous plan. The rebuilt payload and canonical request hash match it, including the 4,000-token cap and 5,007-token allocation. All 574 hashes in the historical preservation baseline matched.

## Closed checks

| Gap | Revised enforcement |
|---|---|
| Limit applicability and completeness | Admission requires a nonblank authoritative inventory reference, a complete-limit attestation, explicit organization/project, explicit project applicability, and explicit split metric lists for each scope. Four organization metrics are always required. A project declaration of applicable limits requires all four project metrics. Every declared split metric is required. The exact expected scope/metric set must appear once in both the limit inventory and usage windows. No project records are inferred from omissions. |
| Contradictions and headroom | Every usage ceiling must equal its inventory ceiling. Duplicate inventory, usage or split declarations, unexpected rows, missing daily rows and project ceilings above a matching organization ceiling fail. The existing transaction still charges external usage, outstanding commitments and SQLite reservations against all applicable windows. It uses the shared state location from the earlier live harness so changing versions does not clear consumed reservations. |
| Per-row evidence | Every quota row requires nonblank evidence and its own finite data_as_of timestamp. At claim time and immediately before dispatch, every row must be within 15 seconds, neither future-dated nor newer than the operator verification. Shared freshness and traffic-control checks still apply. |
| Ownership and authorization binding | The revised CLI requires a separately maintained credential_approval.json at its fixed configuration path. A trusted custodian must record the reviewed Console inventory or provider record, ownership evidence, verifier, validity window, credential inventory ID and SHA-256, organization and project. The same record binds the operator, explicit authorization evidence, stage, run and exact request digest. The gate matches these fields and checks the selected secret hash before claiming and again before dispatch. |

Credential ownership and authorization are **operator attestations backed by evidence references**. The implementation performs exact binding and expiry checks. It has no provider-side identity lookup, signature verification, or authenticated evidence fetch. A secret hash proves equality with the reviewed inventory fingerprint. Only the custodian's verification of the underlying provider records establishes ownership. Protect the approval file separately from admission input and keep the custodian-controlled directory and shared SQLite ledger protected from unauthorized writes. The artifact writer excludes credential hashes and rejects admission metadata containing the selected secret. The secret itself is supplied only in memory by the environment.

The operator must independently confirm whether project limits and split limits apply. Explicit false or empty declarations represent reviewed applicability decisions, with a required inventory evidence reference. They are not auto-discovery. If applicability, provenance or headroom cannot be established, keep HOLD. The previous harness is preserved for historical review. Any future authorization must name this revised entry point.

## Files added

- admission.py and live_stage_a.py, revised harness modules
- admission.schema.json and credential_approval.schema.json, schema exports only
- request_plan.json, unchanged frozen request copy
- test_live_stage_a.py, retained regression assertions with updated fixture evidence
- test_admission_v2.py, 33 new completeness, freshness and identity/authorization cases
- AUDIT.md, this report

No real admission or credential approval record was created. Test workspaces contain simulated fixtures only.

## Exact regression commands and results

From C:/Projects/adaptive-notes/backend:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_stage_a_admission_v2_20261104_125816/regression_work data/output/t0022_stage_a_admission_v2_20261104_125816/test_live_stage_a.py data/output/t0022_stage_a_admission_v2_20261104_125816/test_admission_v2.py data/output/t0022_safety_infrastructure_20261104_003405/test_control.py data/output/t0022_offline_prototype_20261103_225328/test_prototype.py
```

**101 passed in 11.23 seconds.** The prior run had 100 passes and one failure because the new missing-daily diagnostic was too general for an existing assertion. The specific diagnostic was restored. Existing duplicate and cross-process claim tests passed, alongside the new checks. HTTP tests used MockTransport and blocked construction of the real transport.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_stage_a_admission_v2_20261104_125816/historical_audit_work data/output/t0022_quota_admission_audit_20261104_080000/test_admission_audit.py
```

**10 passed, 1 xfailed in 1.78 seconds.** The expected failure is on the preserved historical harness. The corresponding partial-project case passes as a rejection test on the revised harness.

## Readiness verdict

**Offline checks pass. Operational Stage A remains HOLD.** The revised gate is suitable for another readiness review once an authorized operator supplies verified identity, complete limits, fresh row-level usage, current headroom and controlled/accounted traffic, and a trusted custodian supplies the bound approval. Actual organization quota and competing traffic remain unverified. Stage B stays on HOLD and release stays NO-GO. No live request or quota consumption occurred.
