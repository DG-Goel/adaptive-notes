# Coverage gaps and classifications
The two compiler errors are distinct. The declaration change to double repairs the integer-declaration/double-result mismatch, not the final-pi assignment error. The pi-to-PI rename expresses a convention, not a repair for final reassignment.
| Fact | Exact source excerpt | Latest result | Preservation recommendation |
|---|---|---|---|
| Final-variable pi assignment error | cannot assign a value to final variable pi | Missing; final-variable terminology survives but not the diagnostic. | Retain the scoped attempted-assignment error. No repair for final reassignment is supplied in this passage. |
| Separate double-expression/integer-declaration error | we have a compilation error because on the left side we declared an integer but here the result of this expression is a double | Missing; conversion narration does not preserve the error cause. | Retain the incompatible declared/result types as the demonstrated cause. |
| Double declaration repair and observed floating result | so to fix this problem we need to change this to double now when we run this program we get this floating point number | Missing from returned content. | Combine with the immediately related type-mismatch cause, retaining spoken repair without Java reconstruction or an invented numeric result. |
| pi to PI naming correction | by convention we use all capital letters to name constants so this should be PI | Quote exists, but PI is an alias of the general constant concept, not a naming-correction claim. | Preserve uppercase convention and this instance correction together; remove the PI concept alias. |
| Increment demonstration 1 to 2 | we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2 | Present in raw /examples/2; mechanically unaccepted. | Preserve both values and action in one spoken example, not reconstructed code. |
| Float or double alternatives | if you want to get a floating-point number here you need to convert these numbers to a float or a double | Present in raw /explanations/1; mechanically unaccepted. | Retain alternatives and local scope without a universal one-operand/double requirement. |

Why missing: the complete source includes these passages; input truncation is ruled out by full-source and wire-message checks. The response front-loads ten concepts and repeated definitions, then ends after one fact under a length finish. Exhaustion/front-loading/compliance are likely contributors; their individual causal shares are unproven.

Two partially supported items:
- /concepts/0: constant is supported; final variable describes pi but is not an explicitly established unrestricted synonym; PI names the demonstrated instance and is not an alias of constant. Preserve pi context and naming correction instead.
- /definitions/0: constant is a supported term; a final variable or a constant repeats source words but is circular as a definition and strips instance context. Use a scoped fact/explanation, not a fabricated formal definition.

The other nineteen item-level supported classifications concern populated claims only. All twenty-one still fail provenance/evidence, and all omit content. Exact quotation matching never establishes entailment. No fact is recovered by this investigation.