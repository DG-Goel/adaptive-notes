# Opt-in five-organization scheduler

## Local total-limit accounting (November 6 update)

Credential identity reviews and local-policy credential approvals accept an explicit
`expires_at: null` for operator approval until revoked. The field remains required;
missing validity data does not grant approval. Finite deadlines are still enforced
when supplied. Future-dated reviews are rejected. Disable/remove the slot or revoke
the provider key to stop use; request binding and authorization remain mandatory.
The standalone frozen legacy harness keeps its original finite-expiry schema.

`LocalQuotaAdmission` accepts request/credential/configuration binding, authorization,
and `QuotaLimit` rows containing scope, metric and configured total limit. It does
not request external used/outstanding measurements, usage freshness timestamps,
or a verified-available-quota declaration. This is an alternative to the existing
`VerifiedAdmission` interface described below; callers explicitly choose the type.

For local accounting, admission requires:

`local ledger usage + outstanding local reservations + proposed request <= min(floor(total limit * 0.85), configured ceiling)`.

The configured ceilings remain RPM 25, RPD 850, TPM 6800, TPD 170000. Applicable
project and split-token limits remain enforced. Actual usage reconciles local
reservations; unknown outcomes retain reservations across resets/restarts. Unknown
external usage is outside this mode's accounting scope, not certified as zero.
Status/audit labels this mode `local_tracked`, never `quota_verified`.

The live bridge now accepts this policy with a matching `LocalStageARecord`:
provider/model/stage, fixed source T0022, run ID, organization/project, operator,
authorization, credential identifier/fingerprint, exact request hash and total
limits. Pass that record and a genuine matching credential approval to the existing
`StageAAuthorization(record, approval)` interface. No fresh available-capacity,
external-usage inventory, traffic-control or usage-window timestamps are requested
by this local-policy path. Constructing these records does not grant approval.

The bridge preserves one enabled organization, no automatic retries, fixed reviewed
payload, credential validity/fingerprint/authorization binding, and one-shot Stage A
control claims. It requires the exact active scheduler reservation. Its total limits
must match the scheduler admission. Both the scheduler and shared Stage A quota
database enforce the 85% ceilings, retaining earlier claims across policy changes.
Confirmed attempts age out of rolling windows; uncertain attempts remain reserved.
The adapter reconciles Stage A accounting on success and error paths. No live
credentials are enabled by this change; Java payload authorization remains separate.

Frozen Stage A/B files are unchanged. Their standalone legacy entry points retain
the original verified-admission contract. The application's legacy verified path
also remains available explicitly, but local-policy callers need no available-quota
measurements at either the scheduler or Stage A bridge.

Implementation is offline-tested only. Live execution is not authorized. Stage A HOLD, Stage B HOLD, release NO-GO.

## Scope and entry points

`organization_scheduler.py` provides immutable configuration, credential inventory binding, verified admission, durable organization-partitioned claims/usage, and secret-free status/audit records. `organization_extraction.py` provides `prepare_request()` and the explicitly invoked `extract_chunk()` operation. Neither module is imported by an existing production runner or Stage A/B harness. No CLI or background worker starts requests automatically.

The adapter reuses `build_extraction_prompt`, `TokenBudgetManager`, `KnowledgeExtractor._extract_from_chunk`, the strict raw-contract/evidence parser, and `GroqProvider` error classification and response guards. Legacy credential pools, extraction accounting, chunking, splitting, semantic thresholds and the existing 85% token policy are unchanged. This is a per-chunk adapter, not a document orchestrator or note publisher. Existing downstream semantic/structural evaluation remains required. Separate chunk results must not be blindly concatenated into a production knowledge base; normal ID/merge and document accounting require reviewed integration.

## Configuration and organization registration

Load environment using the application's existing explicit dotenv convention if needed. This module does not load or modify `.env`. Its loader has no fallback to GROQ_API_KEY or GROQ_API_KEY_1..5. Configure five slots with placeholders only:

