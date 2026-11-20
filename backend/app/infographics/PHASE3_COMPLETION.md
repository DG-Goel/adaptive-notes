# Phase 3 hardening completion

Offline software acceptance: passed for the tested scope below. Live model quality
acceptance: pending. No live API calls were made; no real Gemma availability,
segmentation accuracy or prompt-injection resistance claim is made.

## Preservation and inventory

Modified existing Phase 3 files only:

- `segmentation.py`: reserved metadata request construction, complete resume
  validation, classified context resizing and output/thinking allowance.
- `segmentation_budget.py`: educational-content counting adapter.

Created inside `backend/app/infographics/`:

- `HARDENING_BASELINE.json`: 1,909 pre-edit file hashes.
- `planner_context.py`: bounded request packing/resizing adapter.
- `planner_integrity.py`: independent persisted-manifest validation.
- `planner_init.py`: planner-only environment composition.
- `educational_content.py`: schema-aware educational text measurement.
- `segmentation_evaluation.py`: independent quantitative evaluator.
- `evaluation/fixtures_v1.json`: 30 original annotated fixtures.
- `evaluate_planner.py`: opt-in dry/live CLI harness.
- `PHASE3_COMPLETION.md`: this report.

Created outside the module: only `backend/tests/test_infographics_hardening.py`.
All Phase 1 and Phase 2 implementations, interfaces, initialization, configurations,
clients, original notes, generated artifacts and existing application entry points
remain unchanged. No dependency or existing database schema changed. Feature
enablement remains explicit and disabled by default. No later phase was implemented.

All applicable snapshots were checked: Phase 1 1,022/1,022 unchanged; Phase 2
1,892/1,892 unchanged; initial Phase 3 1,902/1,902 unchanged. The fresh hardening
snapshot shows exactly the two authorized Phase 3 modifications above. Snapshots
retain their documented scope and do not cover every runtime/media/cache file.

## Resolved limitations

Dynamic request metadata now enters RequestParts before packing. The adapter
reserves the prompt, capacity guidance, progress/budget metadata, forced flag,
validation feedback and final-document flag inside the complete JSON request.
The existing Phase 2 budget counts full block metadata/serialization and all three
regions, framing, output, thinking and safety margins. The adapter first drops
optional previous context, then reduces source targets/maximum within a configured
eight-attempt limit when packing fails. It retains the same immutable index,
cursor and ownership; only whole structural groups are admitted. Useful lookahead
remains governed by Phase 2. Every transmitted request passes final preflight.
Failure to fit even one group produces paused_capacity_error without a model call.
ProviderError category context_limit triggers a bounded 0.7 input-ceiling reduction;
other transport categories pause or use existing RoleClient retries. The unchanged
Google adapter can return a generic request_failed for some provider errors; these
are deliberately not guessed to be context errors.

Resume now validates source/index/configuration hashes, prompt version/hash, model,
field sets, exact start/end IDs, positions, character offsets, deterministic segment
IDs, categories, metadata bounds, supplementary links, estimated counts, ordering,
continuation-group derivation, completion state and cursor. Derived values are
recomputed from the source. Phase 2 subsequently validates committed/pending ranges.
Manifest failures raise CheckpointIntegrityError without writing a replacement.
The existing append-only atomic manifest/cursor transaction remains unchanged.

`initialize_planner(environment, transport_factory=..., config=..., verify=True)`
checks the feature flag before credential access. It uses the existing ClientConfig,
RoleClient and GeminiTransport, constructs only planner, and verifies metadata by
default. Generator/verifier keys are neither read nor required. Injected transport
supports offline tests; missing planner keys produce the existing clear error.

Educational JSON counts recursively retain content values while excluding an
explicit set of established storage/application fields and duplicate visual copies.
Unknown field values remain conservatively included. Chapter/section titles,
paragraphs, lists, code, formulas and table values remain countable. Markdown uses
its original text. Structural indicators remain separate, and actual serialized
request tokens still include all transmitted metadata. Progress word counts are
explicitly estimated from the fraction of source blocks processed; they are not
claimed as exact per-window educational counts.

## Evaluation dataset and metrics

