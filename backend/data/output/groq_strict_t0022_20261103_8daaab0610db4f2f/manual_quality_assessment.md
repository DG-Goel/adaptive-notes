# T0022 strict smoke test: FAIL

Release NO-GO. One Groq openai/gpt-oss-120b request; zero retries, rotation, fallback or recovery.

HTTP 200 and valid JSON; finish_reason length at 3944 output tokens. Input 2035; total 5979. Zero items accepted by pipeline.

Offline checks on unmodified JSON: 14/14 raw contracts and canonical source references valid; 13 mechanical evidence passes, 1 failure. The procedure quotation invents an ellipsis joining noncontiguous passages. These offline results do not override the live truncation failure.

Semantic item counts: {"Partially supported": 6, "Supported": 8, "Unsupported": 0, "Contradicted": 0, "Inconclusive": 0}. Unsupported field: decrement behavior and prefix/postfix applicability are not in the source.

| Raw item | Classification | Manual finding |
|---|---|---|
| /concepts/0 | Partially supported | Name and uppercase convention supported; preserve pi scope for equivalence. Specific pi-to-PI correction remains only in evidence. |
| /concepts/1 | Partially supported | Name and local assignment prohibition supported; added initialization qualification is not. |
| /concepts/2 | Supported | Increase-by-one and prefix/postfix increment applicability are supported in the complete source. Selected quote does not cover the prefix/postfix portion; an additional excerpt is needed. |
| /concepts/3 | Partially supported | Name supported, all behavioral content unsupported. This is a mention-only operator. |
| /definitions/0 | Supported | The arithmetic operator class and enumerated operators are stated. The short arithmetic-operations description reasonably paraphrases the complete lecture context. |
| /definitions/1 | Supported | Term and remainder definition directly supported; no unstated modulus symbol added. |
| /definitions/2 | Supported | Term and produces-a-value definition directly supported. |
| /definitions/3 | Partially supported | Term supported; preserve the demonstrated-number scope rather than generalize the local label. |
| /examples/0 | Supported | Spoken addition example preserves explicitly stated 13 without invented Java code. Addition label is confirmed immediately after the selected excerpt. |
| /examples/1 | Supported | Spoken increment example preserves int X, initial 1 and printed 2; no code declaration or output is reconstructed. |
| /facts/0 | Supported | Whole-number division rule is explicitly stated by lecturer. No unstated fractional truncation mechanism added. |
| /facts/1 | Partially supported | Alternatives preserved, local scope lost. Unicode nonbreaking hyphen in paraphrase is typography, not a fabricated quotation. |
| /procedures/0 | Supported | Procedure name, change from integer declaration to double, and matching double expression are supported by complete source. The evidence fabricates a stitched quote using ...; preserve two separate exact excerpts instead. |
| /relationships/0 | Partially supported | Terms occur in source; universal relation duplicates and broadens constant concept content. |

Full field-by-field claims, classification reasons and exact evidence are in manual_item_review.json.
## Coverage
| Explicit fact | Finding |
|---|---|
| Increment demonstration 1 to 2 | Present in raw /examples/1; zero pipeline acceptance. Both explicitly stated values and increment action retained as prose. |
| Final-variable pi assignment compilation error | Partially represented. /concepts/1 states a general assignment prohibition with an unsupported initialization qualification. The local pi compilation-error occurrence remains only in evidence, not a clear source-scoped extracted error account. |
| Separate integer-declaration/double-expression error and declaration repair | Present in raw /procedures/0; invalid evidence. Name/step/content convey the type mismatch and declaration change to double; supporting quote is artificially joined using ... and fails exact matching. This does not repair final pi assignment. |
| Float or double alternatives | Present but scope weakened in /facts/1. Both alternatives are explicit. Here/these numbers/division-example qualification is omitted, producing an overbroad standalone conversion recipe. |
| Specific pi to PI naming correction | Missing from claim fields. Uppercase convention is stated in /concepts/0, and pi-to-PI appears in its quotation, but no explicit correction claim is extracted. PI is no longer falsely classified as an alias. |

## Comparison
| Test | Returned | Accepted | Finish |
|---|---:|---:|---|
| Earlier strict JSON failure | 0 | 0 | None |
| Compacted prompt | 15 | 0 | stop |
| Previous repaired prompt | 21 | 0 | length |
| Current strict raw-contract prompt | 14 | 0 | length |

No mechanical validator establishes semantic entailment. Common fields and canonical IDs improved, but faithfulness, completeness and consolidation remain inadequate. Stop for review; no further request is authorized.