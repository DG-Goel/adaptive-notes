# Stage 3.1 targeted recovery findings

## Mortgage: VISUAL_CONTEXT_REQUIRED

Bounded search: 5725–5780 seconds (01:35:25–01:36:20), including frames before
and after Stage 2 event `365ba0502d15f7ff` (5745.260–5762.720). Thirteen
timestamped original frames were extracted. Each received text and formula
recognition on a focused crop [80,200,854,440]. Original 854×480 frames remain
available. Crop coordinates are [left,top,right,bottom], right/bottom exclusive.

Review of the original-frame contact sheet confirms horizontal clipping in the
source video. Before the editor scrolls, the right ends of long expressions
are outside the video. After scrolling, left identifiers are outside it and
some long right-hand text remains clipped. Cropping does not recover pixels
that never appear in that frame. No sampled nearby frame establishes a complete,
simultaneously readable expression. This is a bounded sampling finding, not a
claim that every video frame was examined.

Focused recognition did not establish the complete formula. Formula prompts
sometimes turn Java into distorted LaTeX, change identifiers, or repeat text.
Two formula responses at 5750.010933 and 5752.513433 reached the 512-token
bound and are explicitly unresolved. Text-recognition responses are retained
alongside their competing formula readings in `ocr_records.json` and
`audit.json`. Nonempty output is not evidence of correctness. No mathematical
reconstruction, snippet stitching or completion was performed.

[Original-frame contact sheet](mortgage_contact.png).

## Windows path: focused OCR candidates recovered

Bounded search: 3110–3152 seconds (00:51:50–00:52:32). Complete Stage 1 text
search located the Windows-directory/backslash explanation at 3101.51–3150.15 s.
The core literal-code explanation was **missed by Stage 2**, rather than given
a LOW/HIGH code event. Nearby execution references were MEDIUM:

- `dbf69ea896f937ee`, 3084.23–3096.63, SCREEN_OUTPUT_DEPENDENCY (outside
  this targeted extraction window).
- `3abe89da8c0e3837`, 3139.93–3147.39, SCREEN_OUTPUT_DEPENDENCY (overlaps
  the targeted window and links its extracted frames to existing detections).

No blanket expansion to MEDIUM/LOW events occurred. Thirteen original frames
show the actual chronological editing states, including incomplete strings.
Broad crops frequently lose a backslash or misread the caret/ellipsis. These
outputs remain untouched in the evidence records.

Two additional single-line crops [195,88,745,130], at 3146.009533 and
3150.013533 seconds, independently returned this literal OCR candidate:

```java
String message = "c:\\Windows\\...";
```

Each visible separator in this candidate has **two backslash characters**.
The original frame at 3146.009533 visibly supports doubled backslashes in the
string literal, while its console shows single backslashes. This is an image
comparison observation, not a declaration that the whole OCR output is verified.
The raw broad-crop candidate at that timestamp instead contained single
backslashes; both readings are preserved. No valid-Java correction was applied.
Capitalization, quotation marks, delimiters and ellipsis remain as returned.

[Original 3146.009533](windows_path/3146.009533.png) ·
[Focused crop](windows_path_literal/crop_3146.009533_Text.png).

## Prior failed request: bounded changed-task retry succeeded

Original event `9ab9874fed29b258`, frame 8775.0663 s (02:26:15.066), task
`Formula Recognition:`. Historical Stage 3 recorded one HTTP 500 and one
detailed `prediction aborted, token repeat limit reached` failure. Both records
are copied into the new manifest as prior history; neither had a returned OCR
body to inspect. Existing successful text output remains in historical Stage 3.

The original image shows Java validation code, not a displayed standalone math
equation. One changed request used crop [90,90,840,400], `Text Recognition:`,
temperature 0, 512 output tokens and the same glm-ocr:q8_0 model. It succeeded
without repetition or truncation. Raw output includes the `while (true)` block,
annual-interest input and condition, `break;`, and period input. The long
monthly-interest line remains clipped and ends with `/ M` in the OCR candidate.
This is successful recovery of visible code candidates, **not completion of
missing characters or a successful rerun of the old formula prompt**.

[Original](failed_task/original_8775.066300.png) ·
[Changed crop](failed_task/crop_8775.066300_Text.png).

## Execution and safeguards

- Official existing local `glm-ocr:q8_0`; no model download or substitution.
- 42 sequential requests: 40 nonempty/nontruncated responses, 2 unresolved
  truncated formula responses, zero request errors in Stage 3.1.
- Total request wall time: 42.659614 seconds, excluding extraction/review.
- 26 newly sampled source frames plus a copy of the historical failed frame.
- Exact decoded frame PTS, original/crop hashes, dimensions, crop coordinates,
  task, options, model digest, raw response and uncertainty preserved per record.
- New-frame Stage 2 associations describe events overlapping the targeted
  search window; they do not imply each frame had a direct detector trigger.
- `audit.json`: no historical-source or image-hash mismatches.
- Three targeted evidence tests passed: bounded timestamps, hash/provenance
  integrity and unchanged source artifacts, and exactly one changed-task retry.

Deliverables: `visual_supplement.md`, `ocr_records.json`, `manifest.json`,
`audit.json`, original PNGs, focused crops and contact sheets in this directory.
The supplement includes spoken context and every raw response; differences are
not silently normalized. No results were merged into the transcript or canonical
source. No Groq, retranscription, additional model, notes or Task 11/12A changes.

New code: `backend/targeted_visual_cleanup.py` and
`backend/tests/test_targeted_visual_cleanup.py`. All other new files are in this
Stage 3.1 directory. Existing pipeline code and Stage 1/2/3 artifacts unchanged.

To reproduce the evidence audit and supplement without inference, from backend:
`python targeted_visual_cleanup.py finalize`. Run tests with
`python -m unittest discover -s tests -p test_targeted_visual_cleanup.py -v`.
