# Stage A quota admission completeness audit

**Stage A HOLD. Stage B HOLD. Release NO-GO.**

Reviewed admission.schema.json, admission.py, live_stage_a.py, request_plan.json, and test_live_stage_a.py in t0022_live_stage_a_harness_20261104_074428. The live harness and prompts were inspected without edits.

| Requirement | Finding |
|---|---|
| 1. Organization RPM/RPD/TPM/TPD | Enforced by QuotaLedger.claim before inserting the claim. Exported JSON Schema alone does not express metric completeness. |
| 2. Applicable project metrics | **Gap.** Project applicability has no dedicated field. The gate evaluates supplied project rows but accepts a project TPM row with the other three omitted. The strict expected-failure test reproduces this. |
| 3. Applicable split limits | **Gap.** ITPM/OTPM are supported and checked when supplied. An explicit applicability declaration and completeness check are absent. |
| 4. Duplicate scope/metric | Rejected by comparing the indexed windows count with the original array length. |
| 5. Empty or incomplete windows | Empty arrays and missing mandatory organization windows fail at admission. Missing required row fields fail schema validation. Missing applicable project or split rows are the gaps above. |
| 6. Daily usage | Both organization daily rows and each explicit used value are required. There is no zero default. Supplied project daily rows require used too. Omission of the entire applicable project row remains possible. |
| 7. Evidence, timestamp and scope per row | **Partial.** Each row has a scope enum and required evidence string, with organization and project identity inherited from the enclosing record. Whitespace-only evidence satisfies min_length. There is a shared data_as_of and verified_at, but no row timestamp, row-specific scope identifier or independent evidence verification. |
| 8. Stale evidence | Shared snapshot older than 15 seconds, future or out-of-order timestamps, and traffic control expiring in under 90 seconds fail. Claim and pre-dispatch both check freshness. An old underlying row can be masked by a newer shared timestamp. |
| 9. Lower applicable ceilings | Enforced for supplied rows. The gate applies the lower documented Free Tier ceiling and supplied limit for the four base metrics, and checks all supplied project and split windows independently. Token windows also receive the configured safety margin. Omitted stricter limits escape checks. |
| 10. Outstanding and competing traffic | Explicit used and outstanding values are mandatory. Admission sums both, active SQLite reservations, and planned usage. Unknown/uncontrolled traffic strings and false inventory attestations fail. Operator assertions of controlled/accounted traffic and complete usage are trusted. The program cannot detect outside traffic or verify that an asserted zero is correct. |
| 11. Frozen request hash | execute() compares the record hash against the canonical payload produced by request_plan(). The plan pins the messages, source and cap. The exported request_plan.json is an inspection artifact, so the runtime does not load or verify that file. The current artifact matches the reconstructed payload and hash. |
| 12. Credential ID and hash | **Partial.** The selected secret's SHA-256 is compared with the record using compare_digest. credential_id is only a required string and is not independently checked against inventory or organization/project ownership. A self-consistent record can pair an arbitrary ID with a matching secret hash. |
| 13. Authorization semantics | Authorization and operator fields are plain attestations. The request digest and credential digest are equality checks. There is no signature verification or independent operator authentication. |
| 14. Alternate CLI path | The only sending CLI branch requires --execute-live and a validated --admission record, then calls execute() and the transactional claim. --show-request only renders the plan. No CLI skip flag or fallback path was found. A caller with local access can still supply unverified attestations or use another program outside this harness. |

The request and quota ledger still bind dispatch to one run, reject duplicate claims and count pending reservations across concurrent processes. Local SQLite covers this harness only. It cannot establish organization-wide usage or exclusive traffic control.

## Regression tests

From the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_quota_admission_audit_20261104_080000/test_work data/output/t0022_quota_admission_audit_20261104_080000/test_admission_audit.py data/output/t0022_live_stage_a_harness_20261104_074428/test_live_stage_a.py
```

**38 passed, 1 strict xfail in 8.65 seconds.** The expected failure is the demonstrated partial project-limit acceptance. Added tests cover empty windows, missing RPD and TPD separately, duplicates, partial project windows, absent evidence and counters, empty evidence, stale evidence and wrong request hash. Existing mocked HTTP and subprocess tests ran alongside them. No Stage A execution against Groq occurred.

## Verdict

**The admission gate is not ready for a future operator-approved attempt.** Enforce applicable project/split-window completeness, bind evidence timestamps to individual records or a verified common snapshot, and verify the credential inventory binding before readiness review. External traffic and quota evidence still need authoritative operator verification. The audit added its report and regression module in a fresh directory. No live admission record was created.
