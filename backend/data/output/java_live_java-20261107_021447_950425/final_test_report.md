# Live Java test — November 7, 2026

## Result
Incomplete: 0 of 32 initial chunks accepted. One real request reached Groq through NOTES 1 using openai/gpt-oss-120b and strict JSON schema. HTTP 200, finish reason stop; 3,235 input tokens and 2,006 output tokens (5,241 total). No HTTP 400 or 429. The response passed JSON/schema validation but failed the evidence/exclusion consistency check. No complete notes were produced. No additional requests or duplicate retry were issued after this failure.

## Confirmed failure
The response both cited and excluded Q0006, Q0011, Q0012, Q0013 and Q0014. The resolver correctly rejected this with `Unknown, duplicate or contradictory exclusion`. Q0006 contains both sponsor text and the transition to JDK installation; the other four contain teaching about functions, return values, parameters and function bodies. Treating those whole excerpts as noneducational is incorrect.

## Manual review of rejected output
- The JDK definition and compiler/runtime fact cite only Q0006. That excerpt ends at “jdk is short for Java”; it does not support the full development-kit description or compiler/runtime list. The answer needs additional source references.
- The IDE definition cites Q0010, which lists editor choices and IntelliJ installation. That excerpt does not state the supplied expansion “Integrated Development Environment” or the whole write/compile/run description.
- The function-structure explanation says “parentheses for parameters (which may be omitted)”, which is ambiguous. The cited transcript defers teaching parameters; it does not clearly support this optionality claim.
- JDK installation and IntelliJ installation appear in both explanations and procedures; the facts also repeat definitions. Consolidation is still needed for useful notes.
- Some content fields differ materially from their main definition/explanation fields despite the prompt's repeat-main-text instruction.

These are source-grounding and quality problems, not credential, JSON syntax, or quota failures. Matching an excerpt ID proves provenance location, not semantic support.

## Next correction required
Teach the extraction policy to exclude only wholly noneducational excerpts and to use all references needed for the complete field. Keep the contradiction and evidence validators. Add semantic review before treating notes as ready. Any changed policy needs a fresh hash-bound manifest; this failed request and its token usage must remain in history. Full-document educational completeness cannot be assessed from this rejected first chunk.

## Authorization
The user directly approved sending the project's java.txt to Groq. The live tool execution was permitted. The earlier egress-approval blocker is resolved. Existing non-expiring credential approval and 85% quota controls were retained.
