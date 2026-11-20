# Task 13 request-size and integration repair

## Active production path

`category_bounded_12a_v1` sends one knowledge category per request, with native
Task 12A field objects including text, refs, atomic claims, basis, availability,
literal kind, instructional role and correction refs. It reconstructs the eight
category container arrays mechanically and applies the unchanged original
canonical resolver and local JSON schema. This is a source/task partition, not
a return to the historical weaker schema. All eight categories are scheduled
over the full source by `run_full_multimodal_categories.py`. Existing renderer
and representation selection determine which of nine note representations are
actually supported. Source-only fields are never fabricated to fill a category.

The original rich schema expanded to approximately 45 KB because the same rich
value definition was referenced throughout every category's fields. Corrected
budget accounting expands schema refs conservatively. Category partitioning
reduces that repetition without requiring the model to maintain an extra claim
ID table. Earlier table/row transports remain experimental, with their raw
attempt artifacts retained; they are not the preparer's active default.

`multimodal_source_v2_bounded_speech` groups consecutive speech into bounded
passages (at most 250 words; sentence-end preference after 160 words). It keeps
every original segment object, original start/end/words/probabilities and exact
character-span mapping in provenance. Unit text adds only newline separators;
segment strings are unchanged. All 501 visual records remain separate,
unverified, nonquotable sources linked to their owning speech passage. No Stage
1/2/3/3.1/4 artifact is rewritten. Source IDs and ingestion fingerprints change
only in the new adapter's versioned source document.

The active hard quota is 85%, capped at RPM 25, RPD 850, TPM 6800, TPD 170000
per verified organization. Every changed payload has a new manifest and exact
credential/request binding. No SDK retries, random key rotation, uncertain-charge
clearing, schema fallback or unverified OCR promotion was introduced.

## Ledger lifecycle repair

A historical local reservation failed expected-payload authorization before
physical dispatch, but its attempt was left `completed=NULL,category=NULL`.
That made a 6591-token reservation occupy the minute window indefinitely.
There was no dispatch timestamp, no HTTP status and no shared Stage A claim;
the durable operation already recorded authorization failure and completion.

`close_undispatched` accepts only completed failed/validation_failed operations
with no dispatch, status, category or completion on the attempt, and refuses
repair during an active operation. The repaired attempt is marked not_dispatched
at its original operation completion time. The full 6591 charge and original
reservations are PRESERVED, as is the entire audit history. No actual dispatched
or uncertain attempt is released. `finish` now closes this same pre-dispatch
lifecycle automatically for future authorization failures. Tests verify both the
retained charge and refusal to repair dispatched uncertainty.

## Real validation and current run

Native category-bounded requests have passed Groq's size/schema admission and
produced real knowledge items. The first facts checkpoint had 11 knowledge
items; a later two-checkpoint snapshot had 21 items. Partial previews are built
only from durable successful real checkpoints using the existing note quality
pipeline, and are clearly labeled incomplete/unverified. A response passing
mechanical checks is not a human semantic approval.

The complete invocation may still stop at existing quota/provider gates. Do not
describe an incomplete category or a partial parent run as complete lecture
notes. Per-category failures, truncations, saved responses, usage, checkpoint
IDs and exact source documents remain under their independent output folders.

Start or resume the complete orchestration from backend:

```powershell
& .venv/Scripts/python.exe run_full_multimodal_categories.py
& .venv/Scripts/python.exe run_full_multimodal_categories.py --resume data/output/EXISTING_PARENT_DIRECTORY
```

Parent `category_runs.json` records the exact per-category directories. Resume
reuses those manifests/checkpoints and does not invent new request IDs to retry
failed operations. Confirmed truncations use pre-authorized children on the
same organization. Other confirmed validation failures stay unresolved while
independent primary work may continue. Quota/uncertain/authorization HOLDs stop.

## Tests and files

35 focused/end-to-end tests passed for category-native schema preservation, original local
resolver, missing/unknown evidence rejection, all eight category schemas,
multimodal passage/provenance integrity, pre-dispatch lifecycle repair and 85%
quota boundaries. Earlier runner/checkpoint tests passed for compact transport;
The native-category end-to-end case covers five-slot rotation, checkpoint resume,
and saved-response recovery without redispatch. Additional orchestrator checks
enforce quota stops even on the final primary's recovery child and stop mixing
different source/adapter bindings across passes.
legacy native multi-category planning tests that assumed the old underestimated
schema budget are not evidence that the new large schema fits. Experimental
codec tests remain separate from production path validation.

Active added files: app/extraction/category_wire.py,
run_full_multimodal_categories.py, publish_multimodal_progress.py,
tests/test_category_wire.py, tests/test_undispatched_lifecycle.py and this guide.
Also retained experimental files: compact_claim_wire.py, field_row_wire.py,
typed_claim_wire.py and their tests. Existing files updated:
organization_extraction.py, organization_scheduler.py, multimodal_adapter.py,
prepare_multimodal_run.py, document_authorization.py, source_context.py and
corresponding adapter/runner tests. Historical source, response, authorization,
credential and quota artifacts were not overwritten; the sole ledger lifecycle
repair added an audited closure while retaining the full historical charge.
