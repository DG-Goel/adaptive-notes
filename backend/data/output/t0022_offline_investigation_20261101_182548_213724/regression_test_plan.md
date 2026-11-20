# Regression-test plan

No pytest modules were run during this investigation. Code tracing, read-only JSON analysis, preservation hashes and SourceDocument roundtrip assertions were sufficient. No ingestion/extraction/recovery job ran. The historical 256-pass result was reviewed, not rerun.

After approval, proposed tests:

1. Single-source chunk JAVA_CHUNK_000 contains canonical T0022. Outgoing prompt explicitly distinguishes roles and permits only T0022; complete source and all eight category contracts survive.
2. Multiple canonical units and split children retain canonical IDs. Root, parent and child scheduling labels remain invalid evidence IDs. Test existing chunker/splitter locally, no provider calls.
3. Source-model JSON roundtrip preserves source_id and transcript text. Never regenerate IDs from a changed segmentation.
4. Latest unmodified 21-item fixture fails strict checks. A separate canonical-ID-only-corrected synthetic copy still fails missing content; a missing-content copy with /content evidence also fails raw required-key checks. Never edit historical fixtures or call repaired copies accepted model output.
5. Strict missing/null/wrong-type common-field checks identify raw category/index. Define empty-string policy explicitly rather than silently introducing one. Cover all eight subtype contracts and evidence paths.
6. strict_evidence=False preserves constructor defaults, serialization and metadata compatibility. Valid strict output retains separate /content and main-text paths even when one exact excerpt supports both.
7. Existing multiple aliases, steps, prerequisites, nested dictionary RFC 6901 escaping, omitted optional fields and missing leaf regressions remain unchanged; no parent-path acceptance.
8. Matching-but-misleading quotations remain mechanically distinct from entailment; semantic_entailment_verified stays False. PI substring appearance cannot be treated as semantic proof of an alias.
9. Human-authored coverage reference cases separately preserve final-pi assignment error, double-expression/declaration error+repair, increment 1-to-2, float/double alternatives and pi-to-PI naming convention. These test representation/contracts, not real-model quality.
10. Prompt consolidation tests preserve distinct facts and forbid quota-driven item deletion. Existing duplicates/fragmentation fixtures support a manual review checklist, not automatic merging based only on word overlap.
11. Mock finish_reason length with valid JSON: existing guard still rejects, exactly one request under smoke configuration, no credential rotation or fallback/splitting. Raw usage retains reasoning-token details in diagnostic artifacts; no provider behavior change.
12. Complete request assertions retain Groq, openai/gpt-oss-120b, json_object, strict evidence and existing computed budget. No manual allowance increase, source/instruction truncation or model switching.

Suggested focused command after implementation, NOT executed now:

.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/test_extraction_grounding.py tests/test_extraction_unit.py tests/test_serialization.py tests/test_chunk_splitting.py tests/test_adaptive_splitting_advanced.py tests/test_token_budget.py tests/test_truncation_handling.py tests/test_groq_provider.py tests/test_extraction_reliability.py
