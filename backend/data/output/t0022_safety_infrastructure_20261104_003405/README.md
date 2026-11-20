# Two-stage experiment safety infrastructure

**Offline validation complete. Live readiness remains NOT READY. Release remains NO-GO.**

## Entry points and artifacts

| Entry point | Behavior |
|---|---|
| stage_a.execute_a | Requires explicit offline authorization. Checks the preserved T0022 source hash, independently admits the simulated quota, and consumes the A claim before a scripted dispatch. Saves response and diagnostics. A complete, mechanically valid result becomes an exclusive-create fact-store checkpoint awaiting human review. |
| stage_b.approve_b | Requires a reviewer identifier, exact checkpoint SHA-256, review of every fact ID and mapping of every required teaching topic. The final-pi and division compiler errors require separate fact IDs. The reviewer attests semantic support and scope. |
| stage_b.execute_b | Reads approval and verifies the checkpoint hash against the approval and original A event. Builds its input from those verified bytes. Rechecks quota, consumes B's independent claim, and runs strict evidence reconstruction and the supplied field reviewer. Successful items stay isolated for review. |

The entry points are Python functions exercised by the offline tests. The harness accepts only its scripted OfflineScenario. It has no transport, credential loader, background worker, or production publication path. A returns zero publishable items. A failed B produces no review-result artifact. Even a successful B returns zero publishable items.

Each run has a directory with control.sqlite and exclusive-create request, response and checkpoint files. Request records include the model pin, full credential-free fixture messages, their hash, unchanged budget calculation and simulated quota evidence. Response records retain raw mock body, finish reason, status, usage and provider request ID when supplied. A's validation event stores the exact checkpoint hash. B leaves A's files intact.

## Durable marker and approval schemas

- **run** binds a ledger directory to one run ID.
- **claims** has a unique primary key over run and stage, plus claim time. A transaction inserts the claim and authorization event together. SQLite full synchronization and the unique constraint protect the claim across local processes sharing this ledger.
- **events** stores ordered run/stage, event kind, timestamp and JSON payload. Authorization claim, dispatch attempt, confirmed response and uncertain outcome are distinguishable. Dispatch is recorded before the mock is invoked. A pending dispatch without a confirmed response is treated as uncertain on reopening. A crash before dispatch leaves the claim consumed too. A confirmed 429 is terminal.
- **approvals** has one record per run and B stage, with reviewer ID, exact SHA-256, approval time and JSON review details. A changed checkpoint is refused. Approval is a trusted operator attestation, not identity authentication or automated semantic entailment.

The ledger is the authoritative local attempt record. A crash during artifact writing can leave an incomplete file, but a missing or mismatched checkpoint validation event prevents B admission. A consumed claim has no release path.

## Quota admission and limits

QuotaEvidence identifies provider, organization and model and includes a verification time and request/token ceilings and usage by window. The offline checks require a minute window and check each supplied applicable window. They reject missing or mismatched evidence, snapshots older than 15 seconds or from the future, insufficient headroom, and lack of authoritative limits, coordinated usage or controlled traffic. The unchanged estimator computes the entire request allocation before admission.

OfflineScenario.quota_lease simulates a trusted coordinator. The fields are fixture assertions. They do not verify any real Groq organization, current usage, applicable limit completeness, or capacity reservation. A future integration must provide authoritative limits for every applicable window and coordinated usage under a lease that covers preflight and dispatch. If other organization traffic cannot be controlled or accounted for, deny the stage. Previous headers and process-local counters cannot reserve headroom. There is no assumed provider reservation endpoint.

## Tests and exact results

The first invocation hit 19 setup errors because the sandbox default pytest temp directory could not create numbered subdirectories. A workspace-local pytest base directory resolved the setup issue. From the backend directory:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_safety_infrastructure_20261104_003405/test_work data/output/t0022_safety_infrastructure_20261104_003405/test_control.py
```

**19 passed in 3.48s.**

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --tb=short --basetemp=data/output/t0022_safety_infrastructure_20261104_003405/regression_work data/output/t0022_safety_infrastructure_20261104_003405/test_control.py data/output/t0022_offline_prototype_20261103_225328/test_prototype.py
```

**40 passed in 3.63s.** Separate subprocesses competed for the same SQLite claim, with exactly one winner. Separate crash processes exited after claim and after the dispatch marker. Tests covered timeout, 429, hash mismatch, changed artifact, incomplete A, separate B approval, quota rejection and B recheck, and isolated publication. Socket creation, connection and address resolution were blocked in the tests and subprocesses.

## Remaining live prerequisites

Use one trusted ledger path per run and protect the ledger and checkpoint from unauthorized writers. The local uniqueness constraint applies to processes using that ledger, not cloned run directories. The review record trusts the configured operator to attest the meaning and coverage of each fact. The exact approved bytes are loaded once for B. Live response sanitization, explicit credential selection, SDK and application retry configuration, authoritative quota verification and an actual coordination lease would require a separately reviewed transport integration and explicit authorization. No actual network request or recovery job ran.
