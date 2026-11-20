# Task 13 actual live result

The user explicitly authorized transmission to Groq. Three real requests were
dispatched to the configured openai/gpt-oss-120b, all pinned to organization slot
1. No other organization was used to retry rejected work. All three failed before
successful generation; no lecture chunks completed, no knowledge items or student
notes were generated. Provider usage was not returned, so token consumption is
unknown rather than zero. Existing conservative ledger reservations remain.

## Attempts retained

1. `multimodal_notes_full_multimodal-20261110_085436_074829`: HTTP 400,
   unsupported `uniqueItems` in response schema.
2. `multimodal_notes_full_multimodal-20261110_085740_952649`: HTTP 400,
   provider cannot disambiguate legacy/atomic anyOf branches with overlapping
   required keys.
3. `multimodal_notes_full_multimodal-20261110_085853_161575`: HTTP 413,
   requested 9250 tokens, provider TPM limit 8000. No 429 or credential evasion.

The provider transport now omits unsupported uniqueItems, while unchanged local
Task 12A JSON-schema validation still rejects duplicate references. It also
requires the atomic claim value form, a strict subset of the local legacy-or-
atomic schema. No fallback to the older extraction policy was made. Tests check
both invariants. Existing exact request binding was regenerated for each changed
wire payload; historical attempts were not erased or relabeled.

## Remaining blocker

The current byte-based token estimator underestimates Groq's requested tokens
for the schema-inclusive request. The third attempt was rejected at 9250 > 8000,
despite passing local estimated admission. The stricter local 85% ceiling is
6800 and must also be preserved. No further calls should be made until a revised
request-size plan demonstrates compliance using defensible schema-inclusive
accounting. Identical retries and switching keys do not repair this error.

A compatible plan may require smaller evidence-boundary chunks/output planning
and a defensible tokenizer/upper bound, or genuinely larger provider capacity
with explicit policy review. Do not raise ceilings, discard Task 12A evidence
fields, truncate source coverage or treat OCR candidates as verified to fit.
This is a technical request-size blocker, not missing user authorization.

Latest prepared inventory: 2682 units (2181 original speech segments, 501 visual
records); 306 primary chunks plus conditional recovery requests. Estimated
input 1041150, reserved output 918000 are estimates invalidated as reliable
admission sizing by the provider rejection. The full workload also exceeds one
day's combined configured 850000-token margin if those reservations were used.

## Quality and comparison

No new extraction exists to compare semantically against old notes. The latest
historical text-only run remains unchanged: 48/50 completed chunks, 458 items.
There is no claimed improvement, coverage score or complete new lecture notes.
Raw OCR candidates, mortgage VISUAL_CONTEXT_REQUIRED, conflicting Windows-path
strings and clipped retry evidence remain in the new source inventory/review
supplement. No new OCR, ASR, canonical approval or note invention occurred.

The previous regression invocation passed 32 tests. An additional atomic-wire
subset test passed along with the uniqueness preservation test. See saved run
request_audit.json, errors.json, quota_report.json and run_summary.json for actual
attempt accounting. Frozen payload manifests and separate per-run approvals are
retained. Resume cannot replay an already consumed failed operation automatically.

## Additional files changed this turn

`app/extraction/organization_extraction.py` (provider wire compatibility only),
`tests/test_groq_wire_schema.py`, this blocker report, and the two new versioned
run directories. Task 12A's local schema and evidence policy remain unchanged.
