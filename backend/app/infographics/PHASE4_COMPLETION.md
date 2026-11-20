# Phase 4 completion

Offline software acceptance: passed for the tested scope below. Live model quality
acceptance: pending. No live API calls were made. Phase 3 live quality also remains
unverified. Source-range preservation is distinct from planner-assessed suitability
and from semantic fact preservation in future generated content.

## Inventory and preservation

All changes are additive. No earlier-phase source, prompt, client, configuration,
test, application entry point, original note or generated artifact was edited.
The feature remains disabled by default. No dependency or existing schema changed.

Created under `backend/app/infographics/`:

- `PHASE4_BASELINE.json`: pre-implementation hashes for 1,919 existing files.
- `optimization_model.py`: completed-input validation adapter, capacity settings,
  compact metadata, lexical candidate discovery and ownership invariants.
- `optimization.py`: global planning, batched source confirmation, transformation,
  atomic checkpoints, replay validation, configuration-aware reuse and metrics.
- `prompts/global_segment_optimizer.txt`: versioned planning/confirmation prompt.
- `optimization_evaluation.py`: unchanged fixture reuse and before/after evaluation.
- `evaluate_optimization.py`: opt-in dry/live evaluation command.
- `evaluation/optimization_cases_v1.json`: ten editorial scenario annotations.
- `PHASE4_COMPLETION.md`: this report.

Created outside the module: `backend/tests/test_infographics_optimization.py` only.

Integrity checks: Phase 1 **1,022 unchanged**, Phase 2 **1,892 unchanged**, initial
Phase 3 **1,902 unchanged**, and new Phase 4 **1,919 unchanged**. The older hardening
baseline lists the same two pre-existing authorized Phase 3 modifications
(`segmentation.py`, `segmentation_budget.py`) documented in PHASE3_COMPLETION.md;
Phase 4 made no additional changes to either. Snapshots retain their scoped
source/config/docs and selected-note coverage; they do not hash every media/cache file.

## Architecture and API

`OptimizationJob(completed_segmentation_job, planner=..., store=..., config=...)`
accepts a completed Phase 3 job and invokes its existing range checks plus
`planner_integrity.validate_checkpoint` against the reconstructed source metadata.
Incomplete jobs, bad IDs, source hashes, offsets, categories, support links and
ownership fail before optimization. The input manifest is captured as immutable
canonical JSON; `manifest` returns a detached canonical optimized JSON value only
after completion or an explicit optimization-skipped state. Provisional files are
never overwritten. `prepare_optimization(..., environment=...)` checks the disabled
flag before inspecting input or creating any storage/client/job.

Only the supplied Phase 1 planner RoleClient is used, with workload
`global_consolidation`. The existing planner-only helper can initialize/verify it.
Generator/verifier clients and keys are not required or accessed. Normal application
startup remains disconnected. Existing provider retry, concurrency, token/request
accounting and quota admission remain authoritative. Bounded response retries apply
only to malformed successful responses; quota/model/credential/transport failures
pause without publishing an optimized result.

### Stage A: deterministic candidates

The compact planning manifest uses short IDs with a backend mapping to stable
optimized group IDs. Metadata includes exact start/end source block IDs, order,
category, title, focus, words/tokens, density, estimated items, section paths,
continuations and supplementary associations. Up to six literal source-derived
anchor terms are extracted locally. Original notes are not sent for this stage.

Adjacent pairs are discovered through normalized title/objective token overlap,
nonempty shared sections, continuation groups and possible nonvisual support.
Candidate records expose combined item counts and category compatibility.
These signals propose review only: they never authorize a merge. Empty/single/no-
candidate manifests exit without requests. Pure visual manifests already at the
preferred minimum also exit locally because a merge would violate that minimum.

### Stage B: compact global planning

The static prompt is **2,353 UTF-8 bytes**, a conservative local token estimate,
not an exact Gemma tokenizer count. Runtime budget checks include the complete
serialized prompt, overview, category guidance, soft lecture budget, segment rows,
candidate rows and retry feedback reserve. One global request is used when it fits.
Otherwise sequential greedy windows retain limited read-only previous/forward
metadata and overlap two eligible segments. Adjacent pairs across windows remain
available. Proposals are restricted to the eligible short IDs; read-only context
cannot be merged. Global overview counts and budget pressure accompany each window.

After meaningful accepted changes, a bounded second round plans from updated compact
group summaries, allowing cross-window/previous-group reconciliation. An unchanged
round stops. Default rounds are limited to two, and requests have a separately
configured conservative attempt cap. Larger scenarios can require an explicitly
configured additional round; the optimizer never loops indefinitely.

