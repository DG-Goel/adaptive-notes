# Stage 1 local transcription

Independent Faster-Whisper ASR only. No OCR, frame extraction, note generation,
canonical integration, Groq calls, or changes to the main backend dependencies.

## Windows setup and use

Run in `C:\Projects\adaptive-notes\backend` with PowerShell:

```powershell
# Already created on this machine; these commands reproduce the isolated setup.
& .venv/Scripts/python.exe -m venv .venv-transcription
& .venv-transcription/Scripts/python.exe -m pip install -r requirements-transcription-lock.txt
& .venv-transcription/Scripts/python.exe transcribe_video.py --input 'C:\Videos\lecture.mp4' --output 'data\transcriptions\lecture'
# Force the safe CPU route:
& .venv-transcription/Scripts/python.exe transcribe_video.py --input 'C:\Videos\lecture.mp4' --output 'data\transcriptions\lecture-cpu' --device cpu
```

Default model loading is local-only. No weights were downloaded during this task.
If the weights are absent, the command fails rather than downloading. After
explicitly authorizing a model download, add `--allow-model-download` to the
command. Alternatively pass `--model 'C:\Models\faster-whisper-small.en'` for
an existing converted model directory. Use a new/empty output directory each run.

MP4, MKV, MP3, WAV and other formats accepted by installed PyAV use its bundled
decoder; system FFmpeg is unnecessary. Original media is never modified.
Defaults: small.en, CUDA int8_float16, English transcription, beam 3, word
timestamps, VAD (2000 ms minimum silence, 400 ms speech padding), previous-text
conditioning off, temperature 0, no batching, one worker, four CPU threads.
CLI help lists configurable performance/VAD options.

GPU needs CUDA 12 cuBLAS and cuDNN 9 DLLs plus their dependencies on PATH.
The implementation registers discovered DLL directories for Windows Python and
checks key DLLs before loading the model. CUDA capability or initialization
failure logs its reason and loads CPU int8. Failures after initialization save
partial artifacts and exit nonzero without rerunning the recording. Some native
runtime failures can terminate a process; complete inference remains necessary
to establish hardware compatibility. Do not copy Torch DLLs into this environment
or downgrade main-environment packages. Faster-Whisper does not require Torch.

JSON preserves returned wording, float timings, word probability or null,
input absolute path/name/size/mtime, actual device/compute, package versions,
configuration, processing duration, audio duration, RTF and alignment coverage.
SRT and TXT display millisecond timings; JSON retains original precision.
Faster-Whisper restores VAD timestamps onto the original media timeline.
Word timings are approximate. Missing alignments stay null. A failed run's files
contain partial results: consult JSON status and the CLI exit code before use.
One model is loaded at a time; PyAV holds decoded audio in RAM, so this is not
a constant-memory streaming route for arbitrarily long recordings.

## Validation on 2026-11-09 (Asia/Calcutta)

- System Python 3.9.11; backend and isolated environment Python 3.12.10, 64-bit.
- Main environment inspected read-only: Torch 2.14.0, Transformers 5.17.0,
  Docling 2.127.0, RapidOCR 3.9.2; no Faster-Whisper/CTranslate2 installed there.
  Isolation avoids overlapping NumPy/tokenizers/Hugging Face/ONNX dependencies.
- Installed isolated Faster-Whisper 1.2.1, CTranslate2 4.8.5, PyAV 19.0.2,
  ONNX Runtime 1.31.1. Exact dependencies are in the lock file. `pip check` passed.
- NVIDIA RTX 3050 laptop, 4096 MiB, driver 596.08. `nvidia-smi` advertised driver
  CUDA capability 13.2; this is not the installed toolkit version.
- Installed toolkit directory v12.1. cuDNN DLL version 9.0.0.312. cuBLAS,
  cuDNN and cuDNN ops DLLs loaded using full paths and registered DLL directory.
- CTranslate2 reports one CUDA device and supports int8_float16. This is a
  capability probe, not evidence of completed GPU inference.
- Idle/pre-test GPU snapshot: 458 MiB / 4096 MiB. No inference peak measured.
- No sample MP4/MKV/MP3/WAV found in project; standard Hugging Face cache had
  Docling and sentence-transformer models, no Whisper model. No existing audio
  transcription implementation found under `app`.
- Five offline mock tests passed: original fractional timeline and three output
  formats, logged CPU fallback, partial failure/no replay, no-speech output,
  formatting/validation. These synthetic objects are not real ASR evidence.
- Real inference: **NOT_RUN**. Video duration, processing duration, RTF, actual
  inference device, segment count, real timestamp coverage and manual speech
  checks: **NOT_RUN**. No accuracy percentage claimed.

```powershell
& .venv-transcription/Scripts/python.exe -m unittest discover -s tests -p test_transcription_stage1.py -v
& .venv-transcription/Scripts/python.exe -m pip check
```

For the future 3–5 minute real test, provide local media and authorize/cache
small.en weights. Capture `nvidia-smi` during the run for memory observations;
JSON records duration, RTF, device, compute and timestamp coverage. Manually
listen to representative speech and silence intervals and compare their timings.

## Files delivered

`transcription.py`, `transcribe_video.py`, `requirements-transcription.txt`,
`requirements-transcription-lock.txt`, `tests/test_transcription_stage1.py`,
`TRANSCRIPTION_STAGE1.md`; `.gitignore` updated for the optional environment and
temporary directory. Local `.venv-transcription/` created (ignored).

Official API/GPU requirements and PyAV/VAD behavior:
https://github.com/SYSTRAN/faster-whisper#requirements
https://github.com/SYSTRAN/faster-whisper#usage
Installed source also checked for `local_files_only` and
`restore_speech_timestamps` behavior. No main environment packages changed.

## Real video follow-up

The supplied `video.mp4` was subsequently transcribed successfully on CUDA.
See `data/transcriptions/video_stage1/run_20261109_retry/TEST_REPORT.md` for
actual speed, outputs and quality caveats. The first real decode exposed a
PyAV 19 incompatibility; the isolated environment and dependency files now pin
PyAV 16.1.0. The earlier NOT_RUN section describes the initial implementation
validation, not the subsequent real-video test.
