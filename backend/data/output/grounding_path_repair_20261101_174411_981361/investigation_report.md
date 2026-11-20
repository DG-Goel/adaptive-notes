# Controlled grounding repair analysis

Release: NO-GO. Offline only; zero live requests.

## Identity caveat

The raw response has no knowledge_id fields and the failed pipeline accepted zero items. Stable raw JSON paths identify the ten reviewed outputs. The historical offline replay restarted IDs for every item; its repeated diagnostic IDs are not authoritative pipeline IDs.

## Ten flagged items: supported and unsupported portions

| Knowledge ID / raw path | Exact claim | Exact evidence quotation | Supported portion | Unsupported portion / missing context | Likely cause | Recommended correction |
|---|---|---|---|---|---|---|---|
| Not assigned; /concepts/1 (offline: CON_0001) | An expression using arithmetic operators such as addition, subtraction, multiplication, division, or modulus. | we have addition subtraction multiplication division and modulus | The arithmetic operator list is supported, and the wider passage introduces arithmetic expressions. The association is plausible; the earlier blanket unsupported label is too strong. | The selected quote alone does not establish the synthesized definition. Preserve lecture framing rather than introduce a textbook definition. | model completion; field association | Prefer: The lecture introduces arithmetic expressions and lists addition, subtraction, multiplication, division and modulus. Cite both the introduction and list. |
| Not assigned; /concepts/2 (offline: CON_0001) | Operator that increases an integer variable's value by 1, usable as prefix or postfix. | we also have increment and decrement operators let me show you so I'm gonna declare a new variable int X we set it to 1 now if you want to increase the value of x by 1 we use the increment operator | Increasing x by 1 and prefix/postfix applicability are both stated. Integer x is the demonstrated variable. | The citation omits prefix/postfix; the generic operator definition obscures that integer x is the example, not a stated type restriction. | field association; model completion | Keep the demonstration scoped to x, with initial 1 and printed 2; cite the later prefix/postfix sentence separately, without inventing its unfinished outcome. |
| Not assigned; /concepts/3 (offline: CON_0001) | Values that operators act upon in an expression. | these numbers that we have here are called operands | The displayed numbers are explicitly called operands. The generalized definition is a reasonable paraphrase but is broader than that wording. | Values that operators act upon adds a definition instead of preserving the local naming. | model completion | Use: The numbers in this example are called operands. No new formal definition needed. |
| Not assigned; /explanations/0 (offline: EXP_0001) | Casting operands to double (e.g., (double) ...) makes the division produce a floating‑point result. | if you want to get a floating-point number here you need to convert these numbers to a float or a double let me show you so we prefix this number with parentheses and in parentheses we type double now we are casting or converting this number to a double | The spoken conversion to double and floating-point objective are supported. | Literal (double) ... is reconstructed, and float-or-double alternatives and local scope are lost. | model completion; prompt representation instructions insufficiently explicit | Keep conversion in prose, preserving float or double and the particular demonstration; do not synthesize Java syntax. |
| Not assigned; /facts/1 (offline: FCT_0001) | In Java, dividing two integers produces an integer result (truncates fractional part). | the result is a whole number because in Java the division of two whole numbers is a whole number | The general whole-number division result is explicitly stated by the lecturer; it need not be narrowed merely because examples surround it. | Only the parenthetical truncates fractional part is unstated. | model completion | Delete the parenthetical. Retain the explicitly stated whole-number result rule. |
| Not assigned; /facts/2 (offline: FCT_0001) | The increment operator may be applied before (prefix) or after (postfix) the variable. | we can apply this operator as a postfix or as a prefix | Prefix/postfix applicability is explicitly stated. Before/after is conventional terminology, but is not defined in this supplied passage. | Under the source-only contract, omit the before/after expansion and do not complete the trailing and we get sentence. | model completion; source ambiguity at truncated ending | Use: The increment operator can be applied as a postfix or prefix. Preserve the unfinished result as unknown. |
| Not assigned; /facts/3 (offline: FCT_0001) | The modulus operator (%) returns the remainder of a division. | modulus which is the remainder of a division | The remainder description is directly supported. | Only the % symbol is absent; the rest of the item can be preserved. | model completion; field association | Remove (%); keep the source remainder description. |
| Not assigned; /facts/4 (offline: FCT_0001) | A final variable cannot be assigned a new value after initialization. | cannot assign a value to final variable pi | A compilation error on assignment to final variable pi is directly supported. | After initialization is not stated. The beginning its value later on lacks its prior context, so avoid inferring lifecycle rules. | model completion; source ambiguity at excerpt boundary | Use: In the example, assigning to final variable pi causes the reported compilation error. Preserve the actual diagnostic quote. |
| Not assigned; /procedures/0 (offline: None) | Cast one operand to double, then divide, and store the result in a double variable to obtain a floating‑point result. | if you want to get a floating-point number here you need to convert these numbers to a float or a double let me show you so we prefix this number with parentheses and in parentheses we type double now we are casting or converting this number to a double | Floating-point conversion, division context and declaration repair are supported in different passages. | One operand and (double) numerator are additions. The quote omits the declaration repair; /steps is invalid and cannot cover indexed steps. Float alternative and local demonstration scope are lost. | model completion; field association; prompt array-path contract insufficiently explicit | Prefer one scoped explanation joining alternatives, demonstration and error/repair. If steps are retained, use only spoken instructions, exact supporting excerpts per step, and /steps/0 etc. |
| Not assigned; /relationships/0 (offline: REL_0001) | A constant is a final variable. | pi is a final variable or a constant | The source calls pi a final variable or constant. A connection between the terms is supported. | A universal constant-is-final-variable taxonomy is broader than this instance-level statement; it is not necessarily wrong in full, but is unnecessary here. | model completion; field association | Fold the scoped statement about pi into the constant item instead of creating a universal relationship. |



