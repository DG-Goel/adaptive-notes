# Stage A operator verification checklist

**Stage A HOLD. Stage B HOLD. Release NO-GO.** This document does not authorize execution.

## Reviewed files and locations

The revised harness directory, abbreviated H below, is `C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816`.

Reviewed H\AUDIT.md, H\admission.schema.json, H\credential_approval.schema.json, H\request_plan.json, H\admission.py and H\live_stage_a.py. There is no README.md in H. The historical `C:\Projects\adaptive-notes\backend\data\output\t0022_live_stage_a_harness_20261104_074428\README.md` was read for context. Its old execution command must not be used for revised authorization.

Fixed custodian approval path: `C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\credential_approval.json`.

Suggested future admission path: `C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\admission.json`.

Shared ledger: `C:\Projects\adaptive-notes\backend\data\output\t0022_live_stage_a_harness_20261104_074428\runs\quota.sqlite`. Run artifacts reside under that runs directory, in the approved run_id subdirectory. Never replace this ledger with a fresh database to avoid claims.

## 1. Credential custodian review

- [ ] Obtain separate authorization for one Stage A request, naming this revised entry point, operator, unique run_id and exact request hash.
- [ ] Review authenticated Groq Console inventory or authoritative provider-issued records identifying the organization, project and credential inventory entry. Record stable identities and secret-free evidence references. Resolve ambiguous names.
- [ ] Trace the selected secret from the approved secret store to that inventory entry, using issuance/rotation records where needed. A masked suffix alone is insufficient if the mapping remains uncertain.
- [ ] Supply exactly that credential securely through GROQ_STAGE_A_API_KEY in the eventual process environment. Never paste its value into commands, screenshots, reports, source control or JSON artifacts.
- [ ] Compute its SHA-256 within the protected custodian workflow without displaying the key. Put the lowercase fingerprint in the two protected records. The offline command below verifies it against the in-memory key without printing either.
- [ ] Protect the approval file independently from the admission preparer. Inspect filesystem permissions and prevent unauthorized modification, deletion or cloning of the shared ledger.

**Trust distinction:** a human can verify provider records independently of the admission preparer. The harness only checks operator attestations, record equality and expiry. It does not fetch/authenticate evidence references or verify signatures. A matching hash proves equality of secret bytes, not organization ownership. If the provider records cannot establish ownership, HOLD.

## 2. Prepare credential_approval.json

Only after actual verification, use H\credential_approval.schema.json. All listed fields are required; extra fields fail.

| Fields | Required source |
|---|---|
| provider, model, stage | Groq, openai/gpt-oss-120b, A |
| credential_id, credential_sha256 | Verified inventory and protected fingerprint |
| organization, project | Explicit verified provider identities |
| evidence_kind | operator_reviewed_console_inventory or operator_reviewed_provider_record |
| ownership_evidence, verified_by | Retrievable nonblank evidence reference and actual custodian identity |
| verified_at, expires_at | Finite UTC Unix seconds; verification not future-dated and approval unexpired at dispatch |
| operator, authorization, authorization_evidence | Actual authorization and evidence, not a purported cryptographic signature |
| run_id, request_sha256 | Unique approved run and canonical request digest below |

Use exclusive creation in the fixed protected location. Preserve prior approvals under custodian policy, without silent overwrite. Never submit simulated test fixtures, placeholders or guessed values as real evidence.

## 3. Complete organization/project limit inventory

- [ ] Review authoritative limits for this model, organization and project, including overrides and stricter applicable ceilings. Preserve secret-free references with identity and observation time.
- [ ] Include organization RPM, RPD, TPM and TPD. Confirmed Free Tier caps are 30, 1000, 8000 and 200000; they do not establish current usage or remaining headroom.
- [ ] Establish project_limits_apply explicitly. Lack of access or missing rows does not prove no project limits exist. When applicable, include all four project metrics. If actual settings cannot be represented without inventing ceilings, HOLD for review.
- [ ] Establish whether ITPM and OTPM apply separately for each scope from authoritative settings or provider confirmation. Aggregate TPM alone does not establish non-applicability. Populate organization_split_metrics/project_split_metrics and corresponding inventory and usage rows for every applicable split metric. Empty lists require affirmative evidence of non-applicability.
- [ ] Provide exactly one limits row and one windows row per required scope/metric. Duplicate, unexpected, missing or contradictory records fail. Each window.limit must match the inventory. The implementation rejects project ceilings above matching organization ceilings; resolve such a discrepancy rather than disguising it.
- [ ] Set authoritative_limits and complete_limit_inventory true only after verifying completeness. inventory_evidence must support applicability and completeness. Unknown completeness means HOLD.

