# Phase 5 completion

Offline software acceptance: passed for the tested scope below. Model access was
verified by three metadata-only requests. Live generation quality, browser rendering
compatibility and independent semantic verification remain pending. No lecture
content or generation request was sent to the provider. No Phase 6–8 work was added.

## Inventory and preservation

Modified earlier-phase files, solely for the explicitly authorized key mapping:

- `config.py`: centralized role-key lookup replaces the legacy-only lookup in
  the existing three-role configuration loader.
- `planner_init.py`: the existing planner-only initializer uses that same lookup.

Created inside `backend/app/infographics/`:

- `PHASE5_BASELINE.json`: 1,928 pre-edit file hashes.
- `role_environment.py`: centralized fixed key mapping and role composition.
- `generator_init.py`: independent disabled-first generator initializer.
- `template_registry.py`: exactly 15 versioned approved entries.
- `generation_schema.py`: eight reusable strict schema families and batch validation.
- `antv_adapter.py`: deterministic native configuration mapping for all 15 templates.
- `generation.py`: validated input, output-aware batches, outcomes, artifacts,
  source associations, checkpoints, resume and metrics.
- `generation_fixtures.py`: original synthetic positive/unsuitable examples.
- `evaluate_generation.py`: opt-in synthetic dry/live evaluation command.
- `prompts/generation_common.txt`: common information-preservation and JSON contract.
- `prompts/master_A_structure.txt`, `master_B_mechanism.txt`, `master_C_analysis.txt`:
  specialized five-choice prompts.
- `evaluation/generation_fixtures_v1.json`: inspectable examples and native mappings
  for all 15 choices, with unsuitable-source cases.
- `evaluation/antv_compatibility_v1.json`: pinned package/hash/source evidence.
- `PHASE5_COMPLETION.md`: this report.

Outside the module, only `backend/tests/test_infographics_generation.py` was added.
No old tests, original notes/artifacts, environment files, dependencies, existing
database schemas, frontend files, application entry points or unrelated API clients
were edited. The feature remains disabled by default and no worker/route was added.

Baseline comparison: all 1,022 original Phase 1 files match. Phase 2 and initial
Phase 3 snapshots differ only in the now-authorized `config.py`. The older hardening
snapshot additionally retains the two already documented Phase 3 changes to
`segmentation.py` and `segmentation_budget.py`. Phase 4 and the fresh 1,928-file
Phase 5 snapshots differ only in `config.py` and `planner_init.py`. These comparisons
cover the existing scoped source/config/docs and selected note artifacts; they do
not imply every media/cache/runtime file was hashed.

## Fixed credentials and model availability

Canonical lookup is fixed: **GEMINI_API_KEY_1 → planner**, **GEMINI_API_KEY_2 →
generator**, **GEMINI_API_KEY_3 → verifier**, with no rotation. All three configured
keys were detected and were distinct; values were never printed or persisted.
Canonical values always take precedence, including explicit empty values. Legacy
role aliases remain optional fallbacks only when the canonical variable is absent,
preserving earlier callers/tests; duplicate environment copies are unnecessary.

The exact numbered names were not referenced by other existing backend/frontend
source in the inspection search, and no other process/backend environment binding
had an identical value during the check. Existing Gemini clients still use their
original configuration. Separate keys do **not** establish separate project quotas:
other callers and keys in the same provider project may consume shared quota. No
existing key assignment or external client was changed to address that possibility.

`initialize_generator(environment, transport_factory=..., config=..., verify=True)`
uses only key 2 and the existing ClientConfig/RoleClient/GeminiTransport. No planner
or verifier is initialized by this helper. Disabled initialization returns before
credential reads. Generator-only defaults allow a larger configurable context/output
budget (32,000/8,000); the existing three-role defaults remain unchanged. Independent
per-client request/token accounting, rate admission, concurrency and retries remain
in the existing RoleClient. The existing planner helper now works with key 1.