```dotenv
GROQ_ORG_1_ENABLED=false
GROQ_ORG_1_ID=<verified-organization-1-id>
GROQ_ORG_1_API_KEY=<secret-store-value>
GROQ_ORG_2_ENABLED=false
GROQ_ORG_2_ID=<verified-organization-2-id>
GROQ_ORG_2_API_KEY=<secret-store-value>
GROQ_ORG_3_ENABLED=false
GROQ_ORG_3_ID=<verified-organization-3-id>
GROQ_ORG_3_API_KEY=<secret-store-value>
GROQ_ORG_4_ENABLED=false
GROQ_ORG_4_ID=<verified-organization-4-id>
GROQ_ORG_4_API_KEY=<secret-store-value>
GROQ_ORG_5_ENABLED=false
GROQ_ORG_5_ID=<verified-organization-5-id>
GROQ_ORG_5_API_KEY=<secret-store-value>
```

An enabled slot requires a matching `Identity` from a separately controlled custodian inventory. Each record contains slot, organization, project, credential_id, credential_sha256, verified_by, ownership_evidence, verified_at and expires_at. Numeric timestamps are finite UTC Unix seconds; explicit null expiry means approval until revoked. The custodian must actually verify provider ownership and project membership. Fingerprints bind secret bytes to that reviewed inventory; they do not prove organization ownership. These are operator attestations, not cryptographic signatures or authenticated provider introspection. Protect inventory, admission inputs, process environment and database permissions accordingly.

Pass those records to `load_organizations(identities)`. Duplicate organizations, slots or credential fingerprints are rejected. Keys are retained in private runtime storage, never in SQLite, representations, status or audit output. Enabling a slot without a credential fails closed. Disabled slots are not scheduled. Registration is persisted, and an unexpected identity change on restart fails closed.

One frozen `ExtractionConfiguration` object is shared by every slot. It pins Groq, openai/gpt-oss-120b, temperature 0, json_object, strict_evidence=True, no fallback, and existing output/budget defaults. Bounded transient retries default to two retries (three physical attempts), configurable down to zero and capped at three retries. No model/provider/temperature option varies by organization. The database pins a fingerprint of configuration and prompt construction; an unreviewed change refuses startup. Runtime changes to protected implementations still require deployment review.

## Admission and quota accounting

Create no real admission until separately authorized. `VerifiedAdmission` binds organization, project, credential ID/fingerprint, request ID, exact payload hash, configuration hash, authorization and operator evidence. Four organization windows are mandatory: RPM, RPD, TPM, TPD. Applicable project windows and declared ITPM/OTPM windows are also mandatory. Each row has scope, metric, configured limit, used, outstanding, data_as_of and evidence. Inventory/usage completeness declarations and traffic coordination are required. Duplicate/missing windows, stale/future timestamps, blank evidence and contradictory ceilings fail. Every observation must be at most 15 seconds old, with at least 90 seconds of traffic control remaining; rechecked immediately before dispatch.

`quota_unknown`, `quota_estimated` and `quota_exhausted` never dispatch. Only a valid, current `quota_verified` record permits admission. “Verified” describes the gate's validation of trusted evidence declarations, not an independent provider query. The implementation cannot discover external organization traffic. Unknown traffic is never zero. Configured limits are supplied per organization; there are no assumed Free Tier defaults in admission. Reference ceilings 30/1000/8000/200000 yield internal budgets 21/700/5600/140000, but must be independently established for each organization.

The new aggregate ceiling is exactly `floor(limit * 70 / 100)` for each applicable metric. It does not change the existing extraction budget's 85% policy or reduce/increase its computed output allowance. A request whose unchanged allocation exceeds a 70% ceiling receives HOLD. For example, a 6800-token extraction allocation does not fit a 5600-token organization ceiling. A 5007-token allocation leaves only 593 tokens before other charges under that ceiling.

