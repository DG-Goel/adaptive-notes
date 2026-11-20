# NOETRA infographic engine — Phase 1 completion

Date: 20 November 2026. Scope: independent foundation only; disabled by default.

## Repository inspection and integration decision

The workspace contains a React/TypeScript/Vite frontend in `NOETRA` and a Python
backend in `backend`. No applicable `AGENTS.md` was found in these project trees
or their workspace ancestors. The frontend uses React Query, API service adapters,
mock support and endpoint configuration. Current block-based notes include
Markdown, math, code, tables, flowcharts, diagrams and other structured blocks.
`NoteBlockRenderer` code-splits React Flow-based flowchart/diagram components and
uses error boundaries. Markdown/KaTeX/highlighting/table systems remain untouched.

The operational backend entry point `video_notes_jobs.py` uses a local HTTP server,
a single-worker `ThreadPoolExecutor`, file-backed job status and subprocess stages.
It serves videos, notes, quizzes and visual assets; tutor requests delegate to the
separate Universal-AI-Tutor service. That service has its own ingestion/RAG and
vector-store setup. No new HTTP route, worker or frontend integration was added.

Lecture processing spans transcription/risk/OCR, multimodal integration, authorized
Round 1 extraction, Round 2 visual planning/rendering and polishing. Round 1 stores
complete `generated_notes.md` (or `partial_notes.md`), `extraction_results.json`,
`source_document.json` and related review/gap/checkpoint files. Notes carry knowledge
IDs/source anchors. Video job directories live under `backend/data/output/video_jobs`;
later stages also maintain ordered JSON manifests and polished Markdown. The new
source contracts retain immutable bytes, source hashes and evidence offsets;
there is no importer or writer into existing lecture folders in this phase.

Existing provider abstractions in `app/extraction/llm_provider.py` include Gemini,
Groq, OpenAI and other providers. Existing Gemini reads `GEMINI_API_KEY` and lazily
uses `google.genai`; existing Groq organization admission uses separately authorized
credentials, SQLite reservations and quota policy. Those clients and policies were
inspected and are not imported, reused or changed by the new module. Existing
operator scripts use `dotenv_values`; the new package accepts a mapping or process
environment without loading files or mutating global environment.

Current execution uses file checkpoints and atomic temporary-file replacement in
authorized runners, plus scheduler records. Existing Round 2 rendering uses local
browser export and visual cards. New persistence and rendering remain protocols,
with an independent planned namespace `backend/data/infographics`. No schema,
existing renderer, checkpoint or output file is changed. The existing infrastructure
uses a mixture of logging, worker logs, status JSON, exceptions and pytest; the new
clients emit safe exception categories and contain no logging or content persistence.

The smallest integration surface is the standalone `app.infographics.initialize`
factory. Nothing in the existing application calls it. A future explicitly added
server entry point can opt in without coupling lecture processing to infographics.
No existing dependency or lockfile was modified; the installed `google-genai`
supports the adapter's model metadata, timeout and retry configuration.

## Baseline and preservation

Initial `git status --short` at workspace root, `NOETRA` and `backend` each returned
“not a git repository.” This checkout has no usable enclosing Git metadata; no
Git status, tracked-change attribution or complete Git diff can be supplied.
Nested Git metadata in unrelated subprojects was left untouched.

Before writing implementation code, `INFOGRAPHIC_BASELINE.json` recorded SHA-256
hashes for 1,022 pre-existing backend/frontend files, including environment and
dependency files without exposing their contents. The snapshot excludes `.git`,
dependency/virtual-environment directories, Python/test caches, `data`, `dist`,
`video`, and the nested table-render-test project. Final comparison found zero
changed or removed files in that snapshot. This is scoped preservation evidence,
not a claim that all runtime/data directories were hashed. Implementation changes
were reviewed as additive files; new Python files were parsed, and added-file
diff whitespace checks were run without initializing or changing Git metadata.

No pre-existing source/configuration/test file was edited. No existing modification
needed to be reconciled or removed. Normal build/test outputs were produced by
the existing tools in their output/cache directories. No lecture generation,
ASR/OCR, RAG ingestion or infographic generation was run.

## Created files

