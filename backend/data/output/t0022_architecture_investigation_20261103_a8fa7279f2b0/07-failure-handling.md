# Failure and publication

| Gate | Outcome |
|---|---|
| A transport failure, length finish, malformed JSON or invalid raw shape | End the attempt, preserve diagnostic data, publish zero and skip B. |
| A foreign ID, stitched quote, missing required value or rejected semantic review | Preserve rejection diagnostics, skip B and publish zero. |
| A passes, B fails preflight or execution | Keep immutable A and B diagnostics. Publish zero and record the failed stage. |
| B invents an ID, drops required evidence, uses invalid pointers or produces an invalid expanded contract | Reject the entire B output. Keep A available for a separately authorized review. |
| B semantic review detects an unsupported claim, lost qualification or missing required teaching fact | Withhold publication and record the exact item/field and source gap. |
| Both stages pass all required gates | Publish one final chunk result and preserve lineage to the source and validated A snapshot. |

Use a stage-specific diagnostic record with source/message hashes, usage, finish reason, stage disposition and zero-or-final publication counts. Keep diagnostic artifacts separate from accepted knowledge. An immutable A snapshot prevents accidental references to a different source or run. Publication should be idempotent by run and chunk and occur only after all checks complete. Future recovery would require separate authorization against the original snapshot and a fresh budget check. This investigation proposes no retries, fallback, key rotation or automatic salvage.
