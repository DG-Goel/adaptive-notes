# Real Stage 1 video test — 2026-11-09

## Result and outputs

Full recording completed successfully, CLI exit 0, on NVIDIA RTX 3050 Laptop
GPU using CUDA `int8_float16`, `small.en`, English, beam 3, VAD and word
timestamps enabled. No CPU fallback occurred. Existing transcription module and
CLI were used unchanged. Original ASR text and timing outputs were not edited.

- [JSON](artifacts/transcript.json)
- [SRT](artifacts/transcript.srt)
- [TXT](artifacts/transcript.txt)
- [CLI log](cli.log)
- [Runtime and GPU samples](runtime_observations.json)
- [Structural and acoustic checks](quality_checks.json)

## Runtime

| Measurement | Result |
|---|---:|
| Input size | 195,583,400 bytes |
| Container duration | 9047.771429 s (02:30:47.771) |
| Decoded audio duration | 9047.7714375 s |
| Processing duration reported by CLI | 295.6742734 s (4 min 55.67 s) |
| CLI wall time including interpreter startup | 297.2792005 s |
| Real-time factor | 0.03267924 |
| Speed relative to media duration | approximately 30.6x |
| Actual device / compute | CUDA / int8_float16 |
| Sampled whole-GPU memory peak | 1060 MiB of 4096 MiB |
| Pre-run whole-GPU memory snapshot | 486 MiB |
| Speech segments | 2181 |
| Returned word objects | 25021 |
| Words with non-null start/end | 25021 (100%) |
| Words with positive-duration alignment | 24903 (99.5284%) |
| Zero-duration word alignments | 118 |
| VAD audio removed | 306.2514375 s |
| Successful-run warnings/errors | none in CLI log or transcript JSON |

GPU memory was sampled approximately once per second using `nvidia-smi`.
1060 MiB is the maximum observed total device usage, including other processes;
it is not an exact process allocation peak. Completed CUDA inference, the CLI's
device metadata and active GPU utilization support the GPU execution result.

The input has H.264 video and AAC audio at 44100 Hz in an MP4-compatible
container. Both streams start at zero. No video frames were decoded or extracted.

## Setup issue discovered and resolved

First attempt initialized CUDA but failed before any segments with:

`open() got an unexpected keyword argument 'metadata_errors'`

Installed PyAV 19.0.2 was incompatible with Faster-Whisper 1.2.1's decoder call.
Only the isolated transcription environment was changed to PyAV 16.1.0.
`requirements-transcription.txt` and `requirements-transcription-lock.txt` now
record that version. Decoder API check, `pip check`, and all five offline
software tests passed. Failed artifacts/logs remain in sibling
`run_20261109/artifacts` and `run_20261109/cli.log`; they are not the deliverable
transcript. The full retry used a fresh directory. No GPU failure occurred.

Only the explicitly authorized official model was downloaded, via the installed
Faster-Whisper mapping `small.en` -> `Systran/faster-whisper-small.en`.
Snapshot: `d1d751a5f8271d482d14ca55d9e2deeebbae577f`.
Weights are in `backend/data/transcriptions/model-cache`. Initial download/cache
preparation took 60.915 s; this is excluded from inference timing. The successful
retry checked the cache in 0.811 s before launching the CLI offline. Download
warnings concerned unauthenticated public-Hub requests and unavailable Windows
symlinks; no credentials or system settings were changed.

## Transcript quality and timing assessment

Text inspection sampled the opening, quarter, midpoint, three-quarter and final
passages, plus technical-term searches. The material is a Java course; examples
include JDK, JVM, bytecode, NetBeans, Eclipse, IntelliJ, classes and methods.
These passages are readable and contextually coherent. Code identifiers may be
rendered as ordinary words and Java capitalization is inconsistent. Original
recognized wording remains untouched.

There are no adjacent identical normalized segments, no segment overlaps and no
negative, reversed or out-of-audio word intervals. This does not rule out other
repetitions or missing speech. 254 words have model probability below 0.3;
probability is not a calibrated correctness score.

Acoustic energy exists at representative segment intervals across the original
recording, and the final spoken segment ends at 9040.20 s within the 9047.77 s
recording. VAD restoration preserves original timeline offsets. Checks of bounds
and acoustic energy do not establish precise word alignment or absence of drift.
No manual listening/reference transcript comparison was completed, so lexical
accuracy and timestamp error in milliseconds remain unmeasured.

Two long transcript gaps require listening review:

- 5872.42–5904.10 s (01:37:52.420–01:38:24.100), 31.68 s. RMS 0.03749;
  only about 18.94% of 20 ms frames have RMS below 0.003. The transcript resumes
  with “quality, but it has way more content”, a mid-sentence fragment. This is
  a possible omission, not a confirmed silent interval.
- 8956.68–8967.75 s (02:29:16.680–02:29:27.750), 11.07 s. RMS 0.01237;
  about 48.10% of frames are below that threshold. Energy alone cannot
  distinguish speech, music or other sound.

A focused diagnostic reran the same existing CLI/model/settings on a 38 s audio
excerpt at original offset 5870 s. It completed on CUDA in 4.62 s but returned
only “of our programs. So, I'll see you in the next section.” in one segment
spanning local 0–36.73 s. This broad alignment does not resolve the possible
omission and is itself a timing-quality concern. Diagnostic outputs remain in
`gap_diagnostic/`; they were not merged into the full transcript. No entire
recording was silently replayed. The diagnostic's processing/memory is excluded
from the full-run statistics.

Four original-timeline audio-only review excerpts are included: 0–15,
4490–4510, 5870–5908 and 9030–9045 seconds. WAV conversion uses the same PyAV
audio decoder; original video is unchanged. The 5870–5908 clip is particularly
useful for resolving the possible omission by listening. Word timings remain
approximate; 100% timestamp presence must not be interpreted as 100% accuracy.

Speed and successful GPU operation are established. Fine-grained timing and
speech completeness need listening review of the flagged intervals before using
these alignments as precise downstream interval boundaries. No OCR, downstream
integration, second ASR engine, Groq call, or Task 11/12A changes were made.

## Changes made in this test

- Isolated environment: PyAV 19.0.2 replaced by 16.1.0.
- `backend/requirements-transcription.txt`: compatibility pin added.
- `backend/requirements-transcription-lock.txt`: resolved lock updated.
- `backend/TRANSCRIPTION_STAGE1.md`: current-test pointer appended.
- New run artifacts, monitoring/inspection scripts, review WAVs, report and
  official small.en cache under `backend/data/transcriptions/`.
- `transcription.py` and `transcribe_video.py` unchanged.

The exact command, official snapshot path, sampling data and download timing
are preserved in `runtime_observations.json`.
