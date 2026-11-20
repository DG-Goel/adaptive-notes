# Latest failure

The Groq openai/gpt-oss-120b call returned HTTP 200 and parseable JSON at its 3,944-token cap. The length guard stopped processing before the parser. Zero items reached publication. Offline checks found 14 valid raw contracts and canonical references, 13 mechanically valid items, and one evidence failure. The saved manual review classified eight items as supported and six as partially supported, including one wholly unsupported content field.

| Observation | Interpretation |
|---|---|
| A procedure quote inserts an ellipsis between the declaration mismatch and its repair | The combined claim needs two excerpts. The model serialized the gap as if the two passages formed a single quotation. This is consistent with summarization during consolidation. Its internal cause is unobserved. |
| Decrement gets a decrease-by-one rule and prefix/postfix behavior | The passage mentions decrement and demonstrates increment. The nearby increment discussion offers a plausible source of scope transfer, and general Java knowledge offers another. The saved prompt expressly prohibits this behavior. The model's cause cannot be identified from one response. |
| Final pi becomes an initialization rule and a universal constant relation | The source describes a particular compiler error and instance. Normalizing these as concepts and relations plausibly encourages generic wording. Reclassifying this as a fact alone would still leave room for overstatement. |
| The PI correction appears in a quote but lacks an explicit claim | Quotation presence does not measure teaching-fact coverage. A completeness check must inspect claim content. |
| The JSON closes successfully and still ends with length | The response exhausted the allowance. This does not identify which facts, if any, would have appeared with more generation. |

The two compilation errors remain separate in the manual assessment. The double-result declaration repair belongs only to the second event. Evidence of prefix/postfix increment exists elsewhere in the source, so the increment item also demonstrates a field with a valid quote whose excerpt covers only part of the claim.

Primary inputs are the latest smoke directory's assembled_messages.json, raw_model_response.json, technical_validation.json, manual_item_review.json and manual_quality_assessment.json. Earlier compact and repaired runs provide context. Their changed prompts and outcomes cannot isolate a causal effect.