The JSON companion retains every additional populated field, including all three procedure steps. These are source-only judgments, not claims that the Java statements are generally false.

## Complete teaching-fact coverage inventory

| Source fact | Exact source excerpt | Existing coverage / correction |
|---|---|---|
| Compiler rejects assignment to final variable pi | cannot assign a value to final variable pi | Present but expanded by an unstated initialization qualification in facts/4; retain the local diagnostic. |
| pi is described as a final variable/constant | pi is a final variable or a constant | Present; avoid unnecessary universal relationship duplication. |
| Uppercase convention, specifically pi to PI | by convention we use all capital letters to name constants so this should be PI | Convention present; specific correction missing. Integrate into the constant explanation once. |
| Arithmetic operators and remainder meaning | we have addition subtraction multiplication division and modulus which is the remainder of a division | Present; remove unstated % symbol. |
| Spoken integer result example: 10 plus 3 prints 13 | declare an integer called result and here we can type 10 plus 3 now when we print result it's gonna be 13 | Present twice (example and fact). Prefer one spoken example retaining the stated result. |
| Whole-number division yields a whole number | in Java the division of two whole numbers is a whole number | Present; remove unstated truncation mechanism. |
| Float or double alternatives for this conversion | if you want to get a floating-point number here you need to convert these numbers to a float or a double | Missing from generated claim fields, although present in evidence. Preserve explicitly in a scoped explanation. |
| Spoken parentheses/double conversion, repeated similarly | we prefix this number with parentheses and in parentheses we type double now we are casting or converting this number to a double similarly we should do that here | Replaced by reconstructed syntax and one-operand recipe. Preserve prose only, without guessing unseen expressions. |
| Double expression conflicts with integer declaration | we have a compilation error because on the left side we declared an integer but here the result of this expression is a double | Missing causal explanation. Combine with declaration repair. |
| Repair declaration to double and observe floating-point result | so to fix this problem we need to change this to double now when we run this program we get this floating point number | Repair partly present in procedure; selected evidence omits it, error cause absent, successful result not stated explicitly. Keep as one error-and-repair explanation; do not invent the numeric result. |
| Expression definition | an expression is a piece of code that produces a value | Present and supported. |
| Numbers in demonstration are operands | these numbers that we have here are called operands | Present with an expanded textbook definition. Prefer the local label. |
| Increment demonstration: x begins 1 and prints 2 | we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2 | Increase-by-one present; concrete initial/final values missing. Preserve together in one demonstration item. |
| Prefix/postfix applicability; ending is unfinished | we can apply this operator as a postfix or as a prefix and we get | Applicability present. Preserve incompleteness; omit the unstated outcome and before/after definition. |



The personal pronunciation/C-sharp anecdote is noncore educational context and may be omitted. Decrement is mentioned, not explained. No missing behavior should be inferred.

Coverage strategy: check each explicitly stated teaching fact against existing items; integrate related numeric details, alternatives and cause/repair into the corresponding item once. Use another exact excerpt when the current citation lacks a detail. Add an item only for a distinct supported teaching fact. Empty categories remain normal.

No source facts have been newly recovered from the model in this offline stage. The historical response remains unchanged and failed. These are proposed reference corrections, not validated new extraction results.

## Implementation and tests

Modified only app/extraction/prompts.py and tests/test_extraction_grounding.py. Validator unchanged; parent collections cannot substitute for array element paths. Dictionary keys retain RFC 6901 escaping and require their own paths plus nested substantive descendants.

256 focused regressions passed; zero failed. New tests cover actual validation code, plus prompt-text contracts. Mocked and synthetic cases do not establish real-model quality.

Protected implementation and all failed-smoke artifacts match their pre-change SHA-256 hashes. build_validation_prompt remains unchanged.

## Token budget

{
  "before": {
    "system_characters": 2566,
    "user_characters": 4783,
    "budget": {
      "input_tokens": 2245,
      "max_output_tokens": 4000,
      "total_tokens": 6245,
      "tpm_limit": 6800,
      "is_safe": true,
      "reason": "Within budget"
    }
  },
  "after": {
    "system_characters": 4179,
    "user_characters": 4783,
    "budget": {
      "input_tokens": 2705,
      "max_output_tokens": 4000,
      "total_tokens": 6705,
      "tpm_limit": 6800,
      "is_safe": true,
      "reason": "Within budget"
    }
  },
  "complete_source_preserved": true,
  "category_contracts": [
    "concepts",
    "definitions",
    "explanations",
    "examples",
    "facts",
    "formulas",
    "procedures",
    "relationships"
  ],
  "live_requests": 0,
  "release": "NO-GO"
}

The existing budget policy is unchanged; no output allowance was manually increased. No source or instructions were truncated.

## Limits

Mechanical exact-quote matching, chunk membership and field coverage do not establish entailment. The saved procedure passes mechanical checks after a path-only repair despite retaining unsupported syntax; a regression explicitly demonstrates this. No claim of quality recovery or release readiness is made.