# Task 1: source processing and exclusions

## Root cause
The archived November 7 response simultaneously cites and excludes Q0006, Q0011–Q0014. The strict resolver correctly rejects it, and the regression replays the original response without changing it. Q0006 straddles advertising and JDK teaching; Q0011–Q0014 teach functions, returns, parameters and bodies. The model made incorrect relevance decisions. Prompt ambiguity contributed: it directed exclusion of promotional content without explicitly distinguishing irrelevant portions from whole mixed excerpts. The schema enforces shape but cannot establish relevance or mutual exclusion with evidence references. Catalog excerpts are bounded at sentence/whitespace boundaries (500 characters), so unpunctuated transcripts can split teaching statements. Canonical IDs were not lost in this failure. Incorrect/incomplete field references remain a separate semantic support issue.

## Implemented policy
Source units carry six explicit educational statuses: educational, noneducational, mixed, noisy_educational, incomplete_educational and uncertain. Layout roles do not authorize deletion. Whole-unit exclusion requires noneducational status, a reason and explicit whole-unit review. The exclusion validator rejects unknown/duplicate IDs and cited-and-excluded IDs. Mixed/noisy/incomplete/uncertain units remain eligible. No keyword classifier pretends to establish semantic relevance automatically.

The extraction prompt now describes whole-excerpt exclusion and mixed content across subjects. The resolver still rejects contradictory/duplicate/unknown exclusions without repairing output. Empty output preserves unused excerpts as unresolved with review_required; it no longer forces a model to exclude every excerpt to return no items. Excerpt exclusion never means the entire canonical source unit was excluded. This changes empty-result policy deliberately, not evidence requirements.

## Source model and provenance
Existing fields retain canonical IDs, document IDs, page, section, bbox, parent and Docling reference. Added extensible available provenance, interpretation limitations and educational assessment. Transcript provenance now records original segment index and available timestamp. Fixed single-line/line-delimited HH:MM:SS transcripts bypassing timestamp detection. MM:SS-only timestamps remain unsupported. Parser normalization and segment merging mean original-file character offsets are not guaranteed; IDs are scoped to document identity and parser options, not immutable across re-ingestion with different settings. Filename-derived document IDs can collide across different files with equal stems.

Chunk metadata lists sources needing review and nontext sources requiring interpretation. No page, slide, OCR confidence or coordinates are invented. Provenance metadata can hold format-specific information, but this task does not establish that Docling populates every such field. Existing Docling conversion uses first available provenance location; multi-region and native slide/cell details need further adapter work.

## Chunking and context
Offline reproduction: 50 units, 18 base chunks, 32 initial budgeted requests. These counts are computed. The change is due to full serialized prompt/schema input estimation plus the 3,000-token completion reserve under the 6,800-token ceiling. Existing lossless split tests validate spans and order. No replacement chunking algorithm was introduced.

Real deficiencies: unknown/noise/furniture roles previously disappeared from chunking; now retained unless explicitly reviewed for exclusion. Section/size boundaries and the excerpt catalog can separate definitions, procedures, formulas, captions, code, comparisons and qualified claims. Added deterministic bounded adjacent-context selection with separate primary/context IDs and explicit over-budget/nontext limitations. It preserves canonical IDs and does not mutate primary completion accounting. It is an integration utility, not automatically appended to existing authorized requests. It cannot guarantee long-range cross-page or cross-slide dependencies. Task 2 must serialize/budget context explicitly and regenerate request authorizations, then extend evidence mapping to contextual IDs without treating them as completed primary targets. Existing exact-plan coverage assertions still assume every source is primary; integrating reviewed exclusions requires explicit excluded-source accounting, not bypassing those assertions.

## Format support and limitations
TXT/transcript ingestion is implemented and tested with the actual transcript parser. Generic Docling conversion exists for PDF and office inputs; PDF OCR is configurable and documented as potentially slow/hanging on Windows. No new real PDF, DOCX, PPTX or scanned-file conversion was performed. Synthetic PDF-derived heading/table, PPTX-derived slide and ambiguous OCR fixtures validate policy and metadata only. They do not prove parser quality. DOCX paragraph/cell locations and PPTX native element locations remain dependent on available converter provenance. Visual-only formulas, diagrams and images remain uninterpreted by text extraction and require explicit review. OCR accuracy is not certified. Research papers and technical manuals use generic document conversion, with no specialized semantic parser verified here.

## Exact implementation files modified
- app/ingestion/educational_policy.py (new)
- app/ingestion/transcript_parser.py
- app/models/source.py
- app/models/knowledge.py
- app/extraction/chunker.py
- app/extraction/source_context.py (new)
- app/extraction/grounded_fields.py
- tests/test_universal_source_policy.py (new)
- tests/test_grounded_fields.py

Deliverable files: this report, evidence.json and ../task1_verified_tests.xml.

## Tests and safety
New controlled fixtures cover mixed Java advertising/teaching, mathematics, biology, chronology, qualified research claims, PDF-derived tables, slide-derived context, uncertain OCR, noneducational and empty educational results. Tests exercise explicit exclusion review, unknown/duplicate/cited exclusions, stable IDs, primary coverage, bounded context, nontext limitations, actual timestamp parsing and archived-response rejection. Synthetic fixtures are labeled as synthetic.

No API calls or live extraction. No provider/model change. Frozen artifact hashes are unchanged. Historical response hash is recorded in evidence.json. Prompt/source-model changes invalidate historical request manifests by design; historical artifacts were not regenerated or edited. Authorization and quota code remain unchanged. Task 2 has not begun.

Final applicable regression result: 261 passed, 0 failed, 0 skipped. The initial timestamp regression failed during development and passed after the parser fix. No live validation was performed, as requested.
