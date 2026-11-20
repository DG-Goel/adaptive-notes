# Quality reassessment — November 9, 2026

Readiness: **NEEDS_MORE_CORRECTION**. New overall score: **unassigned**. The previous 50/100 was provisional; no full independent review was performed to justify a new number.

## Actual run
50 physical requests across five keys; 48 accepted chunks; 458 extracted items. Two HTTP400 schema-generation failures (chunks 4 and 45), zero HTTP429, zero automatic retries. Reported input/output usage: 150,754 / 50,556 tokens (known subtotal 201,310). Actual total is unknown because the two failed responses did not report usage; reservations remain conservatively charged. Duration approximately 624.588 seconds, including quota waits. All original source and run artifacts were preserved.

## Comparison against the six criteria
| Criterion | Previous provisional rating | New evidence | New rating |
|---|---:|---|---|
| Completeness (30%) | 50 | 48/50 primary source IDs have accepted items; two failed requests leave gaps. Topic-level completeness is not established. | Unassigned |
| Accuracy/faithfulness (25%) | 50 | FizzBuzz ordering is now correct, but incomplete formula and reconstructed-code extraction remain. | Unassigned |
| Explanation quality (15%) | 50 | 74 explanations versus 45 previously; count alone is not quality. Error and correction are clearer, qualifications still need review. | Unassigned |
| Organization/readability (10%) | 25 | 46 source/topic sections versus one; audit JSON removed. Preview expands to about 22,090 words from 11,602. | Unassigned |
| Examples/code (10%) | 50 | 55 examples; 51 code-like examples trigger non-verbatim checks. These are fidelity flags, not a compiled error rate. | Unassigned |
| Traceability (10%) | 75 | Exact source associations and audit preserved; corrected FizzBuzz ordering lacks its explicit T0042 citation. | Unassigned |

## Key reviewed findings
**FizzBuzz:** the new procedure checks the combined divisibility case first; the demonstrated wrong result for input 15 is explicitly labeled incorrect. This fixes the prior behaviorally wrong procedure. However, the corrected procedure cites T0041, while T0042 explicitly provides the ordering correction. Full evidence association still needs correction.

**Mortgage:** raw output still says mortgage = P * R. T0031 continues with another expression and exponent, and T0033 mentions division. The source does not establish the complete equation in this text artifact. The student view warns that this is an unreviewed fragment; it is not repaired or certified.

**Code fidelity:** string examples still add declarations, variable names and output comments not present as literal source code. Student-facing source-passage fallback is safer, but the extraction defect remains. The current detector targets examples; procedure-step code requires additional review. No compilation benchmark was run.

**Qualifications:** the raw output still risks turning contextual preferences about nesting and repetition into blanket rules. T0042 discusses trade-offs, including preferring some duplication over a deeply nested solution.

**Repetition and usability:** 92 possible duplicate pairs, zero automatic exact merges. They are not 92 confirmed duplicates. The larger source-excerpt-based preview is safer than silently presenting fabricated source code, but less concise and still needs editorial grouping and review.

**Warning precision:** three formulas are flagged: two arithmetic expressions and the incomplete mortgage fragment. An unreviewed warning does not prove an arithmetic expression is incomplete; manual review is needed to reduce over-warning.

## Gates
Extraction completion FAIL; structural validity PASS; semantic faithfulness FAIL due unresolved critical warnings; educational completeness NEEDS_REVIEW; usability NEEDS_REVIEW. None of these failures is concealed by HTTP200 or source-ID coverage. Most item content remains NOT_REVIEWED; no global supported-claim percentage is invented.

## Validation and next work
376 readiness tests passed before execution. No implementation changed during the live run. Actual outputs were assessed after completion; no automatic repeat of failed chunks and no cross-run payload substitution were performed. Next work is source-backed review of code across all fields, complete instructional links and citation repair, original visual retrieval for the mortgage expression, targeted handling of the two missing source units, and independent topic/semantic review. Another full rerun alone is not a demonstrated solution to these persistent quality defects.
