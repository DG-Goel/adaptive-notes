# Stage A read-only preflight

**HOLD. Release NO-GO.** Configuration and allocation inspected offline. Stage A was not invoked.

## Files inspected

- data\output\t0022_safety_infrastructure_20261104_003405/stage_a.py, control.py and stage_b.py
- data\output\groq_strict_t0022_20261103_8daaab0610db4f2f\source_units.json
- data\output/t0022_offline_prototype_20261103_225328/prototype.py
- data\output/groq_quota_runbook_20261104_004222/RUNBOOK.md
- app/extraction/token_budget.py and app/extraction/llm_provider.py

## Allocation and checks

The configured estimate uses ceil(UTF-8 bytes / 3.5) per message, 32 framing tokens per message, 16 assistant priming tokens and 64 JSON-mode overhead tokens. System bytes: 443. User bytes: 2574. Estimated input: **1007**. Maximum planned output: **4000**. Estimated allocation: **5007**. The 85% policy ceiling is 6800, giving 1793 tokens within policy and 2993 tokens below the nominal 8,000 TPM ceiling. This is request sizing. Admission requires actual remaining capacity.

| Check | Result |
|---|---|
| Groq and model pin | PASS for offline request metadata. Live binding unavailable. |
| Rotation, fallback, recovery | PASS offline. Only the exact scripted scenario type is accepted. No transport, retries or recovery path is wired to Stage A. The standalone Groq adapter can use SDK defaults and key pooling unless overridden. |
| Source provenance | PASS. Frozen source SHA-256 matches and the only unit is T0022. User message starts with the canonical marker. A validation checks source membership and exact contiguous excerpts. |
| Exact messages and full estimator overhead | PASS. Messages reproduced directly from the execute_a assignment below. No entry point invoked. |
| Output cap and safety margin | PASS for computed allocation. The cap is recorded in budget metadata. No SDK request exists that enforces it on the wire. |
| Minute and daily quota | HOLD. The admission loop checks one request and the full allocation against every supplied window. It requires a minute record but does not require a day record or pin the supplied limits. Live admission needs verified RPM 30, RPD 1,000, TPM 8,000 and TPD 200,000 headroom, plus any applicable stricter ceilings. |
| Durable ledger | PASS offline. SQLite unique (run, stage) claim and authorization event commit before dispatch. This controls processes sharing the ledger. Quota evidence is simulated and this ledger supplies no organization-wide capacity reservation. |
| A checkpoint and stop | PASS offline. Successful mechanical validation writes an exclusive checkpoint, flushes and fsyncs it, records its hash, and returns awaiting manual review with zero publishable items. B is a separate function. |
| Checkpoint integrity | PASS at the application boundary. Exclusive creation rejects overwrites. B checks the bytes against the original A event and persisted approval. Filesystem edits remain possible, and trusted access to the files and ledger is required. |
| Mock publication | PASS. Offline results have no production publication route. |

## Manual admission still required

Match the credential inventory alias and secret version to its organization and project. Verify fresh applicable limits and remaining minute/day request and token headroom, including in-flight commitments. With the confirmed ceilings, a single estimated allocation of 5007 and one request fit in isolation. There must actually be room for both across all windows immediately before dispatch. Require controlled or fully accounted competing traffic. The simulated gate's 15-second cutoff cannot turn old telemetry into fresh evidence. Include any lower project caps and applicable input/output ceilings. HOLD on any missing, stale or contradictory evidence. An authorized 429 consumes the attempt and stops it.

## Execution command

**Unavailable.** The current entry point is the offline Python callable execute_a(ledger, scenario, organization, authorization). It accepts only OfflineScenario and the module has no CLI dispatch. An exact live execution command cannot be supplied from the existing code. A separately reviewed live harness would need explicit single-credential selection, SDK retries set to zero, max_tokens set to the computed cap, and independent admission before claiming dispatch.

## Exact Stage A message configuration

The JSON escaping below preserves the original message strings.

```json
{
  "provider": "Groq",
  "model": "openai/gpt-oss-120b",
  "source_id": "T0022",
  "response_format": {
    "type": "json_object"
  },
  "max_tokens_planned": 4001,
  "budget": {
    "input_tokens": 1007,
    "max_output_tokens": 4000,
    "total_tokens": 5007,
    "tpm_limit": 6800,
    "is_safe": true,
    "reason": "Within budget"
  },
  "mode": "offline scripted only",
  "sdk_retries_declared": 0,
  "application_retries": 0,
  "key_pool": false,
  "fallback": false,
  "source_sha256": "4edcc092ab609aed3809184feeb3dd8485836199ccaad239bb4954d91dadf7aa",
  "messages": {
    "system": "Return a JSON facts array with fact_id, source_id, claim, quote, scope and optional relationships with relation and target_id. Cite only T0022 and contiguous exact text. Keep the final pi error distinct from the division type mismatch and declaration repair. Preserve explicit pi-to-PI naming, scoped float or double alternatives and increment 1 to 2 when supported. Omit inference, reconstructed code, decrement behavior and universal claims.",
    "user": "[T0022] its value later on you can see here we have a compilation error and it says cannot assign a value to final variable pi so pi is a final variable or a constant now by convention we use all capital letters to name constants so this should be PI beautiful now I tell you a little side story in one of my early courses that I created years ago that was c-sharp basics for beginners there I used the same example to teach the concept of constants but I pronounce this word as P instead of Pi and believe it or not to this day people make fun of me for saying P instead of Pi but that's how we learned this back in Iran we pronounce it as P and I think Greek people also say P but anyway I just thought to share this video to change the mood now you're done with constants next we're gonna talk about arithmetic expressions in this tutorial we're going to talk about arithmetic expressions in Java so in Java we have the same arithmetic operators that we have in math we have addition subtraction multiplication division and modulus which is the remainder of a division let's look at a few examples so I'm gonna declare an integer called result and here we can type 10 plus 3 now when we print result it's gonna be 13 pretty straightforward there you go so this is addition we also have subtraction multiplication division is an interesting one let's take a look so here the result is a whole number because in Java the division of two whole numbers is a whole number if you want to get a floating-point number here you need to convert these numbers to a float or a double let me show you so we prefix this number with parentheses and in parentheses we type double now we are casting or converting this number to a double similarly we should do that here and now we have a compilation error because on the left side we declared an integer but here the result of this expression is a double and by the way an expression is a piece of code that produces a value so what we have here is an expression because it produces a value so to fix this problem we need to change this to double now when we run this program we get this floating point number beautiful so these are the arithmetic operators and these numbers that we have here are called operands we also have increment and decrement operators let me show you so I'm gonna declare a new variable int X we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2 there you go we can apply this operator as a postfix or as a prefix and we get"
  }
}
```
