# Coverage-matched mocked comparison

| Path | Mock calls | Estimated input | Estimated visible output | Estimated total excluding reasoning | Compact output bytes |
|---|---:|---:|---:|---:|---:|
| Current single-stage prompt and expanded response | 1 | 2,856 | 1,157 | 4,013 | 4,049 |
| A with atomic facts | 1 | 980 | 748 | 1,728 | 2,615 |
| B with field references | 1 | 1,181 | 745 | 1,926 | 2,607 |
| A and reference B combined | 2 | 2,161 | 1,493 | 3,654 | 5,222 |
| A and full-schema B counterfactual | 2 | 2,138 | 1,905 | 4,043 | 6,664 |

Input estimates use the unchanged request estimator. Visible output estimates use ceil(UTF-8 bytes / 3.5). A and B estimates use the representative message strings in compare.py. The mock stages exchange source and fact objects directly. These are sizing estimates, with reasoning and live latency unmeasured. The full-schema B row sizes a counterfactual.

Both exercised paths produce nine items covering the same ten reference facts. The comparison expands the same reviewed annotations for the single-stage mock and checks that the strict parser returns equivalent content and evidence metadata. Thus the comparison controls coverage, duplication and semantic content by construction. It does not compare independently generated quality. Stage B’s reference format carries field-to-fact lineage before expansion. The single-stage mock carries the same quotations and field paths directly.

The two-stage fixture uses 359 fewer estimated tokens overall before reasoning, while producing 336 more visible output tokens across both calls. Its largest single completion estimate drops from 1,157 to 748. Full-schema B erases the estimated total saving. The intermediate A payload is 2,615 bytes. Different reasoning allocations could erase or reverse the estimated savings.

The existing single-stage adapter rejects a length finish before parsing. The prototype rejects length in either mock stage. Failure in A skips B. A late failure in B returns zero items even when earlier items passed. The fixture also checks missing A facts and loss of B coverage. The semantic reviewer rejects unsupported claims with otherwise valid evidence references.

## Limitations and recommendation

The hand-authored reviewer proves how to enforce reviewed scope in this fixed fixture. A novel paraphrase requires a new semantic decision. Exact normalized content catches literal duplicates. Semantic redundancy outside the reviewed fixture requires review. The reference set covers ten selected teaching points, and the all-category synthetic test exercises shape only. Mock outputs cannot establish model compliance, latency, actual token cost or reasoning savings. The prototype does not exercise shared quota admission or persistent publication.

**The design merits one separately authorized, bounded live experiment** to measure peak completion pressure and semantic coverage. Such an experiment needs a reviewed live harness, shared budget admission and an explicit allowance for up to two sequential Groq openai/gpt-oss-120b calls, with B contingent on A passing review. Judge it against the same reference coverage and preserve both stage outcomes. Release remains NO-GO.
