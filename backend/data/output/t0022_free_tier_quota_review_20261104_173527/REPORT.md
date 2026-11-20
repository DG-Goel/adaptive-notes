# Free Tier quota admission feasibility

Reviewed 2026-11-04. Stage A HOLD. Stage B HOLD. Release NO-GO.

## Verdict

The existing admission process is **not operationally established with the available Free Tier evidence**. No documented Free Tier surface reviewed supplies all four authoritative quota balances with the required <=15-second freshness and organization-wide completeness. This is a finding about documented capabilities and available evidence, not proof that an undocumented account feature cannot exist. Upgrading alone is not a demonstrated solution either.

Classification below concerns authoritative current usage/headroom suitable for this gate, not whether a configured ceiling can be viewed. PARTIALLY AVAILABLE means a relevant balance observation exists but cannot satisfy this complete preflight under the restrictions. UNAVAILABLE means no qualifying documented Free Tier observation was found.

| Metric | Classification | Evidence and admission gap |
|---|---|---|
| RPM | UNAVAILABLE | Configured ceiling is known, but no documented RPM balance header or qualifying fresh Free Tier usage endpoint was found. |
| RPD | PARTIALLY AVAILABLE | Response-time remaining/reset observations exist. No new response can be obtained under this task, and historical observations cannot meet the freshness gate. |
| TPM | PARTIALLY AVAILABLE | Response-time remaining/reset observations exist, with the same freshness and competing-traffic limitations. |
| TPD | UNAVAILABLE | Configured ceiling is known, but no documented TPD balance header or qualifying fresh Free Tier usage endpoint was found. |

## Official header contract

| Header | Meaning |
|---|---|
| x-ratelimit-limit-requests | RPD ceiling |
| x-ratelimit-remaining-requests | RPD remaining at response time |
| x-ratelimit-reset-requests | RPD reset information |
| x-ratelimit-limit-tokens | TPM ceiling |
| x-ratelimit-remaining-tokens | TPM remaining at response time |
| x-ratelimit-reset-tokens | TPM reset information |
| retry-after | Delay on HTTP 429 only |

Groq documents the six rate-limit headers as included on responses. Remaining headers are balances, not merely configured limits. They reserve no quota and do not establish a complete four-window preflight. Do not relabel request headers RPM or token headers TPD. The public documentation does not establish exact rolling-window algorithms sufficiently to turn these fields into a complete request history. [Groq Rate Limits](https://console.groq.com/docs/rate-limits)

## Dashboards, organization scope and other callers

Groq documents project-specific keys and usage/log views, with console selection filtering the displayed project. Organization ceilings constrain combined projects; a single project's view is insufficient. Project limits can only narrow organization limits. Separate input/output ceilings are organization-only according to the current documentation. Owners can inspect activity across projects, but the documentation provides no <=15-second freshness guarantee or exact quota-balance contract for those views. Free Tier account-specific dashboard visibility was not inspected. Thus basic usage analytics should not be described as absent, nor promoted to complete real-time quota telemetry. [Groq Projects](https://console.groq.com/docs/projects)

Other keys and applications can only be accounted for with a complete caller inventory, coordinated dispatch records and a validated baseline/window interpretation. Existing local logs cannot prove that inventory. Pausing one machine, waiting one minute, or recording zero outstanding work without evidence cannot establish daily balances. A newly captured image of stale telemetry does not refresh its data timestamp.

## Provider-supported endpoint and upgrade limits

Groq explicitly restricts its organization Prometheus/VictoriaMetrics surface to Enterprise. The documented base is https://api.groq.com/v1/metrics/prometheus with supported query paths. Published request and token metrics use five-minute rates and model/project labels. This is organization telemetry, not a documented atomic quota reservation or exact four-window headroom endpoint. It is unavailable as a documented Free Tier feature. No call was made. A Developer upgrade cannot be assumed to enable this Enterprise feature, and even Enterprise requires verification of freshness and accounting suitability. [Groq Prometheus Metrics](https://console.groq.com/docs/prometheus-metrics)

No supported general Free Tier remaining-quota, quota-reservation or complete-usage preflight endpoint was identified in the reviewed public reference. This is a documentation search result, not a guarantee that no other provider capability exists. Model-listing probes, undocumented console endpoints or inferred OpenAI-compatible usage routes are not substitutes and were not called. [Groq API Reference](https://console.groq.com/docs/api-reference)

Exact rolling-minute and daily usage without an API request is therefore **not established**. Public documentation can establish capabilities and configured policy, not this organization's present consumption. A human Console review might supply additional evidence, but cannot be assumed to meet the gate without demonstrated scope, data timestamps and window semantics.

## Local implementation and evidence

Read-only inspection covered:

- C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\admission.py
- C:\Projects\adaptive-notes\backend\data\output\t0022_stage_a_admission_v2_20261104_125816\live_stage_a.py
- C:\Projects\adaptive-notes\backend\data\output\groq_quota_runbook_20261104_004222\RUNBOOK.md
- C:\Projects\adaptive-notes\backend\data\output\groq_strict_t0022_20261103_8daaab0610db4f2f\smoke_report.json

Admission.validated_windows requires all four organization windows and applicable project/split rows. fresh checks each row independently within 15 seconds and requires traffic control for at least another 90 seconds. QuotaLedger.claim charges used, outstanding, local reservations and the proposal. These are strict operator-evidence checks, not provider telemetry acquisition. The ledger cannot observe other callers.

The revised request remains 1007 estimated input plus 4000 maximum output = 5007 tokens. Its 6800-token internal TPM ceiling leaves 1793 tokens before existing charges. That arithmetic does not establish actual headroom.

The historical smoke report records one response with 2035 input, 3944 output and 5979 total tokens. Those are individual-request usage, not organization daily usage. A filename-only search for x-ratelimit-remaining / x-ratelimit-limit in JSON/log files under data/output returned no matches. This search does not prove no headers exist in any other file format. The revised harness preserves the response body and request ID, but does not persist rate-limit headers. Even historical headers, if located elsewhere, would be stale for this admission.

The earlier runbook's conditional admission path requires actual complete evidence. It must not be read as confirmation that Free Tier supplies it. Where its wording suggests avoiding overlap in accounting, the revised code takes precedence: external counters and local reservations are deliberately charged conservatively even if overlapping. No implementation was changed.

## Recommendation

Do not create PASS records or execute Stage A. Request provider clarification through a separately authorized human support process on Free Tier quota telemetry, account window semantics, freshness and completeness. No support message was sent here. If a documented authoritative baseline plus independently complete organization-wide accounting can later establish conservative current bounds, assess that evidence under the unchanged checks; do not treat this hypothetical route as achieved. If neither provider evidence nor complete reconciliation is available, the gate remains unusable operationally on the current evidence.

Do not purchase an upgrade solely on the assumption it fixes admission. First obtain confirmation that the proposed tier exposes the exact required information. No checks should be weakened to manufacture PASS.

Only public documentation pages and local files were read. No Groq API request, probe, test, credential rotation, extraction or recovery ran. No approval/admission records were created. No production files, historical artifacts, frozen request or thresholds changed. This new report is the only added artifact.