The versioned dataset contains 30 original editorial fixtures spanning computer
science, AI, mathematics, physics, biology, chemistry, history, economics and
engineering. It includes definitions, classifications, mechanisms, procedures,
feedback, chronology, comparisons, numbers, derivation/proof support, code and
mixed objectives. Each fixture identifies required/acceptable/avoided boundaries,
related groups, independent concepts, allowed categories, essential support,
nonvisual handling, visual-count range, soft limit, expected range coverage and
context challenge. Annotations were authored independently of planner responses
by the assistant; they have not received independent human expert review and must
not be described as unquestioned ground truth. Multiple acceptable boundary/category
sets are supported by the evaluator and dataset schema.

The evaluator measures deterministic coverage, missing blocks, duplicate ownership
and invalid ranges separately from quality diagnostics. Boundaries use configurable
adjacency tolerance and one-to-one matching for precision; recall checks required
boundaries, with harmonic F1. It reports unnecessary splits, related groups separated,
words per visual, normalized fragmentation, missed required boundaries, independent
concepts merged, estimated complexity excess and conceptual mixing. Category metrics
are block-weighted acceptable-category matches, distribution, confusion matrix
(first acceptable category is the reference), and incorrect N use. Budget metrics
compare actual visual count to the annotated acceptable range and soft ceiling.
Coverage never establishes semantic fact preservation; no generation/verification
is performed. Fewer visuals do not erase merge/missed-boundary penalties.

## Actual validation

The relevant combined regression selection passed **300 tests and 7 subtests**:
249 prior cases plus 51 hardening cases. New tests exercise 13 derived-field corruptions,
planner-only initialization, missing credentials, disabled credential isolation,
Markdown/JSON count equivalence, unknown content retention, large dynamic metadata,
forced/retry overhead, no-capacity behavior, all 30 discipline fixtures through the
runner, 250-block sequential processing over more than ten windows, lookahead
ownership rejection, classified context reduction, transient same-client retry,
dataset annotations and evaluator behavior. Prior cases cover partial commits,
source mutation, prompt changes, interrupted persistence, stale revisions,
malformed responses, source injection serialization, quota holds and no-progress.
This is selected regression evidence, not a full repository-suite or model-quality claim.

Dry runs for the whole fixture set and `01-queue` completed without credentials
and reported zero network requests. The command is:

```powershell
cd C:\Projects\adaptive-notes\backend
.\.venv\Scripts\python.exe -m app.infographics.evaluate_planner --dry-run
```

Explicit live evaluation (not executed):

```powershell
$env:GEMINI_PLANNER_API_KEY = '<authorized planner key>'
.\.venv\Scripts\python.exe -m app.infographics.evaluate_planner --live --fixture 01-queue --max-requests 10 --max-tokens 100000
```

The harness verifies the model and prints obtainable input/output limits. It reuses
RoleClient quota admission; max_attempts is restricted to one in the harness so a
conservative two-call envelope can bound each job step. Metadata verification counts
toward the request budget. Each step reserves two full configured context envelopes
against the invocation token cap before dispatch. Budget exhaustion leaves persisted
work resumable; completed fixtures are skipped unless --repeat is supplied. Use
--retry-paused for explicit reconciliation/retry of a paused fixture. Results save
compact manifests, redacted response copies, quality metrics and performance
diagnostics in the independent evaluation directory. Do not place private lectures
in the synthetic fixture dataset; redaction is designed for credentials, not general
PII detection. Ordinary tests never execute --live.

Performance diagnostics record the conservative static prompt estimate (3,539 UTF-8
bytes), dynamic metadata estimate, source estimate, full input/framing estimate,
window utilization, local resize attempts, forced-request flag, provider-reported
output usage and request counts. Admitted source ranges also provide an aggregate
estimated redundant primary-source token count and total automatic resize count.
An admission interrupted before dispatch can overestimate resubmission; these are
local admission estimates, distinct from provider-reported token usage.

## Remaining practical limits

The annotation set is small and assistant-authored, not expert-reviewed. Local byte
estimates intentionally underuse some hosted token capacity. JSON storage exclusion
is a conservative allowlist of established metadata; unfamiliar structures may count
extra content. Source-range metrics cannot establish semantic accuracy. Unclassified
provider context/timeout errors pause with a generic safe category. A source group
that cannot fit is explicitly unsupported rather than split arbitrarily. SQLite
recovery remains intended for supported local filesystems and one coordinated writer.
Live availability, semantic quality, exact tokenizer performance and real prompt
injection resistance remain pending live experimentation.
