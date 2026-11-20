# Stage 3 local GLM-OCR recovery

Implementation: `visual_recovery.py`. Uses existing transcription environment's
PyAV and NumPy plus the standard library; no dependency installs. Only HIGH
merged events are processed. Transcript SHA256 must match Stage 2. Source
artifacts remain read only; output is independent evidence.

## Current actual status (2026-11-10)

Ollama client/server 0.40.11; service reachable at 127.0.0.1:11434 after CLI
startup. Installed models: gemma3:4b, granite4:micro, qwen2.5:3b. No models
loaded in `ollama ps`. **glm-ocr:q8_0 is missing.** No substitute was loaded.
NVIDIA RTX 3050 Laptop GPU, 4096 MiB, initial whole-GPU usage 425 MiB.
Actual GLM inference/GPU placement: NOT_RUN. Three software tests passed.

40 HIGH events verified. All 40 are unprocessed pending explicit download
permission. Execution status and five required report/manifest files are under
`data/transcriptions/video_stage3/run_20261110/`. Empty records are not OCR
results. Mortgage equation completeness, Java escape-sequence OCR and FizzBuzz
visual states have NOT been established. No source text was reconstructed.

Once explicitly authorized, download only the official model:

```powershell
ollama pull glm-ocr:q8_0
```

Then run/resume from the backend directory:

```powershell
& .venv-transcription/Scripts/python.exe visual_recovery.py --video video.mp4 --transcript data/transcriptions/video_stage1/run_20261109_retry/artifacts/transcript.json --risks data/transcriptions/video_stage2/final_20261109/risk_intervals.json --output data/transcriptions/video_stage3/run_20261110
```

Localhost needs sandbox network access in this environment. No external inference
endpoint exists in the implementation. Official supported task prompts:
https://ollama.com/library/glm-ocr

## Behavior and limits

Sequential single-image requests, temperature 0, 4096 context and 2048 output
tokens; timeout 180 seconds. CLI configures sampling period, frame count,
resolution, timeout and output bound. Text, formula and table recognition remain
separate tasks for mixed categories. No transcript is sent to the model.

Beginning/mid/end plus periodic 3-second samples use exact decoded frame PTS,
not requested seek time. Full original PNGs remain on disk; inference derivatives
have a configurable 1600-pixel long edge. Source/inference dimensions, hashes,
crop=null and timestamps are preserved. Exact identical pixel arrays are
deduplicated. Text-edge differences prioritize small changes; sharpness is
recorded, not used to silently throw away possible source text. Up to 12 unique
images/event are sent by default, prioritizing endpoints/midpoint and changed
frames; capped candidates remain on disk and in manifest. This conservative
method can retain redundant frames and miss changes between samples. It does
not identify text regions semantically or guarantee a final complete state.

Smoke order is first code event and mortgage event, then all remaining HIGH
events automatically. API failure stops safely and checkpoints. Empty/truncated
outputs are unresolved. Every response, including raw metadata, is saved after
the request. Successful inference hash/task pairs are reused across events.
Source/config identity mismatch blocks resume. Failed/unresolved requests can
be retried on resume; successful requests are skipped. Do not change configuration
in an existing run directory. GPU ps observations preserve Ollama size/size_vram
placement evidence and per-request nvidia-smi samples; these are sampled device
usage, not an exact process peak. Actual offloading needs interpretation of the
returned Ollama placement metadata; it is not assumed from GPU presence.

OCR remains unverified. Generated descriptions must be treated as
MODEL_INTERPRETATION. No description task is requested; outputs are deliberately
kept raw rather than silently classified as literal truth. No snippets are
combined, corrected, or promoted into canonical knowledge. The supplement keeps
overlapping original speech for comparison. Markdown image links reference
original local PNGs. All visual changes and OCR tasks remain frame-linked.

Tests: `python -m unittest discover -s tests -p test_visual_recovery.py -v`.
Tests cover deterministic schedule, mixed task routing, valid PNG encoding and
atomic checkpoint replacement; real model/API compatibility, OCR quality and
memory behavior remain untested until weights are available.

New files: `visual_recovery.py`, `tests/test_visual_recovery.py`, this guide and
Stage 3 status artifacts. No Stage 1/2, Task 11/12A, authorization, quota or
credential artifacts modified.

## Authorized actual run completed

After explicit model-download authorization, local processing inspected all 40
HIGH events. 39 events have all selected tasks successful; one formula request
remains unresolved due to the model's token repetition limit. See
`data/transcriptions/video_stage3/run_20261110/REVIEW_FINDINGS.md` for actual
runtime, GPU placement, source audit and historical-example limitations. The
earlier missing-model section records the initial pre-download state.
Added `audit_visual_recovery.py` for offline frame/source integrity and raw OCR
state-difference auditing. HTTP errors now retain Ollama's detailed response;
known repetition-limit failures are not endlessly retried on resume.
