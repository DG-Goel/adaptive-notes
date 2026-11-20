# NOETRA infographic engine — Phase 2

Phase 2 adds deterministic source reading and context management. It does not
make segmentation decisions or implement routing, summarization, generation,
semantic verification or rendering. Phase 1 files, contracts, clients, settings,
prompts and initialization are preserved byte-for-byte. No existing application
entry point imports these additions. The feature remains disabled by default.

## Source artifacts and indexing

Inspection confirmed existing complete/partial Round 1 Markdown, polished
Markdown, Round 2 `ordered_notes.json` arrays and the frontend's sections-and-blocks
`NoteDocument` contract. Notes contain heading hierarchy, prose, nested lists,
numbered lists, math, fenced code, Markdown/HTML tables, examples, definitions,
image/diagram references, knowledge/source anchors and literal timestamps. The
ordered manifest additionally contains timing arrays, source gaps, body offsets,
visual payloads and review flags. Polished Markdown may omit provenance; missing
metadata is not invented or inferred from another artifact.

`FileSourceReader` implements the Phase 1 read-only source port using an explicit
ID-to-file allowlist. It reads bytes and computes a SHA-256 digest. It supports
UTF-8 `.md`, `.markdown`, `.txt` and `.json`. It does not load diagram images,
resolve links, execute code or rewrite a source file. Other formats fail explicitly.

`build_index(snapshot)` retains the source snapshot plus a complete ordered
partition of original text. Each immutable block contains its stable ID, sequential
position, original text, artifact ID, half-open character offsets, section path,
structural type, parent where available, content digest, conservative token
estimate, provenance, timestamps, locator and structural cohesion group.
Offsets count Python Unicode characters, not UTF-8 bytes. Reading the same snapshot
reproduces IDs and offsets. IDs bind the artifact ID, complete source digest,
index version and offsets; an edited source intentionally creates a new identity.
`index.reconstruct().encode('utf-8')` exactly reproduces the original bytes,
including Unicode, CRLF, whitespace, warnings and metadata.

Markdown is indexed by structural boundaries: ATX/setext headings, paragraphs,
fences, display math, supported LaTeX environments, whole tables and lists. Code,
equations and nested list content are retained together. Explicit adjacency
groups associate headings with content, code/math with adjacent explanations,
examples with preceding prose, qualifications with their preceding block, and
NOETRA anchors with preceding content. These are syntactic heuristics, not claims
of semantic correctness. Explicit trailing anchor metadata is copied to its
cohesive content without changing the original text.

JSON indexing retains exact original object slices, including all unknown fields,
and separate structural-envelope slices. Ordered note objects are addressable by
array pointer; structured document blocks carry section hierarchy and JSON pointers.
JSON source text is never regenerated or replaced with a new notes format. Original
escaped text remains part of its original serialized object. Existing body offsets
inside JSON remain intact; index offsets refer to the JSON artifact itself.
Nested list/diagram/table payloads stay inside their original object. Unsupported
JSON schemas and duplicate object keys fail explicitly.

`subdivide(index,budget)` can divide an oversized list at complete top-level item
boundaries, retaining nested items and parent IDs. Original blocks remain in
`index.blocks`; request leaves live in `index.units`. The first child keeps its
heading association. Oversized paragraphs, equations, code, tables, JSON objects
or individual list items have explicit unsupported-block records. They are not
silently truncated, summarized or split at arbitrary character/token positions.
`StructuralSourceIndexer` adapts exact blocks/evidence to the original Phase 1
`SourceIndexer.index()` signature. Rich index metadata stays in `SourceIndex`.

## Provider-independent budgeting

`TokenBudgetManager` accepts explicit positive input/output limits and an optional
shared context limit. `ModelLimits.from_client(settings, metadata)` combines the
existing Phase 1 client ceilings with available `ModelInfo`. With no metadata,
offline configured ceilings may be used, marked **unverified**. Hosted model input,
output and configured shared limits remain distinct. No advertised model context
or unverified free-tier quota is substituted for account metadata.

