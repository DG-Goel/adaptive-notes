# Source-faithful multimodal transcript

Stage 4 is an offline, standard-library alignment and serialization layer.
It performs no OCR, ASR, network/model invocation, source replacement or note
generation. Run from `C:\Projects\adaptive-notes\backend`:

```powershell
& .venv-transcription/Scripts/python.exe multimodal_transcript.py --output data/transcriptions/video_stage4/my_new_version
& .venv-transcription/Scripts/python.exe -m unittest discover -s tests -p test_multimodal_transcript.py -v
```

Outputs under `data/transcriptions/video_stage4/run_20261110/`:
`multimodal_transcript.json`, `multimodal_transcript.md`,
`visual_evidence_index.json`, `unresolved_source_gaps.json`,
`integration_report.md`. Existing output directories are rejected.

## Alignment and fidelity

All 2181 speech segment objects, including text, fractional times, words and
diagnostics, are copied unchanged. A chronological timeline references these
objects and each visual evidence record. Actual frame PTS is used for alignment
to half-open speech intervals [start,end). No temporal padding, nearest speech
assignment or timestamp invention. The 26 visual records in speech gaps remain
explicitly unassigned; the Markdown still places them at their own timestamps.

501 visual records preserve both historical failed attempts, the successful
changed-task retry, raw outputs, image/crop metadata and hashes, original model
metadata, execution status and exact source-artifact/index provenance. Source
paths and exact-byte fingerprints are in the evidence index. Original images
and inference derivatives are hash-verified. Historical input fingerprints are
checked against Stage 2, Stage 3 and cleanup lineage, and rechecked after writing.
Model responses/token contexts are not duplicated into Stage 4; the immutable
source artifact and record index identify their complete original response.

188 exact repeated task/output readings use display references to their first
chronological occurrence. All occurrences remain in JSON. No punctuation,
backslash, capitalization, whitespace or line-break normalization is applied.
Different tasks retain separate evidence. Different-time text changes preserve
observed states; they are never assembled into a complete program or equation.
Existing Stage 2 correction links are retained without inferring correctness.

Same-frame `String message` lines with differing characters are explicitly
unresolved character conflicts. Other differing same-frame outputs are potential
divergences (crop coverage/formatting may explain them); no winning reading is
selected. Differing timestamps alone do not establish conflicting characters or
an instructor correction. This intentionally conservative comparison is not a
semantic equivalence checker and can miss conflicts with different line layout.

Speech is LITERAL_SPEECH. OCR is always UNVERIFIED, with canonical approval false.
Ambiguous readings are labeled. Recognizable descriptive prose is tagged as
possible MODEL_INTERPRETATION; this lexical tagging cannot identify every model
interpretation. The policy explicitly forbids interpreting any unclassified OCR
prose as verified literal source content.

## Important unresolved sources

- Mortgage stays VISUAL_CONTEXT_REQUIRED. No complete equation reconstructed.
- Windows path remains unverified; broad/single-line competing backslash
  readings remain traceable, without selecting or correcting a string.
- Successful changed-task retry remains alongside historical errors; clipped
  monthly-interest characters remain unresolved. The older failed formula
  request is not relabeled as successful simply because text recognition worked.
- All 40 HIGH events have nonempty successful OCR candidates at actual event
  times. That means candidate availability, not verified source completeness.
  Every event retains an unverified/required-context status. No OCR is approved.

The gap index contains 241 items, including potential same-frame divergences,
execution issues and explicit historical limitations. This is not a count of
confirmed source errors. The machine representation is designed for future
Source Unit ingestion to consume candidate evidence and gap records separately;
no canonical-source integration or schema changes were made.

## Validation and files

Six offline tests passed: half-open timestamp alignment and gaps; unchanged
speech/dedup/chronological edits/correction links; unresolved character conflicts;
missing formula and retry history; provenance and bad image integrity; source
fingerprint rejection. The real output also passed checks for exact equality of
all speech segments to Stage 1, sorted timeline, unique evidence IDs and zero
canonical approvals. Production run verified source and image hashes; runtime
was about 0.82 seconds including reads, image hash checks and output writes.

Added `multimodal_transcript.py`, `tests/test_multimodal_transcript.py`, this
guide and the five Stage 4 output files. No existing Stage 1/2/3/3.1 artifacts,
Task 11/12A, authorization, quota or credential files were changed. No dependency
was installed. Future consumers must preserve verification status and unresolved
gaps and independently review source images before promoting exact characters.
