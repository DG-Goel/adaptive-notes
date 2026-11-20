# Output-token analysis

| Measurement | Previous compact test | Latest repaired test |
|---|---:|---:|
| System/user characters | 2566 / 4783 | 4179 / 4783 |
| Actual input tokens | 1572 | 1919 |
| Computed output allowance | 4000 | 4000 |
| Actual completion tokens | 3611 | 4000 |
| Reported reasoning tokens | 2174 | 2398 |
| Non-reasoning remainder by subtraction | 1437 | 1602 |
| Finish | stop | length |
| Final JSON characters | 6152 | 6306 |
| Returned objects | 15 | 21 |
| source_evidence serialized characters | 2711 | 3348 |
| Total/distinct quotation characters | 1557 / 1199 | 1582 / 998 |
| source_unit_ids serialized characters | 135 | 378 |
| content serialized characters | 1136 | 0 |

Raw provider completion_tokens_details reports reasoning_tokens. Installed groq/types/completion_usage.py describes this as a completion breakdown. Reasoning used 59.95% of the latest allowance. The remaining 1602 is a subtraction-based non-reasoning completion remainder, not an independently tokenized final-JSON count. No reasoning text is reproduced here.

Confirmed: the response hit the 4000 cap and finish_reason length even though JSON parses. A valid closing brace does not prove complete extraction. The final JSON lacks formulas/procedures/relationships keys; absent empty categories alone is not proof of missing facts, but missing explicit teaching facts and length establish that completeness is unverified.

Largest measured output field group: source_evidence, 3348/6306 or about 53.1% of final JSON characters. Its 23 entries contain 1582 quotation characters plus source IDs, paths and structure. Quotation characters exceed the distinct-string total by 584; this indicates repetition, not 584 guaranteed removable characters. Several one-name operator concepts repeat the same list quotation. Ten concepts and four definitions amplify object/evidence overhead.

The wrong scheduling ID is 14 characters versus 5 for T0022. Across 21 source_unit_ids values and 23 evidence source_id values, it adds 396 characters relative to canonical IDs. This is a measurement, not authorization to mutate the saved response or fix provenance by blind replacement.

Repeated instructions consume input tokens. They can influence reasoning and compliance, but these two runs cannot prove that prompt growth caused the additional 224 reasoning tokens. Both outputs already allocate about 60% to reasoning. Fragmentation is an avoidable contributor, not the sole proven cause. Missing required content artificially reduced response size; a compliant version would need additional content and evidence paths.

Exact per-field token attribution is unavailable without a verified model tokenizer/provider breakdown. Measurements are compact-JSON characters; nested sizes must not be double-counted. Actual totals are provider usage. No tokenizer is downloaded. Preserve the existing budget and 4000 computed allowance; do not change reasoning configuration, model/provider, or increase allowance to conceal exhaustion.