| File | Purpose |
| --- | --- |
| `INFOGRAPHIC_BASELINE.json` | Initial file hashes and Git limitation |
| `INFOGRAPHIC_PHASE1_REPORT.md` | Inspection, inventory, validation and limitations |
| `backend/app/infographics/__init__.py` | Disabled-first lazy entry point |
| `backend/app/infographics/config.py` | Isolated credentials and independent role settings |
| `backend/app/infographics/contracts.py` | Neutral educational types and future-stage/provider/storage/rendering protocols |
| `backend/app/infographics/clients.py` | Role authorization, limits, concurrency, retries and usage accounting |
| `backend/app/infographics/gemini.py` | Independent Google SDK transport and safe provider errors |
| `backend/app/infographics/runtime.py` | Client composition, explicit model verification and cleanup |
| `backend/app/infographics/.env.example` | Server-only disabled-by-default configuration example |
| `backend/app/infographics/README.md` | Module boundaries, configuration and future integration |
| `backend/tests/test_infographics_foundation.py` | 34 focused offline test cases |

Modified pre-existing files: **none**. No justification for an existing-file edit
is needed because all requested foundation behavior was implemented additively.

## Actual validation

Before implementation:

- Existing regression selection: **70 passed, 7 subtests passed**.
- Frontend `npm.cmd run build`: **passed** TypeScript and Vite production build;
  Vite reported its large-chunk warning. Frontend source/dependencies did not change.

After final implementation:

- Same existing tests plus new foundation tests: **104 passed, 7 subtests passed**.
  Existing files selected: `test_round2.py`, `test_round1_quiz.py`,
  `test_gemini_provider.py`, `test_rendering_simple.py`, `test_serialization.py`,
  `test_transcription_stage1.py`, `test_transcription_risk.py`.
- The **34 new cases** exercise disabled lazy initialization with forbidden network
  and directory operations, missing keys, invalid configuration, distinct dedicated
  credentials, legacy-key isolation, independent settings/transports/accounting,
  role workload rejection, model admission/reverification, context/request/token
  limits, concurrency, same-client retry accounting, quota holds, safe errors,
  partial-init cleanup, close semantics and Google SDK mapping with no network.
- Removed all three dedicated keys from a subprocess environment, set the feature
  flag false, initialized the new module, imported the real existing backend, bound
  an ephemeral loopback port and made one read-only `GET /api/videos`: **HTTP 200**.
  Existing Host validation was respected with `Host: 127.0.0.1:8765`. The initial
  sandbox blocked the loopback connection; an approved unsandboxed run worked.
  An initial ephemeral-host request returned the existing expected 403; supplying
  the existing required Host header completed the smoke check. No job was submitted.
- Snapshot comparison: **1,022 checked; zero changed or removed**.
- No paid generation requests or real model completions were issued.

Reproduce regression command from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_infographics_foundation.py tests/test_round2.py tests/test_round1_quiz.py tests/test_gemini_provider.py tests/test_rendering_simple.py tests/test_serialization.py tests/test_transcription_stage1.py tests/test_transcription_risk.py -q --disable-warnings
```

These are selected regression tests and a backend startup/read smoke check, not
a full application end-to-end or full repository test-suite claim.

## Model and architectural limitations

The [official Gemma API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
documents `gemma-4-31b-it`. The three dedicated keys were absent from both process
environment and backend `.env`; exact availability/permissions for these accounts
could not be verified through their configured API. The code provides explicit
per-role `models.get` checks for the exact model, generation capability and token
limits, and denies completions before verification. Legacy keys were not used.
Enabling the feature alone creates no metadata or generation requests.

Limits and counters are independent per client, process-local and in memory. They
do not provide durable or distributed quota enforcement. Provider project/account
quotas still apply across credentials. Local token reservations use a conservative
byte-based estimate; actual usage is recorded separately where reported, including
thought tokens when present. A future context manager can implement exact token
counting. Retry attempts never rotate credentials; provider 429 errors stop as holds.

The three-category taxonomy, fifteen template mappings, stage implementations,
durable artifacts/checkpoints, prompts and AntV rendering remain intentionally
unimplemented. Their contracts and capacities are prepared. Deterministic rendering
is a future adapter obligation, not a tested rendering capability in Phase 1.

Phase 1 is complete within these stated verification limits. No later phase was
started, no existing application integration was activated, and the feature remains
disabled by default.