The strict JSON response has `merges` and `attachments` arrays. Merge fields are
ordered adjacent `segments`, category A/B/C/N, short title/focus, density enum,
bounded estimated_items and controlled reason enum. Attachment fields are source,
target and supporting_derivation/supporting_example. Unknown fields, duplicate
JSON keys, malformed/truncated JSON, unknown IDs, duplicate IDs, nonadjacent ranges
and conflicts within a response are rejected. Valid proposals missed by local
candidate discovery are allowed if they reference eligible adjacent groups.

### Stage C: source-grounded acceptance

Deterministic checks run before original source is transmitted: category/metadata,
current adjacency, conflicting earlier merges, readability capacity, preferred
minimum and future generation context. Source retrieval uses existing immutable
indexed blocks; no new source parser exists. Multiple eligible proposals are packed
into context-safe confirmation batches. Oversized batches shrink to whole proposals;
a proposal too large even alone is rejected without truncation.

Confirmation requests contain the exact source blocks and proposed objective.
Strict responses must identify every proposal exactly once and report boolean
support, distinction preservation and readability with the expected final category.
Uncertain/negative responses retain original groups. Confirmed proposals still pass
current structural/capacity checks at application time, so stale overlapping groups
from different planning windows cannot create duplicate ownership. Independent valid
operations may survive rejection of a conflicting operation. The batch is committed
in one checkpoint transaction; in-memory groups are restored if persistence fails.

These are planner suitability judgments, **not independently verified semantic
truth or guarantees about future infographic content**. Mock responses test the
acceptance machinery, not actual model discernment of independent concepts.

## Capacity, categories and supplementary ownership

`OptimizationConfig` supplies generation input/shared ceilings and reserves for one
category prompt, five schemas, structured output, supporting output, thinking,
serialization and safety margin. Defaults are conservative configurable engineering
estimates: input 24,000; shared 32,000; prompt 1,500; schemas 3,000; JSON output 6,000;
support output 1,500; serialization 512; safety 10%. They are not hosted/free-tier
claims. Original source JSON including references is byte-counted. Overflow blocks
the merge; missing verified generator metadata yields `provisional_limits`, never
an invented verification. No generator client is initialized. Existing unchanged
segments can retain an explicit overflow status requiring later handling.

Default readability admission uses at most A=20/B=15/C=15 estimated items and the
larger of proposed items and the sum of constituent estimates. This is deliberately
conservative and configurable, not a renderer limit or educational-quality score.
It may reject useful merges whose concepts overlap. Capacity and the preferred
visual minimum are never sacrificed to hit a count. A/B/C reassignment is allowed
only after source confirmation, with original/final categories in merge history.

Continuation-linked groups receive candidate priority but cannot evade capacity.
Oversized continued concepts keep linked segments. N groups remain separate source
owners and cannot be swallowed into a visual or created from visual groups merely
to reduce count. They can gain a display association to a visual target after
confirmation; `semantically_represented=false` remains explicit. Earlier Phase 3
support links are retained. Target aliases resolve through merged ancestors,
including on checkpoint replay. Associations never duplicate ownership or increase
the independent infographic count.

## Output and recovery

Optimized rows retain exact source artifact/hash, block IDs, positions, offsets,
category, objective metadata, source estimates, all ordered original constituents,
continuation groups, supplementary IDs/display links, merge history and downstream
status. Stable IDs hash the source index fingerprint plus ordered constituents.
All original source units remain owned exactly once in the original order.

The existing SQLiteCheckpointStore is reused in an independent default namespace
`backend/data/infographics/optimization`. No tables in existing NOETRA databases
are touched. ReadingCheckpoint envelopes contain a new optimization stage and
source/input/index/prompt/model/config hashes; accepted/rejected operations,
confirmation outcomes, queues/cursors, history, usage, associations and final groups
are appended atomically. Request-in-flight revisions resume as paused_uncertain_request
and require explicit `retry_paused=True` reconciliation. Invalid responses or failed
optimization never overwrite a prior successful immutable revision.

Resume validates hash bindings and replays every accepted operation from the
immutable provisional input, independently recomputing derived groups, IDs, ranges,
history, capacities and association remapping. Stored groups must exactly match
that replay. Wrong source/input/model/config/prompt, corrupted checksums/fields or
bad cursors are rejected without repairs. Stale writers are rejected by the existing
parent-checkpoint check. Completed compatible runs reuse results without API calls.

## Examples and evaluation

