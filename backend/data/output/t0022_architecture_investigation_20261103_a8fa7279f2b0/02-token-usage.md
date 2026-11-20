# Token and size accounting

| Measure | Latest |
|---|---:|
| Provider prompt tokens | 2,035 |
| Completion tokens | 3,944 |
| Reported reasoning tokens | 2,648 (67.14% of completion) |
| Completion remainder after subtracting reasoning | 1,296 |
| Total tokens | 5,979 |
| Local estimated input / output cap | 2,856 / 3,944 |
| Provider total / completion time | 8.363 s / 8.253 s |

The remainder is an accounting difference, not an independent tokenization of visible JSON. The previous repaired run used 2,398 reasoning tokens out of 4,000 completion tokens. Two runs provide no estimate of the effect of an arbitrary reasoning setting.

| Saved prompt block | Characters |
|---|---:|
| System introduction and grounding rules | 2,968 |
| System contrasts, excluding the 10-character heading | 1,483 |
| User source block including its opening marker | 2,589 |
| User category/common-field contracts | 1,354 |
| User worked evidence example | 619 |
| User header / skeleton / trailer | 224 / 204 / 39 |

These are exact character counts, not per-instruction token measurements. Grounding and its contrasts dominate the instruction text. The source is the largest user block and the category contract is the largest user instruction block. Provider usage does not attribute reasoning tokens to individual instructions.

The final JSON is already compact at 5,439 characters. The serialized evidence-array values account for 2,404 characters (44.2%), including 1,289 quote characters. Serialized content values account for 941 characters, with additional repeated text in subtype fields. Content ranges from 5 to 15 words per item. The largest compact item is 582 characters. Four concepts, four definitions, two examples, two facts, one procedure and one relationship account for 14 items. There is no evidence of individually verbose prose or a meaningful absolute item-count limit violation. The duplicated constant relation and repeated common/subtype text are identifiable overhead. Blindly reducing the item count could worsen coverage.
