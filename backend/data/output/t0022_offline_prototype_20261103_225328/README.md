# Experimental offline two-stage extraction prototype

Release status is **NO-GO**.

- `prototype.py` contains the atomic fact schema, both validation stages, evidence reconstruction and the atomic return boundary.
- `fixtures.py` records the hand-authored T0022 claims and approved per-field support. `reference_facts.json`, `mock_stage_b.json` and `mock_single_stage.json` serialize the annotations and scripted responses.
- `test_prototype.py` exercises both successful and failing paths with local mocks.
- `compare.py` reproduces the comparison. `comparison.json` records the estimates.
- [Comparison and limits](comparison.md) and [Test results](test_results.md) document the findings.

The fixture reads the complete preserved T0022 source. Its ten reviewed facts are a targeted reference set for this exercise. The accepted result contains nine knowledge items because the division mismatch and its repair share one scoped item with two separate exact excerpts. The final-pi assignment error remains a separate item. Naming, conversion alternatives and increment each remain explicit.

Stage A matches quotations and canonical IDs, then applies a reviewer supplied by the caller. Stage B resolves every field pointer to one or more reviewed facts, expands the evidence locally, and uses the existing strict parser. The fixture reviewer accepts only manually approved combinations of category, field value and fact IDs. Semantic support is a separate decision from substring matching. Neither the fixture nor this prototype supplies a general semantic verifier.
