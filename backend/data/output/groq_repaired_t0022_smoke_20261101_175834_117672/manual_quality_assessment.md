# T0022 controlled smoke test: FAIL

Release: NO-GO. One API request; zero retries, rotation or fallback.

HTTP 200, valid JSON, finish_reason length. Usage: input 1919, output 4000, total 5919. Provider truncation guard accepted zero items.

Semantic item classifications: {"Partially supported": 2, "Supported": 19, "Unsupported": 0, "Contradicted": 0, "Inconclusive": 0}. These classifications do not waive provenance/evidence failures.

| Raw item | Classification | Field findings |
|---|---|---|
| /concepts/0 | Partially supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /aliases/0: Partially supported (final variable describes pi alongside constant; it is not explicitly established as an unrestricted alias for every constant.); /aliases/1: Unsupported (PI is the corrected name of the demonstrated constant, not an alias for the general concept constant.) |
| /concepts/1 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/2 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/3 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/4 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/5 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/6 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /aliases/0: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/7 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /aliases/0: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/8 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /aliases/0: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /concepts/9 | Supported | /concept_name: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /definitions/0 | Partially supported | /term: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /definition_text: Partially supported (The words occur exactly in a statement about pi. Recasting a final variable or a constant as the definition of constant is circular and removes the instance context.) |
| /definitions/1 | Supported | /term: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /definition_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /definitions/2 | Supported | /term: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /definition_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /definitions/3 | Supported | /term: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /definition_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /explanations/0 | Supported | /topic: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /explanation_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /explanations/1 | Supported | /topic: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /explanation_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /explanations/2 | Supported | /topic: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /explanation_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /examples/0 | Supported | /exemplifies: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /example_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /examples/1 | Supported | /exemplifies: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /example_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /examples/2 | Supported | /exemplifies: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.); /example_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |
| /facts/0 | Supported | /fact_text: Supported (Supported by the complete T0022 passage; see item note for scope and quotation-association qualifications.) |

All 21 items use noncanonical source IDs and omit content evidence. Quotations themselves exactly match T0022. Strict validation was not reached in the original pipeline because truncation was detected first; offline replay rejects all 21.
Coverage: increment 1 to 2 and float/double alternatives appear in raw content. Both distinct compilation-error accounts and the double-declaration repair are missing. Naming correction appears only in quotation and is misclassified as an alias.
Compared with the prior test: 21 vs 15 raw items; 0 accepted in both; length vs stop; 4000 vs 3611 completion tokens. Earlier invented code/symbol details absent, but provenance, common-field compliance, consolidation and truncation regress.
Exact whole-number statement is duplicated as explanation and fact. Multiple concept/definition pairs and five separate operator-name concepts add fragmentation. No reconstructed Java code/formulas found in final JSON.
Recommend offline investigation and a narrow proposal before any future request. Full field-level review, exact evidence and source coverage are in manual_quality_assessment.json.