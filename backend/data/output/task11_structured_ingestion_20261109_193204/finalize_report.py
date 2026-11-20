"""Freeze delivered code, test accounting and historical-preservation evidence."""
from pathlib import Path
from hashlib import sha256
import json
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
FILES=[
 'app/ingestion/docling_parser.py','app/ingestion/router.py','app/models/source.py','app/models/knowledge.py',
 'app/extraction/chunker.py','app/extraction/chunk_splitter.py','app/extraction/output_splitting.py',
 'app/extraction/quote_catalog.py','app/extraction/source_context.py','app/extraction/context_grounding.py',
 'app/extraction/document_authorization.py','app/extraction/organization_extraction.py',
 'app/extraction/single_request_authorization.py','app/evaluation/notes_pipeline.py',
 'pdf_ocr_pipeline.py','run_authorized_java.py','tests/test_structured_ingestion.py',
 'tests/test_ocr_completeness.py','tests/test_authorized_runner.py']


def main():
    tree=ET.parse(OUT/'regression_final_pass.xml')
    cases=tree.findall('.//testcase')
    failed=[c.attrib for c in cases if c.find('failure') is not None or c.find('error') is not None]
    skipped=[{'test':c.attrib,'reason':c.find('skipped').get('message')} for c in cases if c.find('skipped') is not None]
    stats={'passed':len(cases)-len(failed)-len(skipped),'failed':len(failed),'skipped':len(skipped),
           'skips':skipped,'failures':failed,'network_connections':'BLOCKED','live_calls':0}
    (OUT/'test_summary.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    if failed:raise AssertionError(failed)
    hashes={}
    for relative in FILES:
        content=(ROOT/relative).read_bytes();hashes[relative]=sha256(content).hexdigest()
        copy=OUT/'code_snapshot'/relative;copy.parent.mkdir(parents=True,exist_ok=True)
        if copy.exists() and copy.read_bytes()!=content:raise AssertionError('Code snapshot changed')
        if not copy.exists():copy.write_bytes(content)
    (OUT/'modified_file_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    before=json.loads((OUT/'historical_hashes_before.json').read_text(encoding='utf-8'))
    changed=[p for p,h in before.items() if not (ROOT/p).exists() or sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    preservation={'checked_files':len(before),'altered_files':changed,'passed':not changed,
        'task9_status':'READY_FOR_HUMAN_REVIEW','live_calls':0,'quota_records_modified':False}
    (OUT/'historical_preservation.json').write_text(json.dumps(preservation,indent=2),encoding='utf-8')
    if changed:raise AssertionError(changed)
    file_links='\n'.join('- ['+p+']('+str(ROOT/p).replace('\\','/')+')' for p in FILES)
    formats=json.loads((OUT/'cross_format_results.json').read_text(encoding='utf-8'))
    report=f'''# Task 11 — Structured ingestion repair

Status: **OFFLINE_INGESTION_REPAIR_COMPLETE**. Semantic review is still required.
The Task 9 pilot remains **READY_FOR_HUMAN_REVIEW**, not VERIFIED_STUDY_NOTES.

## Demonstrated result

The same saved 11-page Docling document now retains all 131 text elements. All 42
previously unmatched references are mapped, without rewriting the historical
document, source inventory or historical S-ID associations. Added elements receive
stable reference-derived N IDs; reading-order positions are independent of IDs.

| Measure | Historical baseline | Repaired replay |
|---|---:|---:|
| Canonical units | 109 | 154 |
| Text-bearing units | 89 | 131 |
| Missing raw text references | 42 | 0 |
| Uninterpreted picture units | 15 | 15, explicitly pending |
| Structural groups | Five empty list containers represented incompletely | Eight explicit structural containers |
| Original 13 chunks serializable | 4 | 13 |
| Recovered document chunks | — | 18; all serialize into prepared payloads |

These are source-element counts, not a semantic-quality score or unique-fact count.
The new PDF replay package contains 18 unapproved requests and zero budget holds.
It is a replay preparation artifact, not a live-run authorization manifest.

## Exact implementation changes

- **Docling adapter:** recursively walks serialized Docling references, including
  picture children, nested lists, captions and furniture. Each reference is emitted
  once. Broken links, cycles and orphan recovery are recorded. Pages with no element
  evidence become unresolved page units, rather than assumed blanks.
- **Identity and sidecars:** retains historical top-level S associations; new nested
  refs use stable N identifiers. Immutable, content-addressed sidecars contain the
  structured document, projection mapping, relationships and source snapshot.
- **Structured evidence:** table serialization retains cells, row/column offsets,
  headers and spans; native chart data is retained. CodeItem text is kept literally,
  including indentation. Native equations remain recognized source expressions.
  Supported script formatting is serialized explicitly with original text retained
  in provenance. No image descriptions are invented.
- **Provenance:** preserves all supplied provenance entries, coordinate origin,
  page/slide numbers, headings, parents, captions, labels and formatting. The full
  original structure remains available in its sidecar.
- **Evidence states:** distinguishes text, structured, awaiting interpretation,
  failed, incomplete, empty and structural elements. Non-quotable IDs stay in
  inventories and coverage; they do not become fabricated quote markers.
- **Strict serialization:** registered non-text units are explicitly non-quotable;
  genuinely missing, duplicate, contradictory or ambiguous markers still fail.
  Literal code excerpts preserve source whitespace. Oversized indivisible structured
  units are held instead of split in a way that detaches table headers or breaks code.
- **Context:** prioritizes heading ancestry, parents, children and captions, then
  adjacent continuity. The existing 1,000-character whole-unit limit remains. Context
  cannot become primary completion or authorize a context-only claim/exclusion.
- **Planning:** TXT retains existing TranscriptParser segmentation and timestamps.
  PDF, DOCX, PPTX and supported raster-image inputs route to Docling. Parser/source
  metadata participates in versioned manifest and request binding, budgeting and
  payload hashes. The existing runner uses this router and exact manifest chunks.
- **Authorization:** changed document plans cannot reuse old bindings. The fixed
  one-request gate hashes its exact approved source snapshot, so additive constructor
  defaults do not alter a frozen snapshot; schema validation and exact regenerated
  payload comparison remain mandatory. No approvals are created.
- **Coverage:** returned items receive only actually cited primary IDs, preventing
  one claim from marking an entire chunk or its figures covered. Notes reports expose
  non-quotable units and ingestion status. All nine adaptive rendering contracts remain.
- **OCR:** exceptions retain failure status and any extracted text; OCR boxes and
  confidence are retained. Only uniformly white rendered pages with no native/OCR
  text are verified blank. Partial pages remain retryable; resume checks saved status.
  Persistence failures clear completion and preserve recovered content. Old page
  attempts are archived, and a separate source-hash/DPI-bound OCR v2 output directory
  protects the historical OCR experiment. Corrupt manifests fail explicitly.
- **Determinism:** unavailable Docling confidence NaNs become JSON nulls. They do
  not cause repeated plans to compare unequal or generate invalid JSON metadata.

## Accounting for the 42 references

See `recovered_42_accounting.json` for every reference, recovered text, new canonical
ID, classification and rationale:

- 32 recovered educational elements: teaching paragraphs, headings, exercises,
  vocabulary and a caption. This is not an independent factual approval.
- Seven recovered furniture elements: page numbers and running book/chapter labels.
  They remain preserved; no whole-unit exclusions were granted.
- Three still-unresolved interpretations: literal fragments `to`, `1.` and `e`.
  Their text is recovered exactly; their meaning has not been reconstructed.
- Zero intentional exclusions and zero duplicate-representation dispositions.

All 15 picture units remain in `unresolved_visual_inventory.json`, with references,
pages, bounding boxes, provenance and limitations. Their children can be recovered
without pretending the picture itself has been interpreted. Corrupted recognized
text, including the repeated chapter heading, remains visible for review.

## Cross-format evidence and mock notes

| Input | Conversion exercised | Preserved evidence |
|---|---|---|
| Historical 11-page PDF | Replay of saved real Docling structure | All 131 texts; nested teaching, lists, captions; 15 unresolved pictures |
| Controlled TXT | Actual existing TranscriptParser | Source text; existing segmentation/timestamp behavior |
| Controlled DOCX | Actual installed Docling Word backend | Heading hierarchy, list, table, native equation, subscript and Code-style literal indentation |
| Controlled PPTX | Actual installed Docling PowerPoint backend | Slide references and native chart tabular data |
| Controlled PDF | Actual installed model-free NativePdfPipeline | Native PDF text and provenance; no claim of OCR/layout/table reconstruction |
| Raster OCR and partial conversion | Controlled fake OCR/conversion results | Failure, blank, partial, confidence, resume and persistence handling |

Each real controlled format runs through canonical units, chunking, bounded context,
request preparation, strict canonical-wire resolution, MockLLMProvider, mechanical
evidence validation, assembly, representation selection and notes rendering.
`controlled_structure` additionally exercises explicit formula, literal code,
table/span/formatting, caption and unresolved-picture contracts.

The mock deliberately echoes one source excerpt per text-bearing chunk. It does
not perform independent extraction or establish full knowledge coverage. The reports
retain uncited-source gaps and unreviewed fields. Preview notes are illustrative
pipeline outputs, not complete or verified study notes. Source-backed semantic
support remains a human-review task; no semantic score or human approval is created.

Examples: `controlled_docx/notes_preview.md`, `controlled_pptx/notes_preview.md`,
`controlled_structure/notes_preview.md`, and `saved_pdf_mock_preview/notes_preview.md`.
Original mock knowledge, request evidence and quality reports accompany each preview.

## Tests and preserved safeguards

Final applicable offline suite: **{stats['passed']} passed, {stats['failed']} failed,
{stats['skipped']} skipped**. See `regression_final_pass.xml` and `test_summary.json`.
The 19 skips are 18 pre-existing Windows model-conversion skips and the explicitly
disabled real OpenAI integration test. Network connections were blocked for the
suite. Mock HTTP transports exercised authorization, quota, recovery and rotation
without physical requests. The November 7 rejected response still fails. All nine
adaptive representations, strict schemas/evidence, one-time claims, five-slot safety
and the 85% quota policy pass their existing regressions.

Docling emits unavailable-confidence NumPy warnings on model-free conversions;
the metadata records null, never a claimed confidence score. Earlier failed test
attempts are retained. Recovery tests were updated to derive expected call counts
from the approved manifest because version-binding overhead can change chunk splits.
The offline runner is a real file so Windows multiprocessing claim tests can spawn.

SHA-256 checks confirm **{len(before)} protected files unchanged**, covering the saved
source baselines, Task 8/9 review artifacts, credentials file and live-state records.
No Groq calls, model downloads, package upgrades, automatic approvals, API-key changes
or historical quota edits occurred. A Git checkout was unavailable; exact delivered
file bytes and hashes are supplied in `code_snapshot` and `modified_file_hashes.json`.

## Enrichment and remaining limitations

- CodeFormulaV2 and Granite-Docling enrichment weights are absent from the inspected
  standard Hugging Face cache. No enrichment inference was attempted. Cached layout
  and TableFormer weights are not formula/code enrichment weights.
- Torch remains 2.14.0+cpu. The RTX 3050 is not enabled for Torch inference.
  The machine reported 15.69 GiB physical RAM; available memory was 1.4 GiB during
  testing. This is a point-in-time observation, not a model memory benchmark.
- Model-based PDF/image conversion requires an explicit existing local artifact
  directory. It is not silently replaced with native PDF mode and does not opt into
  downloading weights. Complete OCR/layout artifact staging and current Windows
  model-runtime health remain NOT_VERIFIED.
- Actual scanned-image OCR and fresh standard-model conversion of the historical
  PDF were not performed. Successful model-free PDF conversion does not establish
  diagram, chart-image, formula-OCR or reading-order accuracy.
- Superscript/subscript handling covers formatting provided by the installed backend;
  it does not add the newer PDF ScriptPositionOptions API. Unstyled Word paragraphs
  may already have lost indentation upstream; the adapter cannot reconstruct it.
- Table and native chart data are preserved, but generated explanations still need
  semantic review. Non-text visuals and the three source fragments remain unresolved.
- Structured/literal elements that cannot fit the existing budget are held for an
  explicit strategy, rather than fragmented unsafely or granted extra quota.
- The examples demonstrate source transport and mechanical grounding. Actual live
  educational quality improvement is NOT_VERIFIED, and no live run is authorized.

Next readiness: review the recovered source inventory and unresolved material. Any
future live experiment needs a newly generated version-bound manifest and separate
exact-request authorization. The independent Task 9 human-review pilot is unchanged.

## Files modified or added

{file_links}

Delivery-only scripts, fixtures, reports, sidecars, unapproved manifests and snapshots
are under this new Task 11 directory. They introduce no new production evaluation
framework or model dependency.
'''
    (OUT/'task11_report.md').write_text(report,encoding='utf-8')
    print(json.dumps({'tests':{k:stats[k] for k in ['passed','failed','skipped']},
        'protected_files_unchanged':len(before),'code_files':len(FILES),'report':str(OUT/'task11_report.md')},indent=2))


if __name__=='__main__':main()