`ContextConfig` defaults:

| Setting | Default |
| --- | --- |
| target_source_tokens | 10000 |
| max_source_tokens | 16000 |
| lookahead_tokens | 1500 |
| previous_context_tokens | 500 |
| reserved_output_tokens | 3000 |
| thinking_tokens | 0 |
| safety_margin_ratio | 0.10 |
| framing_tokens | 256 |
| max_no_progress | 3 |
| expansion_factor | 1.5 |

The response target is reduced if the effective output limit requires it; thinking
allowance is deducted separately and cannot consume the entire output budget.
Callers must use the reported effective response/thinking allowances when forming
future API requests. Defaults are adjustable local targets, not provider guarantees.

Input capacity is the smaller of the input ceiling after its safety margin and
the shared ceiling after its safety margin, response reservation and thinking
allowance, minus framing. All final serialized request text is counted. Reports
separately expose system instructions, caller-supplied segmentation prompt,
request metadata, previous context, primary source, lookahead, full serialized
input, output, thinking and both safety margins. Counts for tokenizers are not
assumed additive: the full request count governs admission.

The default offline counter conservatively uses UTF-8 byte length. Source blocks
and budget reports label estimates and methods explicitly. A supplied local
`TokenCounter` may report measured counts for a known tokenizer; the code does
not automatically invoke any provider token-count endpoint. When limits derive
from a Phase 1 client, a byte-bound and at least 256 framing tokens are additionally
enforced to match its unchanged admission behavior even with a measured counter.
`session.preflight(final_payload=..., provider_metadata=...)` rechecks the final
wire content and optionally newer metadata. It returns evidence, not submission
authorization. An unverified report remains unverified; Phase 1 still requires
explicit model verification before actual completion calls.

## Reading windows and decisions

Every window serializes three separate regions with explicit ownership labels:

- **A:** committed read-only blocks, or a caller-supplied read-only context summary.
- **B:** contiguous commit-eligible source beginning at the current cursor.
- **C:** contiguous upcoming lookahead, excluded from commit eligibility.

Windows are built by whole structural groups and checked against the complete
serialized budget. Source targets shrink under effective API limits. A small
initial target may grow to fit one cohesive group within the maximum. Previous
context can be omitted to admit source; an oversized supplied summary is rejected
instead of truncated. If needed, a complete trailing B group yields to C to keep
lookahead within budget. An atomic/group constraint can leave C empty; the ready
result explicitly records when forward context is unavailable. A final B range
reaching the document end has no forward source.

`next_window()` performs no commitment. A `BoundaryDecision` must cite the matching
active window and a B block ID; `apply()` commits exactly the contiguous prefix
through that ID. Optional pending IDs must name the first remaining B block.
Lookahead, previous context, unknown IDs, stale windows and replayed decisions are
rejected without changing state. A partial commit leaves the next block as the
next cursor; remaining source is carried forward. Final-document windows do not
complete processing until a validated decision commits every reading unit.

No-progress decisions track consecutive counts and repeated pending boundaries.
The next target grows by a bounded factor, never beyond the maximum. If the next
window cannot expose more primary source, or the configured retry count is reached,
the state returns `oversized_concept` or `forced_boundary_required`. It stops
offering automatic windows and retains every uncommitted block. A future explicit
decision handler may request `allow_forced_boundary=True`; this flag itself commits
nothing and makes no semantic split decision. An unsupported atom returns no
request window at all. `restart()` explicitly creates a fresh session while
leaving the old state unchanged; use a new run ID for separately persisted work.

The coverage ledger accounts for original blocks, subdivided reading units,
committed/uncommitted ranges, A/C blocks, pending range, cursor, partially committed
parents and unresolved oversized blocks. Its complete status means **source-range
coverage**, not semantic fact coverage.

## Persistent recovery