Exactly **three live model metadata requests** were explicitly executed, with one
attempt per role and no retries. Each returned `models/gemma-4-31b-it`, input limit
**262,144**, output limit **32,768**, and `generateContent`/`countTokens` capabilities.
These are metadata-advertised limits, not rate/free-tier guarantees. Effective
request admission remains constrained by configured client ceilings and safety
reserves. No planner segmentation, generator completion or verifier processing
was invoked. A verifier metadata check is not a Phase 6 verification workload.

## Registry and AntV compatibility

Intended compatible package: **@antv/infographic 0.2.20**. The public npm tarball
was read in memory without installation or extraction into the project. SHA-256:
`cb82ca6a37be7c21ab3d2e5caa495cc6546441d30c214f261d4c732db465696e`.

References inspected: [official repository](https://github.com/antvis/Infographic),
[official data documentation](https://infographic.antv.vision/learn/data), and
[syntax creator source](https://github.com/antvis/Infographic/tree/main/skills/infographic-syntax-creator).
The evidence JSON records actual package source paths, generated-family registration
and structure field accesses. All identifiers below were confirmed, including names
expanded dynamically from family configurations. No identifier was substituted.

| Code | Exact AntV identifier | Intermediate family |
| --- | --- | --- |
| A1 | hierarchy-mindmap-branch-gradient-capsule-item | Recursive hierarchy |
| A2 | hierarchy-tree-curved-line-rounded-rect-node | Recursive hierarchy |
| A3 | hierarchy-structure | Grouped hierarchy |
| A4 | list-grid-badge-card | Unordered information list |
| A5 | sequence-pyramid-simple | Ordered sequence |
| B1 | sequence-snake-steps-compact-card | Ordered sequence |
| B2 | sequence-circular-simple | Ordered sequence |
| B3 | sequence-timeline-rounded-rect-node | Ordered sequence |
| B4 | relation-dagre-flow-tb-badge-card | Directed graph |
| B5 | sequence-interaction-default-compact-card | Actor interaction |
| C1 | compare-binary-horizontal-simple-fold | Comparison groups |
| C2 | compare-quadrant-quarter-simple-card | Comparison groups |
| C3 | chart-bar-plain-text | Numerical values |
| C4 | chart-line-plain-text | Numerical values |
| C5 | chart-pie-donut-plain-text | Numerical values |

Each registry entry exposes purpose, required/optional fields, category, mapping,
recommended capacity, description behavior, limitations, pinned version and separate
documentation/browser statuses. Readability preferences are guidance; configurable
maximum items/depth bound validation. No reserve templates are exposed.

NOETRA intermediate JSON is the validated educational representation. AntV textual
DSL is a separate syntax and is **not emitted**. The adapter returns native JavaScript
configuration expressed as JSON-compatible data, with application-controlled styling.
Native configuration has been source-inspected and tested as data, not executed in
a browser. Browser rendering remains untested and belongs to Phase 7.

Key mappings/limits: hierarchy `root`; grouped layers/components through `items` and
`children`; lists via `lists`; ordered sequences via `sequences`/`order`; comparisons
via `compares`; graph `nodes`/`relations`; numerical `values`. Interaction data uses
actor lanes containing action children with unique IDs and integer `step`, and edges
connect actions. A3 supports at most three native levels; its label-only structure
folds concise descriptions into labels. Interaction action descriptions are likewise
folded into labels. C2 dimensions are retained in the native description. C4 uses
equal index spacing; it is not a continuous time-axis renderer. Numeric geometry
uses JavaScript-compatible doubles while original decimal strings/units remain in
the intermediate artifact and visible labels. Overflow/underflow are rejected;
arbitrary double precision is not claimed. No native resource URL, generated code,
HTML, styling field or arbitrary template name is accepted from the model.

## Generation architecture and preservation policy

GenerationJob accepts a completed OptimizationJob, or a validated skipped result
only with explicit `allow_skipped=True`. It verifies source/index/provisional hashes,
derived original boundaries/IDs/counts, category metadata, continuation/support links,
complete ownership, and replays Phase 4 accepted transformations. The replay must
exactly match the optimized manifest. Previous manifests and notes remain immutable.

Category-specific requests combine the common preservation block, one specialized
prompt and its five compact choices. Template selection, compression and structured
generation occur in the same call; no extra template-selection call exists. Combined
static prompt byte/token estimates: **A 3,336; B 3,388; C 3,492**, using conservative
UTF-8 byte estimates rather than an exact Gemma tokenizer. Runtime schema/choice,
source, metadata/serialization and output reserves are recorded separately.

The common policy preserves P0 technical definitions, formulas, values/units,
assumptions, conditions/exceptions; P1 concepts and mechanisms; P2 examples, code,
derivations and qualifications via linked support; and removes only genuinely
redundant P3 wording. A 25% visible-word target is a flexible preference, not a
hard limit or proof of preservation. Nodes require meaningful descriptions.
Supporting records reference a visual item and exact authorized source aliases.
No compression ratio or hierarchical-routing token-saving claim has been benchmarked
against live model behavior.

All eight families share strict node/reference/support rules and template-specific
checks. Generated records have segment/status/type/title/data/support only. Nonvisual
N segments pass through locally with their source references and no routine LLM call.
Outcomes `needs_split`, `reroute`, and `unsupported` remain explicit records; they do
not mutate Phase 4. Split boundaries must be ordered internal primary-source block
boundaries. Optional automatic rerouting permits at most one correction, then retains
any further proposal instead of looping. Operational capacity/provider/validation
failures are paused states rather than fabricated educational outcomes.

## Context, batching and traceability

Pending segments are grouped by current master category. The packer estimates
output from item count, density and configurable per-item/support/base reserves,
adds thinking allowance and checks full serialized input with existing TokenBudgetManager
and verified metadata/configured ceilings. It reduces whole-segment batch size when
input or output does not fit. A single oversized segment receives a paused capacity
issue without truncation. Requests return exactly one record per requested alias;
missing/duplicate/unknown records reject the whole uncommitted batch.

Source aliases use stable global indexed positions, so a source alias authorized
for one segment is not accidentally reused for another. Only the current primary
range and explicitly attached N support are permitted. Aliases resolve to original
block IDs, offsets and content hashes. Native item IDs are deterministically derived
from the persistent visual identity and local item IDs. Supporting associations can
resolve through this item-ID map. Final artifacts restore original lecture order,
independent of category processing or model response order.

JSON educational counts exclude established storage metadata via the existing adapter
and conservatively retain unknown content. Actual transmitted JSON is always counted
in full for API admission. Structural estimates, educational words and request token
cost are not treated as interchangeable. Source-reference presence is traceability,
never evidence that the referenced text entails a generated claim.

## Deterministic validation and artifacts

Validation rejects unknown fields, duplicate JSON keys, NaN/infinity, bad statuses,
wrong category-template combinations, missing descriptions, invalid hierarchy depth,
duplicate/unsafe IDs, graph endpoints, action actors/ordering, binary/quadrant shape,
incompatible binary attribute labels and repeated quadrant axes/poles. Cycles require
explicit closure references but their semantic genuineness remains unverified.
Numerical data use exact decimal strings, finite geometry values and literal source
matching for values and units. C5 rejects negatives and zero totals and requires
whole/exclusivity source references. Literal formula support must appear exactly
in cited text. These checks do not establish general semantic correctness.

Artifacts bind stable visual/optimized/constituent IDs, source identity/range/hash,
category/template, intermediate content, support, reversible source aliases,
registry/schema/adapter versions, model/prompt metadata, native adapter result and
usage scope. `deterministic_validation=passed` is separate from
`semantic_verification=pending`. They are not labeled fully verified.

The unchanged SQLite store is reused under an independent generation namespace.
Checkpoints contain config/version/hash bindings, queues, in-flight batches, completed
records/artifacts, outcomes, overrides, usage, validation/retry history and processing
state. Each batch commits artifacts and progress atomically; failed writes restore
uncommitted results. A request-in-flight resume pauses as uncertain until explicitly
retried. Existing validated artifacts are excluded from subsequent pending batches.
Resume revalidates record schemas/authorized refs, identities, native conversion,
version bindings, nonvisual ownership, category overrides and queues. Corruption or
source/manifest/config/version changes reject recovery without repairing stored data.

## Evaluation and actual tests

The relevant combined regression suite passed **435 tests and 7 subtests**: 365
previous cases plus 70 Phase 5 cases. The final focused rerun passed **70 tests**.
Python syntax and added-file whitespace checks passed. This is selected regression
evidence, not a full repository/browser suite.

Tests cover all 15 templates/eight families, five-choice prompt separation, both
canonical initializers and precedence, disabled credential isolation, graph and
interaction structure, binary/quadrant constraints, hierarchy limits, numerical
precision/units/nonfinite/negative/zero/underflow cases, exact formula support,
unauthorized source refs, support association, native text injection isolation,
strict JSON/missing/duplicate records, output-aware 2+1 batching, lecture order,
nonvisual pass-through, reroute limit, capacity/quota holds, incompatible recovery,
corrupted adapter replay, uncertain requests and failed transaction rollback.
Existing tests continue to cover earlier stages and existing backend startup without
new credentials. No original lecture processing or paid generation test was run.

The fixture catalog includes one positive structured example and one unsuitable
educational source per template, plus deterministic native examples. They are original
assistant-authored synthetic fixtures, not independently expert-reviewed ground truth.
Unsuitable fixtures test preservation via explicit unsupported outcomes; mocked
acceptance is not evidence that Gemma will select the right template. Existing
Phase 3/4 annotations remain unchanged.

The dry run selected all 15 fixtures, required no credentials and reported **zero
requests**:

```powershell
cd C:\Projects\adaptive-notes\backend
.\.venv\Scripts\python.exe -m app.infographics.evaluate_generation --dry-run
```

Optional bounded live generation (not executed):

```powershell
# Export the existing GEMINI_API_KEY_2 into this process, or pass an operator-loaded
# environment mapping to initialize_generator. No key rename is needed.
.\.venv\Scripts\python.exe -m app.infographics.evaluate_generation --live --fixture A4 --max-requests 3 --max-tokens 100000
```

The CLI supports category/fixture selection, verified model limits, invocation
request/token caps, checkpoint resume, cache reuse and --retry-paused. Synthetic
validated source/optimization fixtures are built locally without initializing a
planner client or reading planner/verifier credentials. It saves uniquely named
result artifacts, selection diagnostics and metrics with the exact credential
redacted. It never transmits private original lecture content. Cached results are
revalidated and reused; ordinary tests never enable live mode. Environment files
are not auto-loaded by the module or edited by the CLI.

Actual provider activity in this phase: **3 metadata requests; 0 generation
requests; 0 independent verification requests**. Public AntV package downloads
were compatibility inspection, not LLM calls. Live generation quality remains pending.

## Metrics and practical limitations

Metrics expose optimized/generated counts, categories/templates, success/outcomes,
schema-valid response ratio, split proposals/reroute corrections, educational words,
visible/support word estimates, compression/content ratios, source-reference coverage,
requests/provider-reported usage, tokens per visual, prompt estimates, batch sizes,
retry/cache/duration and context resizing. Source-reference coverage measures indexed
blocks cited by generated content; it is distinct from complete preserved source
ownership and does not include semantic fact verification. Ratios use all original
educational words, including nonvisual material. Artifact usage is explicitly scoped
as job-cumulative-at-commit, not invented per-artifact provider measurements.

The existing transport does not expose finish reasons separately, so malformed or
truncated JSON is rejected but an exact output-truncation rate is unavailable. Output
estimates and local byte bounds are conservative and can pause dense single segments;
larger configured context/output ceilings may be needed within verified limits.
Reordering, semantic cycles, genuine analytic dimensions, entailment, and whether all
unique important facts survived compression remain for Phase 6/live evaluation.
Native descriptions and data contracts are source-inspected; actual clipping,
layout, font behavior, interaction and browser export are Phase 7 work. No claim
of full visual or semantic verification is made.
