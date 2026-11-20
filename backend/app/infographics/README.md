# NOETRA infographic engine: Phase 1

This package is an independent backend foundation. No existing application imports
it, no route is registered, and no job is submitted. Removal consists of deleting
this directory and its focused test file. Existing prompts, clients, API key
assignments, database schemas, note files and frontend components are untouched.

## Boundaries

- `__init__.py`: opt-in entry point. Disabled initialization returns `None`
  before importing runtime, SDK, configuration or stage contracts.
- `config.py`: immutable server configuration, three separate credentials and
  independent model/limit/retry/concurrency settings. No environment mutation or
  implicit dotenv loading. The dedicated namespace is `backend/data/infographics`;
  no directories or artifacts are created in this phase.
- `contracts.py`: immutable source snapshots and source-hashed evidence, neutral
  knowledge items/links, segments, hierarchical routes, templates, verification
  reports, render requests, artifacts and versioned checkpoints. Protocols cover
  indexing, context selection, sequential segmentation, routing, consolidation,
  template selection, compression, structured generation, coverage/grounding
  verification, targeted repair, rendering, source reads and separate storage.
- `clients.py`: provider-neutral role clients, workload admission, process-local
  sliding-minute request/token limits, semaphore concurrency, retry policy and
  per-client accounting. Metadata requests count toward request limits. Every
  generation attempt reserves a conservative input bound plus output allowance;
  provider-reported usage is recorded separately. Unknown usage remains explicitly
  unreported. Failed attempts retain their reservation.
- `gemini.py`: independent lazy adapter using the already installed `google-genai`.
  SDK retries are disabled so role clients account for every attempt. Only this
  adapter contains Google SDK calls. Raw provider errors are replaced with safe
  categories. No keys, prompts or responses are logged or saved by this module.
- `runtime.py`: composition of three clients; explicit metadata verification and
  cleanup. No stage runner or generation prompts. `complete()` is transport
  infrastructure for future stages, not an implemented educational workflow.
- `.env.example`: new server-only settings, disabled by default.

The three-category taxonomy and fifteen template slots are reserved capacities.
Names, mappings and AntV template identifiers are deliberately unassigned. There
is no master lecture mind map, AntV dependency installation, syntax generation,
rendering, processing algorithm or persistence implementation in Phase 1.

The renderer protocol receives educational knowledge and a separate template
specification. A future AntV adapter owns its syntax and pinned renderer, font,
asset and layout settings. Educational knowledge contains no AntV syntax.
Future storage implementations must be confined to the dedicated namespace,
create immutable artifacts/checkpoint revisions, validate paths, and never write
through the source-reader interface. Checkpoints bind source hashes, public
configuration hashes and artifact IDs, never credential values.

## Configuration and explicit integration

Existing application startup remains unchanged. A future separately authorized
server entry point may call:

```python
from app.infographics import initialize

engine = initialize()  # Reads process environment; disabled by default.
if engine is not None:
    try:
        model_metadata = engine.verify_models()  # Explicit API metadata requests.
        # No processing stages exist yet.
    finally:
        engine.close()
```

For an explicit operator-managed dotenv file, pass a merged mapping to
`initialize(environment)`; process-environment precedence should be retained.
Never load the example into frontend Vite configuration or prefix these keys
with `VITE_`. No existing `.env` file is edited or auto-loaded by this package.

Required only when enabled:

```
NOETRA_INFOGRAPHIC_ENGINE_ENABLED=true
GEMINI_PLANNER_API_KEY=<dedicated planner credential>
GEMINI_GENERATOR_API_KEY=<dedicated generator credential>
GEMINI_VERIFIER_API_KEY=<dedicated verifier credential>
```

Disabled is `NOETRA_INFOGRAPHIC_ENGINE_ENABLED=false` or an absent flag. Only
explicit `true` enables the module; invalid flag values fail with a safe message.
Enabled configuration requires all three nonempty, distinct credentials and
validates everything before constructing any client. Legacy `GEMINI_API_KEY`,
Groq and other existing keys are never used as fallbacks.

Each role accepts the following independently, with prefix
`NOETRA_INFOGRAPHIC_PLANNER_`, `NOETRA_INFOGRAPHIC_GENERATOR_`, or
`NOETRA_INFOGRAPHIC_VERIFIER_`:

| Suffix | Default |
| --- | --- |
| MODEL | gemma-4-31b-it |
| REQUESTS_PER_MINUTE | 5 |
| TOKENS_PER_MINUTE | 32000 |
| CONTEXT_TOKENS | 16000 |
| MAX_OUTPUT_TOKENS | 2000 |
| CONCURRENCY | 1 |
| MAX_ATTEMPTS | 2, including first attempt |
| RETRY_SECONDS | 2, exponential backoff |
| TIMEOUT_SECONDS | 60 per network attempt |

These are conservative local settings, not provider quota claims. A request may
also be rejected locally by its token/context budget. Context admission uses
UTF-8 byte length plus a 256-token framing allowance rather than claiming an
exact tokenizer count. A future context manager can replace this conservative
bound with provider counting. Model metadata must explicitly verify the exact
name, generation support and positive input/output limits before generation;
configured context/output limits and provider limits both apply.

Planner workloads are segmentation, master category routing and global
consolidation. Generator workloads are template selection, content compression
and structured generation. Verifier workloads are coverage, grounding,
hallucination detection, targeted repair and reverification. Other workloads
are rejected before a request. Credentials never rotate; 429 quota errors are
non-retryable holds. Transient server/network errors may retry on the same client
within its local limits. Call `close()` after all in-flight work has completed.

## Model verification status (20 November 2026)

The [official Gemma Gemini API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
identifies `gemma-4-31b-it` for Gemma 4 31B. The
[model metadata API](https://ai.google.dev/api/models) provides per-key model
availability and limits. No dedicated planner/generator/verifier key was present
in process environment or the backend `.env` during implementation, so live
availability for these accounts could not be verified. No legacy key was used.
Run the explicit metadata check only after configuring the three dedicated keys.
No generation probe or fallback model is used.

The [AntV Infographic API](https://infographic.antv.vision/reference/infographic-api)
supports syntax/options rendering. Actual integration and deterministic export
remain future work behind the renderer interface.

## Limitations and validation

Limits, accounting and verified model metadata are in memory per client instance,
not shared across processes or persisted. Use one engine per process; future
multiworker support needs its own shared admission/accounting store. Provider
quotas remain authoritative, including project quotas shared by distinct keys.
Daily budgets, durable ledgers and persistent execution checkpoints are future
work. Conservative token reservations can underuse available capacity. No real
generation or AntV rendering has been tested or implemented in this phase.

Offline test command from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_infographics_foundation.py -q
```

See the workspace `INFOGRAPHIC_PHASE1_REPORT.md` for repository inspection,
baseline preservation evidence, complete file inventory and actual test results.
