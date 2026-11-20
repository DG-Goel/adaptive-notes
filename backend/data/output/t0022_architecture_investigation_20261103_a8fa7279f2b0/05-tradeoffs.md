# Architecture comparison

| Dimension | Current single stage | Proposed two stages |
|---|---|---|
| Model calls per successful chunk | One | Two sequential calls to the same Groq model |
| Input | Source and full category/evidence contract | A reads source and a narrow contract. B rereads validated facts and the structuring contract. |
| Completion pressure | Reasoning, discovery and fully expanded evidence compete in one completion | A omits category and pointer work. B can emit compact fact references. Each stage can still exhaust its own allowance. |
| Total token cost | Latest observed 5,979, a failed run | Sum of both prompts and completions, including both reasoning allocations. Lower per-call pressure can coexist with higher total use. |
| Latency | Latest provider total 8.363 s, excluding local review | Sum of A and B time plus local validation and any rate-limit wait. No measured estimate. A failure avoids B. |
| Evidence traceability | Quotes copied directly for each item and field | Immutable fact IDs trace fields to original exact excerpts. Resolver adds a mapping boundary to validate. |
| Semantic failures | Inference, omitted facts, broad scope, invented excerpt and duplicates occur together | A can omit or overstate a fact. B can broaden a valid fact or join unrelated events. Each error can be attributed to a stage. |
| Recovery and atomic acceptance | Reject the response at a failed gate | Keep validated A as diagnostic state if B fails. Publish no partial final items. |
| Budget | One request checked against existing policy | Each complete request uses that policy. Sequential execution alone does not clear the rolling TPM window. |

A per-stage improvement requires both completions to fit, including reasoning. A total completion saving requires completion_A + completion_B below the chosen single-stage comparator at equivalent supported coverage. The observed 3,944 is a failed baseline, so beating it by omitting facts would prove little. Two calls can move the original final JSON burden into B and add A overhead. References resolved locally remove repeated literal evidence from B by construction, but the size of the savings and the effect on reasoning are unmeasured. The 2,404 serialized evidence characters in the current response are an overhead indicator, not a predicted token saving.

The current budget calculation sizes each request, and rolling usage is tracked separately. A future orchestrator must account for both requests under the same credential and quota window using existing policy. Two individually safe allocations may exceed the shared window. Neither concurrent dispatch nor independent counters would establish safe admission.