`SQLiteCheckpointStore` implements Phase 1 `CheckpointStore.append/latest`. It owns
only `backend/data/infographics/source-reading-checkpoints.sqlite3` by default.
Construction is lazy; storage is created only on an explicit append. A separate
namespace may be supplied for tests or deployments. Paths must not traverse
symlinks/junctions. The adapter refuses an unrelated database. It never connects
to an existing NOETRA database or modifies its schemas.

`ReadingCheckpoint` extends the original immutable checkpoint envelope with
versioned reading state. It records source identity/hash, index version/fingerprint,
cursor, committed/pending ranges, window/budget configuration, status and no-progress
counters. It saves no keys, provider client, prompt text or source text. The
public request configuration is bound by a hash and must be supplied again to resume.

Revisions append atomically in SQLite transactions. Older revisions are immutable
through this API. Duplicate saves are idempotent. Parent checkpoint IDs and range
history reject stale writers and accidental rewinds. Interrupted transactions
recover the latest complete revision; malformed/checksum-incompatible revisions
fail explicitly. A run must have one coordinated decision writer. Resume rereads
the original artifact and rebuilds its index; changed source, configuration,
token-count method or index version invalidates the checkpoint. No fallback to an
older incompatible source or silent reset occurs.

## Explicit offline integration

```python
from pathlib import Path
from app.infographics.source_index import FileSourceReader
from app.infographics.token_budget import ModelLimits
from app.infographics.reading import prepare_reading

reader = FileSourceReader({'lecture': Path('/path/to/generated_notes.md')})
session = prepare_reading(
    reader, 'lecture',
    ModelLimits(input_tokens=16000, output_tokens=2000, shared_context_tokens=16000),
    environment={'NOETRA_INFOGRAPHIC_ENGINE_ENABLED': 'true'},
)
result = session.next_window()  # No API call and no commit.
```

The numbers above are explicit offline configuration examples, not verified API
limits. Production callers should use verified Phase 1 model metadata. An absent
or false flag makes `prepare_reading()` return before reading the source or
importing index, window or persistence modules. Enabled offline Phase 2 does not
require or construct any API client. It creates no checkpoint automatically.
No existing app startup, frontend, worker, API route or notes workflow is connected.

## Completion evidence and file inventory

Initial Phase 2 regression baseline: **104 tests passed, 7 subtests passed**.
See the final verification below. This work adds these files only:

| File | Purpose |
| --- | --- |
| `backend/app/infographics/PHASE2_BASELINE.json` | Pre-edit integrity snapshot |
| `backend/app/infographics/source_index.py` | Immutable source reader/index and safe subdivision |
| `backend/app/infographics/token_budget.py` | Explicit limits, token counts and complete request admission |
| `backend/app/infographics/reading_windows.py` | Three-region windows, boundary state machine and ledger |
| `backend/app/infographics/checkpoints.py` | Independent atomic checkpoint persistence |
| `backend/app/infographics/reading.py` | Disabled-first offline entry point |
| `backend/app/infographics/PHASE2.md` | Architecture, usage, validation and limitations |
| `backend/tests/test_infographics_source_index.py` | Source structures, identity and losslessness tests |
| `backend/tests/test_infographics_reading_windows.py` | Budget, ownership, progress and accounting tests |
| `backend/tests/test_infographics_checkpoints.py` | Recovery, isolation and real-artifact integration tests |

No existing file was modified, including every Phase 1 file. Additions outside
the infographic module are limited to its three new test files. No dependency,
environment file, original notes, existing configuration or database schema changed.
The original Phase 1 context-selection protocol remains reserved for future
segment-level work; Phase 2 adds richer source/window types beside it and uses
the original source-reader, source-indexer adapter and checkpoint boundaries.

Git metadata is still unavailable. The new baseline covers 1,892 existing files:
source/config/docs outside dependency/runtime/cache trees, plus all 855 existing
generated/partial/polished Markdown and ordered JSON artifacts found under
`backend/data`. The original 1,022-file Phase 1 baseline is retained and rechecked.
These snapshots do not hash every media/cache/database/runtime file.