The same SQLite file coordinates all workers, with distinct organization identities and organization-partitioned claims/usage. It must not be cloned, reset or replaced to bypass history. Admission charges external used + external outstanding + local reservations/usage + the proposed attempt. Overlap is conservatively double-counted. Each retry reserves another estimated input plus full completion allowance. Every actual request counts toward minute/day request limits, including failures. Complete valid reported input/output/total usage reconciles that attempt. Reasoning is recorded as a subset of completion tokens, not added twice. Missing/inconsistent usage keeps the full reservation. Unexplained total-token excess is conservatively charged to input for split accounting.

Uncertain attempts retain their reservations indefinitely, even if a later retry succeeds. Confirmed attempts remain charged for conservative rolling local minute/day windows. These local accounting windows are not a claim about Groq's exact internal limiter/reset algorithm. External evidence must account for that difference.

## Selection, concurrency and failures

There is one globally active operation in a scheduler database. SQLite BEGIN IMMEDIATE serializes admission, and unique operation/attempt keys prevent duplicate claims. Other workers receive HOLD while it is active. This deliberate serialization preserves deterministic rotation after **validated success**, rather than after selection or response arrival. Successful eligible sequence is 1,2,3,4,5,1. Disabled, blocked, cooling or unverified organizations can be skipped for independent requests. Failed operations do not advance the cursor. The same request ID cannot be resubmitted to another organization.

A claim survives process crashes without automatic lease release. A crash can block the scheduler until reviewed recovery is separately implemented/approved. Do not edit or delete the ledger to release it. Individual timeout/server attempts remain charged as uncertain. The pre-send dispatch marker records intent; a crash between that marker and socket dispatch cannot establish whether the provider received the request.

- 401 disables the credential/organization persistently. No same-operation rotation.
- 403 disables the organization for this fixed model operation pending review.
- 429 records rate-limited eligibility, respects Retry-After (at least one second, otherwise a conservative 60 seconds), stops the operation and returns retryable=False. Cooldown alone never establishes fresh quota admission.
- 400/model validation errors stop permanently without identical-request retries.
- Classified transient network/server/request errors use bounded retries on the same organization, each requiring fresh admission and additional capacity. SDK and transport retries are zero.
- Unknown errors fail closed. All exhausted/final failures are non-retryable to an outer extractor.
- Truncation, empty output, malformed/duplicate-key JSON, wrong model and strict source-evidence failures return no items and never count as successful extraction.

`review_organization(updated_registry, slot, evidence)` is an explicit protected operator repair entry point. It requires current reviewed identity, preserves organization/project, all usage, cooldown and claims, and clears only the reviewed authentication/access block. It refuses active operations or unrelated identity changes. Existing workers using stale identity are rejected. It is not an automatic repair or a Stage A authorization mechanism.

## Audit and status

SQLite stores operations, attempts and audit_events with request/organization IDs, pinned model/configuration, selection reason, timestamps, reservations, actual usage/reasoning, dispatch markers, status, finish reason, duration, retries, error classification/sanitized diagnostics and extraction/mechanical-validation outcomes. No keys or Authorization headers are stored. Returned items preserve normal evidence metadata; semantic entailment is explicitly unverified.

`status()` displays all five slots, enabled state, identity expiry, access block, cooldown, configured budgets from historical admission, tracked usage, outstanding reservations and last outcomes. Historical evidence alone never yields current availability. `status(admissions, input_tokens, output_tokens)` can compute a request-specific eligibility snapshot and next candidate, but reserves nothing. Admission is rechecked atomically on claim and before dispatch.

## Remaining boundaries

This library is not permission to invoke its network-capable adapter. No Stage A/B authorization/checkpoint code was changed or bypassed. Integration with those gates, document orchestration, live admission evidence, any live smoke test and production release are separate decisions. There is no automatic recovery, output publication, mock fallback or provider switch. MockTransport is used only by offline tests. Passing tests prove mechanics, not real-model quality, semantic faithfulness, provider ownership or actual quota headroom.
