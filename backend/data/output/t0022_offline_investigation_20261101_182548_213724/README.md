# T0022 offline investigation

Release: NO-GO. No live requests, extraction/recovery jobs, implementation edits or historical modifications.

- [Source-ID provenance trace](source_id_provenance_trace.md)
- [Missing-content schema analysis](missing_content_schema_analysis.md)
- [Output-token analysis](output_token_usage_analysis.md)
- [Fact-coverage gaps](fact_coverage_gap_analysis.md)
- [Duplication/consolidation](duplication_consolidation_analysis.md)
- [Root-cause table](root_cause_table.md)
- [Exact proposed files/functions](proposed_minimal_changes.md)
- [Regression-test plan](regression_test_plan.md)
- [Final recommendation](final_recommendation.md)

Machine-readable evidence: output_usage_metrics.json, request_contract_checks.json, source_references.json and preservation_checks.json. Preservation baseline covers 165 implementation/test/historical files. No pytest tests were run: read-only consistency assertions were sufficient. Proposed tests have not been executed or implemented.

Recommendation: approve a narrow prompt/common-field/strict-raw-contract repair before considering another readiness review. No live smoke test is authorized by this investigation.
