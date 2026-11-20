# Fixes and actual live result

The request-size failure is fixed on the active category-bounded native Task 12A
path. Full lecture notes are NOT complete: the run stopped at a daily quota HOLD.

## Repairs

- Expanded-schema budgeting replaces compact-$ref sizing. It is conservative
  accounting, not a claim to reproduce Groq's tokenizer.
- One category per request keeps native per-field claims, source refs, availability,
  literal kinds and correction roles. The original Task 12A local schema and
  resolver remain mandatory. Experimental ID/table codecs are not the default.
- Bounded speech passages preserve all 2181 original segments, exact text,
  fractional times, word records and character offsets. All 501 visual records
  remain separate, unverified and nonquotable. Original stages are unchanged.
- A proven pre-dispatch authorization failure was left open in the minute ledger.
  Its lifecycle was closed at its existing operation-completion time, retaining
  the full 6591-token charge, reservations and audit history. Dispatched or
  uncertain attempts cannot use that reconciliation path.
- Future provider failures save their available complete HTTP error bodies after
  secret checks. Past attempts retain the diagnostics actually captured; missing
  past bodies were not invented.

## Final production-path invocation

Only the facts pass ran. The other seven knowledge categories have NOT started.

| Measurement | Result |
|---|---:|
| Initial primary facts chunks | 61 |
| Actual API attempts | 64 |
| HTTP 200 responses | 52 |
| Provider failures | 12 |
| Validated checkpoints, including recovery children | 43 |
| HTTP 200 responses rejected locally | 9 |
| Extracted fact items | 364 |
| Reported input/output tokens | 165791 / 71473 |
| Attempts with unknown usage | 12 |
| Actual total token consumption | Unknown; reported subtotal 237264 |
| Invocation duration including waits | 1777.875 seconds |
| Remaining untouched primary facts requests | 15 |

Validated checkpoints include recovered children and introductory chunks with no
knowledge items; this is not the completed-primary count. Truncations use approved
smaller requests on the same organization. Invalid responses remain unresolved.
In a sample of 32 reported responses, the largest input-plus-output total was
5734, below 6800; none had input above the corrected estimate. This is actual size
admission evidence, not semantic verification or an exact-tokenizer guarantee.

## Capacity and resume

Organization 2 has 168227 local rolling-day tokens charged against a 170000
ceiling. The blocked request reserves 5876; only 1773 remain. No key switching or
charge clearing was used. Existing charges first permit this specific local daily
check around **2026-11-11 18:40:40 IST**. That is not a provider/shared-stage
headroom guarantee; all checks must run again. See `resume_requirements.json`.

From backend:

```powershell
& .venv/Scripts/python.exe run_full_multimodal_categories.py --resume data/output/multimodal_notes_category_full_20261110_135722_142723
```

## Evidence and outputs

`partial_notes.md` is incomplete, unverified facts-only output with passage times.
Other outputs include extraction_results.json, structured_notes.json,
quality_report.json, source_document.json, source_time_index.json,
source_unit_fingerprints.json, source_fidelity_audit.json, category_runs.json,
run_summary.json, OCR review supplement, unresolved gaps and old/new comparison.
Exact request manifests, responses and checkpoints are in the facts folder linked
by category_runs.json. Earlier experimental calls remain separately recorded.

All cited source IDs resolve. 163 visual units appeared as nonquotable primary
context in dispatched requests; zero visual source IDs were cited as authoritative
facts. The mortgage remains VISUAL_CONTEXT_REQUIRED, path strings conflict, and
clipped characters remain unresolved. No code or formula was reconstructed.

Old text-only output was itself partial (48/50 chunks): 458 items across eight
categories. The new 364-item facts-only result has different coverage/granularity;
counts do not measure improvement. Comparison JSON preserves example excerpts
and source IDs. No accuracy, completeness or readability percentage is claimed.

35 focused checks passed in the final delivery test set. A separate native-category
end-to-end check passed for rotation, resume and saved-response recovery. See
backend TASK13_FIX_IMPLEMENTATION.md for changed files and implementation detail.
No new model, OCR, ASR, canonical replacement or human semantic approval occurred.
