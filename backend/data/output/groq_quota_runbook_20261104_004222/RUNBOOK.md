# Groq shared-quota admission runbook

Reviewed 2026-11-04 (Asia/Calcutta). Scope is the T0022 experiment on Groq openai/gpt-oss-120b. **Decision: HOLD for both stages. Release: NO-GO.** This investigation used public documentation. Actual account identity, quota and competing traffic were unverified.

## Supported evidence sources

| Source | What it establishes | Limits of the evidence |
|---|---|---|
| Organization Limits in Groq Console | Current configured limits for the selected organization and model. Inspect RPM, TPM, daily limits, and any input/output split. | The public model table gives plan examples. The configured ceiling alone gives no current headroom. |
| Console organization/project selector, API Keys, and project settings | Project membership for a key recorded at issuance, and configured project model limits. | An operator must match the configured secret version to the issuance or inventory record. A key name or environment variable alone cannot establish ownership. |
| Console Usage, Metrics, and Logs | Project-scoped activity, request logs and usage trends. | Check the selected project, measurement window and data timestamp. A quiet chart can omit queued or in-flight work and activity in other projects. Public docs do not establish an exact, instantaneous quota balance from these charts. |
| Existing response headers from the matching context | Groq documents request limit/remaining/reset headers as **RPD**, token limit/remaining/reset as **TPM**, and retry-after on a 429. | These are response-time snapshots. They establish neither RPM headroom nor every other applicable limit, and reserve no capacity. Preserve only sanitized headers. |
| Enterprise Prometheus metrics | Groq documents an authenticated VictoriaMetrics-backed query surface, with usage metrics by model and project. | The documented request/token rates use five-minute windows. These are telemetry rather than exact one-minute balances or reservations. Confirm entitlement and visibility before relying on them. This investigation made no queries. |
| API reference and per-response usage | Usage associated with an individual inference response. | The reviewed public reference did not establish a key-to-organization introspection method, a general remaining-quota preflight endpoint, or a reservation API. Batch or model listing does not provide this evidence. |

Organization limits constrain combined traffic. Project-specific ceilings can be more restrictive and still sit under the shared organization ceiling. Multiple keys in one organization do not create additional organization quota. Groq documents separate input/output ceilings as organization-level controls where configured.

Sources: [Groq Rate Limits](https://console.groq.com/docs/rate-limits), [Projects](https://console.groq.com/docs/projects), [Prometheus Metrics](https://console.groq.com/docs/prometheus-metrics), [API Reference](https://console.groq.com/docs/api-reference), [Model Permissions](https://console.groq.com/docs/model-permissions).

## Collect evidence and control traffic

1. Have an organization owner confirm the organization, project, model permissions, and selected credential using the Console and secret inventory. Record a non-secret key identifier or inventory alias and secret version. Keep credentials and Authorization headers out of artifacts.
2. Record each applicable organization and project ceiling and its enforcement window from account-specific settings. Include RPM, TPM, RPD, TPD and configured ITPM/OTPM. Record other applicable restrictions separately, such as an organization spend block. Mark a dimension inapplicable only with evidence.
3. Inventory every caller sharing the relevant limits across projects, users, machines, keys, scheduled tasks, queues, and applicable service tiers. Obtain named owner confirmation. Establish an organization-wide pause with outstanding work drained or conservatively charged, or an existing shared coordinator that covers every relevant caller and holds admission through dispatch. Include queued and in-flight work and uncertain attempts. A local SQLite claim covers only processes sharing its ledger. A project cap does not exclude traffic from other projects.
4. Establish a conservative upper bound on use for each active window. Use authoritative current data where available or reconcile an authoritative baseline with complete coordinated dispatch and usage records. Include pending commitments and unknown usage at a defensible upper bound. A quiet interval can clear minute history only if the applicable reset behavior and complete absence of traffic are established. Daily windows still need independent accounting. Missing coverage, delayed metrics with unbounded gaps, and conflicting observations mean HOLD.
5. Freeze and hash the exact request messages. Calculate the unchanged harness budget. For each scope and window check that ceiling minus bounded usage and outstanding commitments covers one request and the applicable token allocation. Use full estimated input plus full output allowance for combined token checks, and evaluate input/output separately where applicable. Include reasoning within completion allowance and use no assumed cache savings. Apply a defensible estimation margin or HOLD if no reliable bound exists. Avoid double-counting commitments already in usage.
6. Record observation time, data-as-of time, reset or window, collection time, scope, evidence references and expiration. Recheck just before claiming dispatch while coordination remains in force. The offline gate uses a 15-second snapshot-age cutoff. Apply that cutoff and any stricter source or lease expiry. Refreshing a chart does not refresh the timestamp of its underlying data.

## Admission record for each stage

Copy this blank checklist into a fresh stage record. All required fields need evidence before marking PASS.

| Check | Operator record |
|---|---|
| Run ID, stage, operator, separate authorization reference | ___ |
| Organization and project IDs or verified account identifiers | ___ |
| Selected credential inventory ID and version, ownership evidence | ___ |
| Provider, model, message hash, exact computed input estimate and output cap | ___ |
| Each scope and window: configured ceiling, bounded usage, outstanding commitments, headroom, planned charge, evidence reference | ___ |
| Caller inventory, traffic owner confirmations, drain or coordinator status and lease expiry | ___ |
| Data-as-of time, verification time, time zone, validity deadline | ___ |
| B only: reviewed A checkpoint hash, reviewer and B approval | ___ |
| PASS / HOLD, reason and operator sign-off | **HOLD until filled and verified** |

## Separate stage decisions

**A.** Use the complete frozen T0022 source, canonical T0022 and pinned Groq model. Recompute the allocation from the exact guarded request. A PASS establishes operational admission only. Dispatch still requires explicit authorization and a reviewed live harness. One stage claim permits one dispatch. Preserve status, usage, request ID, diagnostics and the fact store, then stop for semantic review. No publishable knowledge results from A.

**B.** Require a complete A checkpoint and recorded review of every fact and required teaching point. Bind separate B approval to the exact checkpoint SHA-256. Rebuild the request solely from those bytes and the structuring contract. Recompute its budget and fill out a new admission record, accounting for A's usage and any other current commitments. Hold if the prior review or current quota gate fails. B has its own one-dispatch claim and preserves A artifacts on failure.

## Stop conditions

HOLD on uncertain identity, unknown limits or headroom, incomplete coordination, stale or contradictory evidence, expired traffic control, changed request or checkpoint, or missing authorization. If a separately authorized dispatch returns HTTP 429, preserve its response and timing information, consume that stage attempt and stop. Treat timeout or uncertain delivery as consumed too. Do not retry or change keys, providers, or credentials to bypass limits.

## Readiness recommendation

A path to admission exists if an authorized organization operator can establish the credential binding, all applicable ceilings, conservative current headroom and control or complete accounting of competing traffic. The documented tools provide inputs to that decision. None of the reviewed surfaces establishes an atomic organization reservation. This runbook records no actual quota evidence and authorizes no dispatch. Keep both stages on HOLD pending operator evidence, harness review and explicit stage authorization.
