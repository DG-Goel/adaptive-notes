# Task 13 multimodal extraction

Prepared run:
`data/output/multimodal_notes_full_multimodal-20261110_085436_074829/`.

Source adapter is opt-in through router parser options
`{"multimodal_stage4": true}` for Stage 4 JSON. Existing TXT and Docling branches
retain their behavior. Source units preserve 2181 speech segments, 501 visual
records, actual PTS, image/crop hashes, raw candidates, repeated-reading links,
model metadata and unresolved gaps. Visual text is null and nonquotable: the
existing quote catalog cannot authorize it as literal evidence. Unique candidate
readings accompany primary chunks as explicitly nonquotable limitations. Repeated
readings refer to their existing evidence record. The review supplement retains
every candidate and alternative, rather than reconstructing code or equations.

The adapter checks Stage 4 lineage, original record/index references and image
hashes. Speech source IDs and visual IDs are independent and deterministic. All
source units remain in inventory. Split leaves containing only unverified visual
material remain pending inventory, not empty provider extraction requests.
The approved manifest uses existing lossless output splitting and exact payload
hashes with Task 12A canonical_grounded_v4 schema, json_schema, temperature 0,
low reasoning, 3000 output-token reserve and zero SDK retries. No schema fallback.

## Current status

Live execution was rejected before process launch by automatic approval review:
the review could not establish explicit authorization for this specific multimodal
payload and external Groq destination from the trusted transcript. An explicit
confirmation is pending in the chat. No indirect workaround was attempted.
Zero Groq requests, no provider token usage and no newly generated knowledge
items or lecture notes. Prepared files are preflight artifacts, not a completed
or simulated notes-extraction result.

338 primary chunks, 1673 contingent source-bound recovery requests; estimated
input 1,151,725 tokens, reserved output 1,014,000. Estimates use the existing
conservative byte estimator and include strict schema/prompt overhead; not a
verified tokenizer or a prediction that all reserved output will be used.
This exceeds the five organizations' combined configured daily 85% ceilings
(850,000 tokens). Full-run dispatch must stop/resume when any assigned org is
on HOLD; no key switching, reservation clearing or ceiling increase is allowed.
External usage is unknown; the approved policy uses local tracked totals and
does not demand a new external capacity measurement. The captured local ledger
snapshot had no current daily charges/active claims, not proof of zero external
usage. Ownership/bindings were checked without printing or copying credentials.

Current configured model: openai/gpt-oss-120b. The wrapper delegates dispatch,
checkpoints, saved-response recovery, quota accounting and nine-representation
rendering to the existing authorized runner. Output directory is a new optional
argument; legacy output behavior is unchanged. Existing Stage A/B exact-type
gates, shared ledgers, 85% ceilings and provider error rules remain in place.
Every actual dispatch must separately pass those checks even after permission.

After the external approval blocker is resolved, resume from backend:

```powershell
& .venv/Scripts/python.exe run_multimodal_notes.py --live
```

The immutable request manifest/approvals belong to this source and do not reuse
historical java.txt authorization. Do not rerun the preparer just to evade an
existing operation failure or HOLD. A fresh independent run, if desired, is
prepared with `prepare_multimodal_run.py`. No provider calls occur during prepare.

## Validation and comparison

31 tests passed across tests/test_multimodal_adapter.py,
tests/test_document_authorization.py and tests/test_authorized_runner.py.
Coverage includes new-source integrity/nonpromotion and existing exact request
authorization and resumable runner behavior. New adapter tests also verify every
original speech string/timestamp, all 501 candidates, duplicate-reference content
identity and mortgage availability preservation. No mocked execution was passed
off as a real run; tests are explicitly offline.

Latest historical text-only result is partial: 48/50 chunks, 458 knowledge items.
No full result was found among the authorized java_live_* summaries. Old artifacts
are unchanged. New-vs-old quality, examples, formulas, readability and improvement
cannot be measured before new extraction. Comparison JSON states this explicitly.

Files added: app/ingestion/multimodal_adapter.py, prepare_multimodal_run.py,
run_multimodal_notes.py, tests/test_multimodal_adapter.py, this document and the
new versioned run directory. Files changed: app/ingestion/router.py (explicit
opt-in JSON adapter only), app/extraction/document_authorization.py
(multimodal-only nonquotable leaves), run_authorized_java.py (optional output_dir).
Task 12A prompts/schema, historical source/extraction/authorization artifacts,
Task 11's Docling parser, quota records and credentials were not edited.

An additional full request-hash audit initially reported 17 mismatches because
the audit command incorrectly read UTF-8 JSON using Windows' default encoding.
This was an audit error, not changed provider payloads. The corrected bytes-based
audit verifies all 2011 request/credential bindings. Preparation now also checks
persisted JSON bytes. A defensive deep-copied JSON snapshot before hashing
preserves immutable request payloads. Earlier undispatched preparation directories
are superseded by the latest pointer; no failed provider work was relabeled.
