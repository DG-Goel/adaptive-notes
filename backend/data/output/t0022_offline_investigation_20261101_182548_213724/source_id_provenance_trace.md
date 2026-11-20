# Source-ID provenance trace
Release NO-GO. No extraction or ingestion was rerun. Exact inspected references are in source_references.json.

| Stage | Observed behavior |
|---|---|
| TranscriptParser.parse / _create_source_unit | Position is i+1, and source_id is T plus four-digit position. Position 22 gives T0022, with transcript_segment_21. IDs depend on the segmentation; the smoke used the frozen canonical artifact, not a new parse. |
| SourceUnit / SourceDocument | Plain string source_id; no renaming validator. Read-only model serialization roundtrip equals the original dictionary. |
| ContentChunker.chunk / _create_chunk | JAVA_CHUNK_000 originates from document_id JAVA plus first chunk counter 000. It is a scheduling identifier. source_units remains [T0022]; text contains [T0022]. |
| AdaptiveChunkSplitter._create_sub_chunk | Appends _SUBn to the scheduling ID; canonical source IDs and visible markers remain unchanged. This smoke disabled splitting; none occurred. |
| Source serialization | run_pipeline.py uses source_doc.model_dump(). The smoke loads SourceDocument.model_validate_json. Previous/latest source JSON bytes are equal and preservation hashes match. No serialization rewrite is demonstrated. |
| Prompt assembly | build_extraction_prompt receives chunk.text_content and chunk.chunk_id. User message displays CHUNK ID: JAVA_CHUNK_000 above source marked [T0022]. Each ID occurs once. Wire messages equal the saved messages. |
| Raw response | All 21 items and 23 evidence entries use JAVA_CHUNK_000 as source ID. The wrong source reference is already in HTTP response JSON, before parser/serialization. |
| Extractor parsing | extract initializes valid_source_ids and _evidence_sources from canonical SourceUnits. _validate_source_ids drops invalid IDs; it does not map canonical IDs to chunk IDs. |
| Strict evidence | _attach_source_evidence rejects raw/normalized reference differences, invalid source/chunk membership, bad quotes and missing field paths. Latest normal execution stops earlier at the provider length guard; offline validation rejects all items. |

Conclusion: no local code overrides T0022 with JAVA_CHUNK_000. The model selected a prominent scheduling label for provenance. The prompt's phrase actual chunk markers and its unqualified CHUNK ID header leave the two identifier roles insufficiently distinguished. Prompt-label ambiguity plus model noncompliance is the likely explanation, not a confirmed deterministic mapping defect. The previous request had the same user header but used T0022 correctly, so one exact causal trigger is not established.

Propose explicit permitted canonical source IDs from the actual chunk, and mark the scheduling label non-citable. Do not rewrite returned IDs automatically, especially for multi-source chunks. No ingestion, schema, chunker, splitter or serialization change is justified by this evidence.
