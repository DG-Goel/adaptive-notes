# Root-cause table

| Area | Classification | Evidence | Minimal response |
|---|---|---|---|
| Source identity | Confirmed observation; likely prompt/model cause | T0022 survives locally; response uses header scheduling ID everywhere | Explicit canonical allowlist; non-citable scheduling label; no mapping fallback |
| Stale input/serialization defect | Not supported | Source bytes, roundtrip, source marker and wire messages match | No ingestion, chunker or serialization changes |
| Missing content | Confirmed observation; likely shared/subtype contract salience | All raw objects omit content despite shared requirement/example | Category lines explicitly inherit COMMON fields |
| Strict raw contract | Confirmed code-level gap | Constructors default content before mechanical validation | Strict-only preconstruction required-field check; preserve legacy defaults |
| Output exhaustion | Confirmed | 4000 completion tokens; length; 2398 reasoning tokens | Reject truncation; reduce unnecessary duplication, not increase allowance |
| Longer instructions cause extra reasoning | Possible, unproven | Prompt +347 actual tokens and reasoning +224 across two runs | No causal certainty or provider-setting change |
| Output overhead | Confirmed contributor | 21 objects, 23 evidence entries, repeated quotes/labels, 3348 evidence characters | Careful semantic consolidation and genuinely shared quote entries |
| Missing errors/repair | Confirmed gaps; likely exhaustion/front-loading/compliance | Full source; facts missing; output ends after first fact | Source-fact inventory before category allocation; preserve separate errors |
| PI alias/circular definition | Confirmed semantic defects | Instance name becomes concept alias; instance wording becomes pseudo-definition | Explicit synonym support; scoped instance facts |
| Evidence rejection | Confirmed offline failure, not original first failure | Original stops at length; offline rejects all 21 | Keep validators and distinct generation/mechanical/semantic diagnostics |

A single run cannot establish one exclusive root cause. Structurally valid JSON is not schema compliance, completeness or semantic faithfulness.
