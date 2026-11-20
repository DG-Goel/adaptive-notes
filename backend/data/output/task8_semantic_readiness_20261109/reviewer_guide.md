# Continue the offline review

Open evidence_desk.html locally in your browser. Search by text, item ID or source ID; filter by semantic status and risk priority. Open a packet to see the exact field bundle, source quotation, mechanical results, related claims, bounded context and prior provenance. The desk shows up to 120 matching packets at once; narrow the search to find more.

Review every assertion in the bundle. Supply your identity and explicitly choose the reviewer type. Choose a disposition and explain the reasoning, especially qualifications, missing support and contradictions. Supported/partial decisions require the evidence and qualification checkboxes. Adding/exporting a draft does not itself certify knowledge or authorize an API call. Downloads remain local.

From the backend directory, validate an exported batch into a NEW output directory:

```powershell
.venv/Scripts/python.exe import_semantic_reviews.py --knowledge data/output/task8_semantic_readiness_20261109/review_input_knowledge.json --source data/output/java_live_java-20261109_022409_842270/source_document.json --history data/output/task8_semantic_readiness_20261109/decision_history.json --relations data/output/task7_educational_completeness_20261109/duplicate_decisions.json --legacy-pin data/output/task8_semantic_readiness_20261109/legacy_provenance_pin.json --decisions PATH_TO_YOUR_EXPORTED_JSON --output data/output/task8_review_round_01
```

The importer validates current text/source bindings and hash-chain integrity before creating output. It never edits knowledge, authorization, credentials or quota files. It preserves previous history and writes a resolved workspace and another local evidence desk. Rejecting a stale decision requires renewed review of the changed packet; do not edit hashes to force acceptance.

This is a local static HTML tool. Static HTML/data/JavaScript checks passed, but visual browser testing was blocked by the available UI policies. Actual browser usability and an independent source/technical review remain outstanding.