The mocked queue example starts with three visual segments. Its first two adjacent
segments merge after source confirmation, leaving two visuals: **one fewer, 33.3%
reduction**, complete range coverage, zero missing/duplicate ownership. The original
provisional manifest stays byte-equivalent. A separate five-segment process fixture
merges its first four into one workflow, retaining an independent fifth:
**five to two, three fewer visuals**. A configured higher item ceiling is explicit
for that synthetic test. Negative confirmation keeps all original groups; source
or downstream overflow causes no source-confirmation request. These examples use
mocked decisions and do not establish live Gemma optimization quality.

All 30 unchanged Phase 3 fixtures are compared before/after using the existing
quantitative evaluator. Tests use deliberately fragmented provisional input and
mocked proposals. They verify complete range coverage, zero duplicate ownership
and preservation of annotated required independent boundaries across all fixtures.
The evaluator separately exposes fragmentation, consolidation, category and budget
metrics; lower visual count does not suppress missed-boundary penalties. Ten extra
editorial scenario cards cover related components, workflows, mixed categories,
continuations, oversized concepts, false lexical similarity, quantitative/theory
separation, N support, unchanged counts and justified soft-limit excess. These cards
document expected behavior; they are not an additional expert-reviewed dataset.

## Actual tests and commands

Relevant combined regression suite: **365 passed, 7 subtests passed** (300 previous
cases plus 65 new Phase 4 cases). The final focused rerun passed **65 tests**.
Added Python syntax and added-file whitespace checks passed. Tests cover empty/single inputs, valid/malformed/conflicting operations,
semantic rejection, reassignment, capacity, immutable source/input, continuation,
N attachment/remapping, all 30 evaluator fixtures, large planning windows and
cross-window adjacent-pair availability, bounded second-round reconciliation,
uncertain requests, stale revisions, corrupted output replay, source/input/config/
prompt mismatch, quota failure, disabled preparation and wrong-role rejection.
This is the relevant selected suite, not a full repository or browser test claim.

Dry run selected all 30 fixtures with **zero requests**:

```powershell
cd C:\Projects\adaptive-notes\backend
.\.venv\Scripts\python.exe -m app.infographics.evaluate_optimization --dry-run
```

Optional live evaluation (not executed):

```powershell
$env:GEMINI_PLANNER_API_KEY = '<authorized planner key>'
.\.venv\Scripts\python.exe -m app.infographics.evaluate_optimization --live --fixture 01-queue --max-requests 10 --max-tokens 100000
```

The CLI reuses planner-only initialization and verifies the model. It builds a
deliberately fragmented validated fixture manifest locally; these are not live
Phase 3 segmentation results. Invocation limits account for planner attempts and
conservative context reservations; transport retries are set to one for strict
harness caps. The model-metadata call counts as a request. Results append unique
JSON artifacts containing before/after metrics, manifest and processing diagnostics.
Compatible completed checkpoints are reused. Paused work requires --retry-paused.
Exact credentials are redacted from persisted result copies; fixtures are synthetic,
not a facility for private-source evaluation. Ordinary tests never enable live mode.

Planner key presence was checked without printing the key: it was absent from the
process and backend `.env`. **Actual live API calls: zero.** Static prompt and
serialized request costs are conservative UTF-8 estimates; actual input/output
token fields come only from provider usage metadata (mocked values in tests).

## Metrics and limits

Metrics expose before/after visual count and exact reduction ratio, accepted/rejected
merge count, category distributions, consolidated continuation groups, attachments,
complete source-range coverage, missing/duplicate ownership, average words/tokens
per visual, density distribution, over-capacity segments, downstream status, planner
calls, provider attempt/token accounting, API/local duration, malformed-response
retries, cache reuse, context window/batch resizing and budget adherence. Unresolved
soft excess has an explicit reason. Semantic fact coverage is always unverified.

Conservative summed item estimates may under-consolidate; small readability
preferences can be raised explicitly. A compact row or source proposal that cannot
fit even alone pauses/rejects safely. Two default reconciliation rounds do not
guarantee an optimal partition of arbitrarily large lectures. Large manifests use
a global statistical overview with local metadata windows rather than exposing
the whole lecture text in every request. Unclassified provider context errors
remain generic safe pauses under the unchanged transport. SQLite assumes supported
local locking and a coordinated writer. Editorial annotations are assistant-authored,
not expert-reviewed. Live semantic coherence, actual readability, generation context
limits and model-level prompt-injection resistance remain experimentally unverified.

No Phase 5 template selection/content generation, semantic fact verification,
rendering, frontend integration, orchestration or final master mind map was added.
