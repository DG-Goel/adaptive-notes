# Current architecture

KnowledgeExtractor._extract_from_chunk assembles the full source, canonical IDs and shared system rules. It budgets those exact messages and calls the Groq adapter. The adapter rejects a length finish before _parse_response runs. Strict parsing checks the raw contract before constructors fill defaults. The evidence validator subsequently checks exact excerpts, canonical membership and coverage of populated JSON Pointer paths. A failed response contributes zero items to the chunk.

One model response currently has to discover facts, preserve scope, choose categories, consolidate, write repeated schema fields, copy excerpts and attach field paths. The category and consolidation work is conceptually separable from discovery. Its reasoning cost is unmeasured. A narrower first-stage contract could reduce the number of decisions made while reading the transcript. It could also add an intermediate paraphrase and shift the same reasoning burden into structuring.

Canonical IDs and common fields worked on the latest response. Preserve these controls. Exact substring checks catch stitched quotes but allow a mention of decrement to be cited for a claim about decrement behavior. Mechanical acceptance and semantic support remain separate gates.

Code references are backend/app/extraction/extractor.py at _extract_from_chunk, _parse_response, _validate_strict_raw_contract and _attach_source_evidence, backend/app/extraction/prompts.py at build_extraction_prompt, backend/app/extraction/llm_provider.py at the length guard, and backend/app/extraction/token_budget.py at calculate_budget and rolling usage tracking.