## 4. Fresh usage for every window

Each windows record requires scope, metric, limit, used, outstanding, data_as_of and evidence. scope is organization or project, bound to the explicit identities at record level. Counts must be nonnegative integers. Evidence must be nonblank and identify the underlying observation and scope.

- [ ] Establish organization-wide usage, across all keys/consumers, and applicable project usage for every minute, daily and split metric. Missing daily data is never zero.
- [ ] Confirm actual window semantics and telemetry delay. Capturing old telemetry now does not make it fresh. Existing response headers are observations, not reservations, and may omit required metrics. Do not send a probe request for this checklist.
- [ ] Each underlying observation gets its own finite UTC Unix-second data_as_of. Each row and the global observation must be no more than 15 seconds old at claim and immediately before dispatch, never future-dated. Every row must be no later than verified_at; global data_as_of <= verified_at <= current time.
- [ ] If authoritative tools cannot provide every required balance at this freshness, HOLD. Never update timestamps without refreshing the underlying evidence.
- [ ] Set complete_usage_inventory true only after establishing all usage. A quiet local machine does not prove zero organization traffic.

## 5. Outstanding work and competing traffic

Coordinate every application, machine, user, key and worker sharing quota. traffic=controlled requires effective coordination; traffic=accounted requires completely bounded competing work. Record coordination_evidence. Unknown/unbounded traffic means HOLD.

Record in-flight and committed external requests/tokens conservatively as outstanding per applicable window. Do not subtract assumed overlap from used. control_until must reflect real coordination and extend at least 90 seconds beyond both admission checks. Maintain coordination through completion or uncertain-outcome reconciliation. An HTTPX timeout does not prove provider execution stopped.

Inspect existing shared ledger claims through authorized read-only procedures. Pending claims remain charged indefinitely. Completed claims remain charged for rolling 60-second or 86400-second windows. Never clear uncertain claims or subtract local claims from external counters; possible overlap is deliberately double-counted. SQLite coordinates this harness only, not all organization traffic.

For each scope/metric the transaction requires:

`used + outstanding + local reservations + proposed allocation <= effective ceiling`

The proposed charge is one RPM/RPD request, 1007 ITPM tokens, 4000 OTPM tokens or 5007 TPM/TPD tokens. Applicable lower supplied/Free Tier ceilings prevail. Token ceilings additionally use floor(ceiling * 0.85), or an approved stricter margin. Default organization ceilings are 6800 TPM and 170000 TPD, leaving 1793 TPM and 164993 TPD after this proposal **before all existing charges**. These are arithmetic maxima, not observed balances. Project and split windows must pass independently.

## 6. Prepare admission.json

Use H\admission.schema.json. Match approval fields exactly: provider, model, stage, credential_id, credential_sha256, organization, project, operator, authorization, run_id and request_sha256. source_id is T0022. Use a schema-valid unique run_id, never an existing artifact directory or consumed claim.

Populate timestamps, traffic/control evidence, applicability declarations, complete-inventory declarations, limits and windows from actual evidence above. decision accepts only PASS. If any requirement is unresolved, keep HOLD in the operator log instead of creating a false PASS record. Prepare stable inventory material beforehand, then refresh usage immediately before a separately authorized attempt. No fixture values or assumptions.

## 7. Offline validation

This command prints the complete frozen request without HTTP or a claim:

```powershell
Set-Location 'C:\Projects\adaptive-notes\backend'
& 'C:\Projects\adaptive-notes\backend\.venv\Scripts\python.exe' -B 'C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\live_stage_a.py' --show-request
```

After genuine records exist, run this read-only validation. It suppresses record values on error. It does not invoke execute, open the quota ledger, consume a claim or send HTTP.

