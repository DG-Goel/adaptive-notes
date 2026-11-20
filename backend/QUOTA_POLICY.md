# Active operator-approved quota policy

## Five-friend ownership clarification

The operator explicitly states that five friends collaborate on this project, and
each configured key belongs to a different friend with a separate organization.
This is the operator's ownership statement, not a provider-issued permission record.
Do not repeatedly ask the operator to reconfirm this ownership arrangement or assume
that distinct organization IDs alone establish rate-limit evasion.

The operator requests five-key rotation. Each organization's usage, reservations,
credentials and applicable 85% ceilings must remain separately accounted for.
Do not switch credentials to retry a request rejected with 429, evade an active HOLD,
or clear uncertain charges. Any live multi-organization implementation must preserve
exact request authorization and the provider's applicable limits.

The document runner now supports explicit `--rotate-five` authorization preparation.
Primary requests are pinned to slots 1,2,3,4,5 in order; recovery children stay on
their parent's slot. All five exact credential/request records must match. Legacy
and single-request Stage A gates remain single-organization. A quota HOLD waits on
the assigned slot; HTTP 429 or uncertain results stop without switching keys. Explicit evaluation
continuation may attempt a different primary chunk after a confirmed HTTP 200
validation rejection, preserving the failed chunk as unresolved; it is not a retry.

## Existing total-limit admission

The latest operator instruction sets a HARD 85% limit, superseding the earlier
50% and 60% policies. Use 85% of configured total provider limits, capped by the scheduler
ceilings: RPM 25, RPD 850, TPM 6800, TPD 170000. Account for recorded local
attempts and shared Stage A reservations, including retained uncertain charges.

Do not require an external available-capacity report or a `quota_verified` inventory
label for the approved local-total admission path. The operator explicitly removed
that prerequisite and reaffirmed this correction after the November 7 blocked report.
`quota_unknown` describes provider visibility; it is not itself a local-admission HOLD.
Do not fabricate external usage or claim that it is known to be zero.

Older manifests and configuration overrides cannot raise the active hard limit.
Request planning also clamps any requested safety margin to at most 85%.
This is a limit on estimated/reserved tokens; the known tokenizer-accounting
blocker remains unresolved. Do not infer actual provider fit from this change.
Do not edit historical authorization records, usage charges or reservations.

Preserve actual quota HOLDs, HTTP 429 handling, credential binding, exact Stage A
authorization, no SDK retries and one selected organization. Never clear historical
usage to gain capacity. Credential approval remains non-expiring until revoked.

The external-availability blocker in
`data/output/java_real_api_test_20261107_042930_490532/final_test_report.md`
is superseded by this explicit operator correction. That historical report is retained
unchanged. No credential or source-file reconfirmation is required.

The operator restored 85% for the latest test. Expanded-schema accounting remains mandatory; do not dispatch a request rejected by corrected offline sizing.
