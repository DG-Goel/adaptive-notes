# Investigation: why 85% worked before and 50% fails now

## Confirmed differences in the saved requests

| Component | Historical working request | Current rejected request |
|---|---:|---:|
| Schema name | canonical_grounded_v4 | canonical_evidence_first_12a_v1 |
| Schema compact bytes (schema only) | 3842 | 5790 |
| Schema bytes after offline local-reference expansion | 8113 | 45634 |
| System prompt characters | 3496 | 2376 |
| User prompt characters | 3416 | 1040 |
| Reserved output | 3000 | 1000 |

Source requests: `data/output/java_authorization_20261109_022409_842270/manifest.json`
and `data/output/multimodal_notes_full_multimodal-20261110_110137_669335/manifest.json`.
Both configuration records say canonical_grounded_v4, but their actual wire schema
names differ. The historical request predates the richer Task 12A wire schema.
It is not an equivalent workload tested at a different utilization percentage.

The historical first request succeeded: input_actual=3189, output_actual=598,
HTTP 200, according to its request audit. The current first request was rejected
with HTTP 413 and Requested 8636 / Limit 8000. The latter is admission sizing
reported by Groq, not actual billed usage; no usage was returned.

## Accounting defect

Task 12A adds nested per-claim refs, basis, availability, literal kind,
instructional role, related refs and abstention alternatives. The schema references
the rich `value` definition 29 times across the extraction fields. Resolving those
references makes the current schema about 5.6x the expanded historical schema.
The current compact schema conceals most of this repetition behind `$ref`.

The byte-based local estimator serialized only the compact response_format,
divided bytes by 3.5, then added output reserve. It admitted the current request
at 3805 total under the 4000 ceiling, while Groq rejected Requested 8636.
The percentages were applied to that underestimated input. Changing them did not
correct the schema-size model. The shorter current prompts and smaller output
reserve rule out simply blaming a longer transcript prompt in this first request.

Provider-internal schema expansion/tokenization has NOT been independently
observed. The offline expansion is a conservative diagnostic proxy and a strong
explanation for the observed mismatch, not proof that Groq performs this exact
transformation or counts each byte identically. GPT-OSS tokenizer equivalence,
hidden formatting and provider reservation accounting remain unmeasured.

Separate earlier errors were genuine provider schema-compatibility failures:
uniqueItems unsupported and overlapping legacy/atomic anyOf disallowed. Existing
transport changes address these while keeping the original local validation and
requiring the rich atomic form. They do not resolve schema-size accounting alone.

## Correction made in this investigation

`schema_budget_text` in `app/extraction/organization_extraction.py` now expands
internal schema references for conservative accounting, without modifying the
actual wire schema or Task 12A local validator. Recursive/external references
fail closed. This is still a byte-based estimate, not an exact provider tokenizer.

The exact request previously rejected by Groq is now rejected OFFLINE by
prepare_request before it can consume another API attempt. No live requests,
quota resets, credential switches, schema downgrades, or historical edits were
performed during this investigation. The hard 50% policy is unchanged.

13 focused tests passed: wire subset/local uniqueness, repeated-reference budget
accounting without wire mutation, recursive-reference rejection and 50% quota
boundaries. Updated files: organization_extraction.py, test_groq_wire_schema.py,
and this report.

## What remains necessary

Use a more compact provider-facing representation of the SAME evidence policy,
or evidence-bound task/schema partitions with equivalent local validation, and
validate schema-inclusive sizing before dispatch. Preserve all source inventory,
unverified OCR state, exact request authorization and the hard ceiling. Do not
silently switch back to the old weaker wire schema, reduce percentages again as
a substitute for sizing, or claim that more primary splitting alone removes
schema overhead repeated in every request.

Groq's documented structured-output modes and constraints:
https://console.groq.com/docs/structured-outputs
The documentation does not establish the internal token-accounting formula used
for these particular rejections.
