# Human reviewer handoff — Task 9

The pilot is awaiting a real independent reviewer, as requested by the user. Existing source-comparison statuses are historical assistant judgments, not completed pilot decisions. The sample contains difficult and easier cases across 30 exact-evidence bundles / 47 fields. Its atomic claim count is unknown.

Open pilot_desk.html locally in your normal browser. Alternatively, from the backend directory start the approved read-only loopback test server:

```powershell
.venv/Scripts/python.exe data/output/task9_review_pilot_20261109/serve_review_desk.py
```

Visit the printed pilot URL in the browser on that computer. Only three named HTML review pages are served, with no directory listing or write/upload route. It binds 127.0.0.1 only. Stop it with Ctrl+C when done. The agent's test server has already been stopped.

Search by claim, item/source ID or quotation; filter by current status and risk priority. Use Source buttons to jump to exact quotes, View item to inspect the other fields as context, and the Review controls link to return directly to the form. Full metadata remains in expandable panels. Prominent warnings distinguish incomplete equations, adverse dispositions and missing evidence. Neighbor context gives no new evidence permission.

Make your own source-backed judgment for the whole bundle: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED or INCONCLUSIVE. Do not mistake exact quotation for factual truth. Check all claims, scope, exceptions, source errors and deliberate-error/correction roles. Use INCONCLUSIVE when the needed original visual/code or technical verification is unavailable. NOT_REVIEWED is a reset, not a completed pilot judgment.

Enter your real identity and select Human only if a person is actually performing this review. Explain your judgment. Positive/partial decisions need the evidence/qualification checkboxes. Adding a draft does not certify the knowledge. Unsent form entries survive navigation in the current tab, but session drafts are not persisted to the server; export before closing/reloading. Revisiting a bundle can create a genuine follow-up record. Re-importing the same decision, including a different member order or equivalent timezone spelling, cannot inflate counts or restore an approval later withdrawn.

Export after completing the pilot and supply the file for validated import. A pilot completion count must use distinct, currently valid reviewed bundles; export rows, history records, fields and atomic claims are different measures. Any source/text/scope change requires renewed review of affected bindings. Extensive packets are also available in pilot_review_packets.md and pilot_evidence_packets.json.

The following command validates an actual future export into a NEW directory; it was not run with human decisions during Task 9:

```powershell
.venv/Scripts/python.exe import_semantic_reviews.py --knowledge data/output/task8_semantic_readiness_20261109/review_input_knowledge.json --source data/output/java_live_java-20261109_022409_842270/source_document.json --history data/output/task8_semantic_readiness_20261109/decision_history.json --relations data/output/task7_educational_completeness_20261109/duplicate_decisions.json --legacy-pin data/output/task8_semantic_readiness_20261109/legacy_provenance_pin.json --decisions PATH_TO_YOUR_EXPORT --output data/output/task9_human_review_round_01
```

Source comparison by a genuine independent person and independent technical verification of an erroneous source are different scopes. Record any technical checks honestly; do not mark a source-only comparison as an executed/independent technical check. A name entered into a local form is a self-declared identity, not cryptographic authentication. No release certification or quality score follows from the sample alone.
