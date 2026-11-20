# Partial notes quality review

Verdict: not ready for independent study or publication. There are useful source-linked Java facts, but semantic errors, inherited transcript errors, missing teaching context, and limited educational structure remain. Completing more API calls alone will not resolve these problems.

## What was checked

Offline structural checks cover all 420 items and all 1,285 stored evidence records (including separate evidence for aliased fields). Semantic review used 30 evenly spaced fact/evidence pairs plus targeted high-risk passages. This is an agent review, not a human approval or an exhaustive accuracy certification. Audio/video was not replayed, so transcript defects cannot be assigned conclusively to the speaker or ASR. No Groq calls, OCR, retranscription, note edits or source changes were made.

## Quantitative findings

- Stored: 419 facts and one definition. There are no structured explanations, examples, procedures, formulas, relationships or concepts.
- All 420 IDs appear in Markdown, but 45 content candidates are withheld and represented by warnings/source excerpts. ID presence does not establish usable learning content.
- 94 of 124 speech passages have at least one citation (75.81% passage presence). This is not 75.81% topic coverage: one fact can cite an otherwise under-covered passage, and some uncited material is promotional.
- All 1,285 evidence quotes match their saved source offsets; all source IDs resolve. This validates provenance, not entailment or Java correctness.
- Zero citations promote the 501 unverified visual units. This preserves safety, but the main notes do not recover the lecture's screen demonstrations.
- The Markdown has no fenced code blocks, no visible HH:MM:SS labels, and no VISUAL_CONTEXT_REQUIRED marker. The formula gap remains available in the separate source-gap artifact.
- The 16,890-word Markdown repeats the generic paraphrase warning 363 times (4,719 words of repeated warning text, about 28% of its whitespace word count). The generic Source G... headings give little topic guidance.
- The pipeline already marks publication ineligible: extraction completion FAIL, educational completeness FAIL, semantic faithfulness NEEDS_REVIEW, notes usability NEEDS_REVIEW. Structural validity alone passes.

## Important errors and ambiguities

| Item | Finding | Source/renderer distinction |
|---|---|---|
| FCT_0383 | Claims loops improve nesting compared with repeated if-else statements. The cited source is comparing two if-else implementations before introducing loops. | Unsupported model paraphrase; remains visible. |
| FCT_0163 | Says String-array elements default to empty strings. Java reference components default to null. | Inherited from G00049 transcript; remains visible. [Java specification](https://docs.oracle.com/javase/specs/jls/se25/html/jls-4.html#jls-4.12.5). |
| FCT_0401 | Says brick statement and continuous statement. | Inherited transcript terminology; visible beside otherwise correct break/continue material. Requires source confirmation, not silent correction. |
| FCT_0073 | Uses lowercase main in a case-sensitive class-name example despite the source's explicit capital-M instruction. | Speech-derived literal characters remain ambiguous; do not approve as code. |
| FCT_0295 | Mortgage is described as multiplying by one expression and dividing by another. | A source fragment, not a usable formula; its gap needs a visible link. Never reconstruct it. |
| DEF_0001 | Short-circuit evaluation is described as simply returning true without naming the OR condition. | Context-dependent example presented as a general definition. |

FCT_0261's candidate confuses next with a byte parser, but its text is withheld in Markdown; the renderer shows an unresolved source excerpt. Oracle documents next() as returning String and nextByte() as reading a byte. This is evidence that some safeguards work, not an additional fully displayed wrong code example. See the [Scanner documentation](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Scanner.html#next()). FCT_0347 and the incorrect FizzBuzz candidate FCT_0375 are also withheld. The detailed findings retain this distinction.

## Missing learning material and readability

The uncited G00044/G00045 contain escape sequences and the Windows-path demonstration. G00117 contains for-each limitations, and G00118-G00122 contain mortgage input validation, scope errors and corrections. These are meaningful missing lessons, not merely end-of-video promotions. G00078's mortgage explanation is also uncited, although some related monthly-interest facts survive elsewhere.

Many retained facts are transcript fragments: Use this for printing multi-dimensional arrays (FCT_0172), Running the program produces output (FCT_0272), Beautiful (FCT_0410), and Take a look (FCT_0418). They do not help a learner without the missing visual context. There is also repeated explanation/transition material; FCT_0197 and FCT_0322 are exact normalized duplicates. Consolidation retained every item.

The notes contain a useful base of facts about primitive types, assignment, methods, strings, arrays and flow control. Their source links and unresolved labels are valuable. They currently behave more like an extraction audit with scattered teaching points than a coherent study document.

## Recommended repair order

1. Investigate semantic failures in accepted paraphrases and the high rejection rate. Do not weaken evidence checks to increase counts.
2. Add explicit, source-linked review for transcript terminology and technical mistakes. Preserve literal speech and keep external corrections separate.
3. Put unresolved formula/code markers and visual-supplement links beside affected lessons. Verify exact characters before approving OCR candidates.
4. Remove low-information fragments, consolidate repetition, and organize accepted points under topic headings with timestamps. Keep detailed warnings/provenance accessible without repeating them before every point.
5. Complete the missing educational categories and lessons after the above quality problems are understood. More records are not a substitute for correctness.

This review does not alter the notes, their source readings, authorization records, or the publication gate. Machine metrics, exact item/source references, source timestamps, sampled IDs, and input hashes are saved alongside this report.
