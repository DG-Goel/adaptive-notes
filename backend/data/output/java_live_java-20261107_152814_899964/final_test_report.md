# Five-key full-scope run — November 7, 2026

## Fresh live execution
All 48 planned primary requests were attempted exactly once in the approved 1→2→3→4→5 sequence. Requests per slot: 10,10,10,9,9. 47 HTTP200 responses, one HTTP400, zero HTTP429. 47 chunks passed mechanical validation and generated 369 knowledge items. Classification of this fresh run remains PARTIAL LIVE EXECUTION because one response failed schema generation.

Failed request: java-20261107_152814_899964-0042, primary chunk 7, NOTES 2. Groq returned json_validate_failed, reporting missing procedure content. Original failure and conservative reservation remain recorded; no missing field was invented and the request was not retried on another key.

Provider-reported input: 143,859 tokens; output: 38,448; known subtotal: 182,307. The HTTP400 attempt supplied no usage, so total actual token consumption is unknown. Missing usage is not zero. Existing local/shared quota history remains charged, independently per organization. End-to-end durable-operation span: 601.644 seconds (about 10 minutes), physical-call duration sum 113.800 seconds. No automatic retries or credential rotation to retry a failed request.

The fresh-run-only artifacts remain partial_notes.md, extraction_results.json, source_coverage.json, request_audit.json, errors.json, quota_report.json, notes_quality_gates.json and run_summary.json. No prior run was overwritten.

## Separate audited cross-run preview
An accepted response exists for exactly the failed primary request in the previous real run: java-20261107_071532_898989-0042. Its source hash, exact serialized chunk and payload hash match the new request. The prior manifest's approved hash, durable successful operation, request hash, HTTP response receipt digest, expected model and finish reason were verified. The saved raw response passed the current canonical resolver and strict evidence/raw-schema parser against the current source. This reuse required ZERO extra API calls and did not change the failed current operation to success.

cross_run_preview/provenance.json records every retained current response and the one reused prior response. It identifies the origin request of each logical chunk. The combined artifact represents all 48 primary chunks and has accepted items for all 50 canonical source units. It contains 376 knowledge items before/after conservative consolidation. This is coverage of accepted extraction work, not proof that every important teaching point was captured.

Main combined notes: cross_run_preview/notes.md. Supporting artifacts: knowledge.json, assembled_notes.json, render_manifest.json, provenance.json and quality_report.json. Notes are explicitly UNVERIFIED and disclose cross-run provenance. The fresh-run-only preview remains separate, so reuse does not conceal the latest error or fabricate a new live success.

## Five gates for the combined artifact
Extraction-work completion PASS; structural validity PASS; semantic faithfulness NEEDS_REVIEW; educational completeness NEEDS_REVIEW; notes usability NEEDS_REVIEW. No overall educational-quality score or factual-accuracy guarantee is asserted. Topic-level omissions, claim support, technical correctness, scope, examples and readability still need review. No complete quality pass is claimed from source references or HTTP200 alone.

## Safety and validation
All five collaborating friends' keys participated with separately enforced 85% ceilings and ledgers. No external available-capacity requirement was introduced. No application implementation was changed during this run; the previously tested rotation/response-validation code was used. This turn performed the live execution and artifact checks, not a new mock benchmark. Cross-run reuse passed explicit hash, durable-operation, JSON-schema and exact-source evidence assertions. Source unchanged: True. Frozen Python artifacts changed: [].