### Final verification

- **225 tests passed, 7 subtests passed**, including all 104 Phase 1 baseline cases
  and 121 new Phase 2 cases. This is the selected relevant regression suite,
  not a claim that the entire repository suite was run.
- New tests cover short/empty/large and multilingual notes, Unicode/CRLF offsets,
  headings, math, fences, tables, lists, JSON metadata, exact reconstruction, stable
  IDs, source hashes, safe subdivision, oversized atoms, measured/estimated budgets,
  hosted input/output limits, missing metadata, A/B/C ownership, carryover, invalid
  and replayed boundaries, bounded no-progress, completion accounting and restart.
- Persistence tests cover deterministic partial-commit resume, full-document
  recovery without duplicate ownership, no-progress recovery, incompatible source,
  configuration/token-counter changes, schema/state corruption, stale writers,
  idempotent saves and interrupted-transaction rollback.
- Disabled-entry tests prohibit source reads, network and directory creation and
  verify that index, SDK, checkpoint and worker modules are not imported. Enabled
  offline preparation works without API credentials and with network forbidden.
- The real existing backend was imported in a separate process with all three
  dedicated API keys removed and the flag false. Its existing video-list function
  returned normally, no worker threads started, and no infographic module was
  imported. Network connections and subprocess dispatch were forbidden by an audit
  hook. This was an import/read-function smoke check, not an HTTP/browser test.
- All **855 existing note artifacts** were separately indexed and reconstructed
  byte-for-byte: 717 complete Markdown, 107 partial Markdown, 14 polished Markdown
  and 17 ordered JSON manifests, totaling 33,632 original structural blocks.
  No corpus artifact failed indexing or exact reconstruction. This establishes
  losslessness; it does not claim every atomic block fits every possible API budget.
- Both integrity snapshots matched: **1,892 Phase 2 baseline files unchanged**
  and **1,022 Phase 1 baseline files unchanged**, including all Phase 1 implementation
  and test files and the 855 note artifacts in the Phase 2 snapshot.
- Added Python files passed syntax parsing and added-file whitespace diff checks.
  No live model/token-count/generation request or new background job ran. No
  frontend build was needed because its source, dependencies and configuration
  remained unchanged; frontend behavior was not newly browser-tested in Phase 2.

Reproduce the regression selection from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_infographics_foundation.py tests/test_infographics_source_index.py tests/test_infographics_reading_windows.py tests/test_infographics_checkpoints.py tests/test_round2.py tests/test_round1_quiz.py tests/test_gemini_provider.py tests/test_rendering_simple.py tests/test_serialization.py tests/test_transcription_stage1.py tests/test_transcription_risk.py -q --disable-warnings
```

### Known limitations

- Structural adjacency is heuristic and deliberately performs no semantic split,
  source truth check or hallucination/coverage verification. Unrecognized Markdown
  syntax remains original text rather than becoming a complete CommonMark AST.
- JSON source blocks are exact serialized objects/envelopes. Very large objects
  are atomic; this phase does not split inside escaped strings, code, equations,
  tables or nested list items. Some sources therefore require an explicit future
  boundary decision or different budget instead of automatic processing.
- UTF-8 byte estimates and per-block metadata can underuse real token capacity.
  Measured token counts are only as authoritative as the supplied tokenizer.
- In-memory sessions are single-writer objects, not thread-safe distributed
  orchestration. SQLite checkpoints prevent stale saves but do not dispatch jobs.
- SQLite atomicity assumes a local filesystem with SQLite's supported locking.
  No network filesystem, distributed persistence or power-loss fault injection
  was tested. Filesystem race hardening against a hostile local actor is outside
  this local operator-controlled namespace model.
- No live model metadata, LLM request, semantic segmentation, visualization
  generation or AntV rendering was performed in this phase.