```powershell
@'
import json, os, sys, time
from pathlib import Path
h = Path(r'C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816')
sys.path.insert(0, str(h))
import live_stage_a as live
from admission import Admission, CredentialApproval, validated_windows, fresh, verify_credential
try:
    def read(path):
        return json.loads(path.read_bytes(), object_pairs_hook=live.unique_object, parse_constant=live.reject_constant)
    record = Admission.model_validate(read(h / 'admission.json'))
    approval = CredentialApproval.model_validate(read(live.CREDENTIAL_APPROVAL))
    frozen = read(h / 'request_plan.json')
    payload, budget, sources = live.request_plan()
    calculated = live.digest(live.encode(payload))
    if payload != frozen['payload'] or calculated != frozen['request_sha256'] or calculated != record.request_sha256:
        raise ValueError('request mismatch')
    if (budget.input_tokens, budget.max_output_tokens, budget.total_tokens) != (1007, 4000, 5007):
        raise ValueError('budget mismatch')
    validated_windows(record)
    fresh(record, time.time())
    verify_credential(record, approval, os.environ.get('GROQ_STAGE_A_API_KEY'), time.time())
    if (live.LIVE_STATE / record.run_id).exists():
        raise ValueError('existing run directory')
except Exception as exc:
    print('HOLD: offline validation failed (' + type(exc).__name__ + '); inspect protected records locally.')
    sys.exit(1)
print('Offline record checks passed. No claim/request made. Manual evidence and transactional quota checks remain required.')
'@ | & 'C:\Projects\adaptive-notes\backend\.venv\Scripts\python.exe' -B -
```

Schema validation alone does not implement cross-record requirements. This command uses runtime checks but does not authenticate evidence, inspect ledger balances, reserve quota or authorize execution. The real quota transaction must still reconcile reservations. Never call QuotaLedger.claim as a dry-run. Freshness may expire during review; refresh observations, not merely timestamps.

## 8. Request identity and future command

Expected canonical payload digest, using control.encode/control.digest rather than hashing formatted JSON file bytes:

`b5f17aa2c8bf06981ab664ee1bb7a45d969131e95695df48c687e3e1bafd1a19`

Compare --show-request with request_plan.json including every message character and complete unchanged T0022. Configuration is Groq openai/gpt-oss-120b, POST https://api.groq.com/openai/v1/chat/completions, temperature 0, max_completion_tokens 4000, response_format json_object, stream false, service_tier on_demand. Estimated input 1007 and allocation 5007 are not exact tokenizer counts. HTTPX retries=0, redirects/environment proxies disabled, no SDK retry layer, fallback or rotation.

**Do not execute now.** Only after separate authorization, genuine approval, fresh evidence and operator sign-off:

```powershell
Set-Location 'C:\Projects\adaptive-notes\backend'
& 'C:\Projects\adaptive-notes\backend\.venv\Scripts\python.exe' -B 'C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\live_stage_a.py' --execute-live --admission 'C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\admission.json' --token-margin 0.85
```

Never bypass HOLD through an older entry point, alternate ledger, imported execute, injected transport or alternate key. There is no CLI dry-run admission mode. A claim is consumed before dispatch. Never rerun after error, timeout, crash or uncertain outcome.

Mechanical success saves A_request.json, A_admission.json, A_response.json and A_facts.json under the unique run directory, binds the checkpoint hash and returns awaiting_manual_review with zero publishable items. Semantic support and required coverage are not automatically checked by this live harness. Review every fact and quote manually, including both distinct compilation errors, pi-to-PI correction, float/double alternatives and increment example. Stage B requires separate approval and independently refreshed quota evidence; it never follows automatically.

## 9. Immediate HOLD conditions

HOLD for uncertain credential ownership or organization/project, unauthorized/tampered/expired approval, mismatched fingerprints or bindings, missing authorization, unknown limit applicability, missing daily/project/split records, duplicates or contradictions, blank evidence, stale/future/delayed telemetry, unknown commitments, uncontrolled traffic, insufficient any-window headroom, inaccessible/replaced ledger, reused run, changed source/payload/budget/hash or expiring traffic control.

After an authorized attempt, stop on any HTTP failure including 401/403/429, timeout, malformed JSON, wrong model, truncation, invalid schema/provenance/quote or failed manual quality review. Preserve artifacts and claims. Never retry, rotate keys or switch providers to bypass restrictions. Matching quotes do not prove semantic entailment.

## Preparation status

Only this checklist was created. No approval/admission record, API request, quota claim, extraction or Stage A execution occurred. Frozen request, production code and historical files were not modified. Commands above are operator instructions; no real record validation was run without genuine evidence. Stage A HOLD. Stage B HOLD. Release NO-GO.
