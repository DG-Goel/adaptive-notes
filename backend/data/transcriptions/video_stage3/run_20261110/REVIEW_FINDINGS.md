# Actual visual recovery review — 2026-11-10

All 40 HIGH events were sampled and sent through official local
`glm-ocr:q8_0`; no MEDIUM or LOW event was processed. 39 events have successful
responses for every selected frame/task. One event has an unresolved formula
task. Successful response means nonempty, nontruncated OCR, not verified text.

## Execution

- 245 candidate sample positions examined: 232 selected images, 7 additional
  unique images preserved but not OCRed under the per-event resource cap,
  5 exact-pixel duplicate positions and 1 position with no frame inside interval.
- 232 distinct images requested; 459 sequential inference attempts, 457
  successful responses and 2 failed attempts for the same image/task.
- Total request wall time: 408.9524542 seconds (6 min 48.95 s), excluding frame
  extraction and download. Mean request: 0.890964 seconds; aggregate request
  time per unique image: 1.762726 seconds (includes multiple recognition tasks).
- Sampled whole-GPU peak after requests: 2756 MiB / 4096 MiB. This includes
  other processes and is not a continuous/exact allocation peak.
- All observed Ollama `/api/ps` placements show loaded size equal to size_vram
  (1437681581 bytes); full GPU placement indicated, no CPU offloading indicated.
  CPU video decoding/image preparation still occurs.
- Ollama 0.40.11; official model digest
  `6e5935a916fc8d6878a67c60c2b99648f54e10b4a4af4cbbfb2c308953000e5f`,
  quantization Q8_0. No other model was loaded.
- Model installed only after explicit user download authorization.
- Three Stage 3 tests and all 14 Stage 1/2 regression tests passed. A broad
  discovery pattern also matched an unrelated pytest suite unavailable in this
  isolated environment; that import failed, and focused suites were run instead.

## Unresolved request

Event `9ab9874fed29b258`, original interval 02:26:15.050–02:26:23.630,
frame 8775.0663 s, task `Formula Recognition:`. Initial HTTP 500 was retried
once to obtain detailed error: `prediction aborted, token repeat limit reached`.
No more attempts were made for that image/task. Other images/tasks continued
without replaying successful requests. Both failed attempts remain in JSON.
The text-recognition response for this frame is retained. There was no reported
GPU-memory or model-loading failure. No failed content was fabricated.

## Mortgage demonstration

Event `365ba0502d15f7ff`, 01:35:45.260–01:36:02.720. Eight source frames
and separately traceable text/formula requests are preserved. The screenshots
show the mortgage Java implementation, including numerator/denominator portions,
but the editor is horizontally clipped and scrolls. The inspected frame at
5754.014933 s clips the right-hand expression; at 5757.284867 s the left-hand
identifiers are clipped and the right edge still truncates long lines.

**A complete readable mortgage equation is not established in a single inspected
frame.** Some raw OCR outputs omit characters, mislabel Java as Python, or
produce plausible completions of clipped content. These are not validated
source text. No equation was reconstructed from mathematics or stitched from
partial OCR. Inspect the preserved images, not just syntactically plausible OCR.

Example evidence:
[frame 5754.014933](365ba0502d15f7ff/5754.014933.png),
[frame 5757.284867](365ba0502d15f7ff/5757.284867.png).

## Java escape sequences / Windows paths

Stage 1 mentions backslashes/Windows paths around 3101–3194 s. No HIGH event
overlaps the escape/path demonstration range 3040–3200 s. It was **excluded by
the priority filter**, and no screenshots or OCR were taken there. No literal
Java path string is claimed to have been recovered.

## FizzBuzz and corrections

Five HIGH events are within the FizzBuzz section (approximately 7197–7494 s).
Frames preserve setup and later conditional-code states separately. At
7299.392100 s (`1fc0eb235209619a`), the inspected image shows input setup and
an empty body region below it. At 7449.508733 s (`0bc018dc14dc3e7c`), the image
shows the combined divisibility condition first, then the individual branches.
At 7474.333533 s (`9b5e455f76a4b215`) the combined condition is highlighted.

These are observed states, not an invented merged program. The earlier incorrect
branch-ordering state has not been established by inspection of these HIGH
frames; the main narrated correction near 7386–7442 s is not covered by the
listed HIGH windows. No extra priority levels were processed to fill that gap.
Per-frame OCR remains raw, including its punctuation and recognition mistakes.

## Audit and limitations

`evidence_audit.json` verifies every selected original and inference-image hash,
and confirms unchanged transcript/detection fingerprints. It contains 136
consecutive OCR text differences. These differences may reflect actual edits,
selection/highlight changes or OCR instability, and are not automatically
classified as instructor corrections. Raw candidates stay individually linked
to screenshots, exact decoded PTS, original event metadata and spoken transcript.

The 854×480 source limits small-character recognition. Sampling can miss brief
intermediate states. No automatically reconstructed code, notes, canonical
replacement, Groq calls, retranscription or semantic evaluation was performed.
Any prose descriptions emitted by the OCR model must be treated as
MODEL_INTERPRETATION, not literal visual transcription. Other text is unverified
OCR, not automatically approved knowledge. Full visual verification of every
character and every returned formula remains outstanding.

Recommended next action is human evidence review of mortgage crops, the failed
formula task, and FizzBuzz state coverage before any canonical integration.
