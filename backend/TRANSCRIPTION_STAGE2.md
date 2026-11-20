# Stage 2: transcript risk intervals

Run from `C:\Projects\adaptive-notes\backend` (Python standard library only):

```powershell
& .venv-transcription/Scripts/python.exe detect_transcription_risks.py --input data/transcriptions/video_stage1/run_20261109_retry/artifacts/transcript.json --output data/transcriptions/video_stage2/my_new_run
& .venv-transcription/Scripts/python.exe -m unittest discover -s tests -p 'test_transcription*.py' -v
```

Outputs: `risk_intervals.json` (raw detections, merged events, configuration,
statistics and source metadata), `risk_intervals.csv`, chronological
`risk_intervals.md`, `high_priority.md`, and `statistics.json`.
Use a new output directory. No video access, network, GPU, ASR, or other models
are involved. Historical transcript files are read only.

`transcription_risk.py` exposes `detect(data, fingerprint, RiskConfig(...))` and
`run(input_path, output_directory, config)`. CLI `--config settings.json` accepts
any RiskConfig fields. Defaults: context 8 seconds, at most 3 segments each way,
padding 2 seconds before/3 after, merge gap 2 seconds, merged span cap 45 seconds,
low word probability below .3, low segment logprob below -1, HIGH >=7 and MEDIUM
>=4. All other events are LOW. Context only assists classification; it does not
automatically include all neighboring segments in the inspection interval.

## Detection and provenance

Precompiled category rules find literal trigger spans, nearby subject context
resolves vague references, and joined adjacent segments detect split phrases.
Standalone vague phrases without subject context are suppressed. Technical
terms/acronyms alone are not ASR errors: TECHNICAL_ASR_RISK requires actual
low-probability words, zero-duration word alignments, or low segment logprob
alongside technical content. Diagnostics are segment-level co-occurrence, not
proof that the particular technical word is wrong. Missing diagnostics remain
missing. Pattern matches and contextual quotations are copied from the source.

Every raw detection preserves exact source segment times, IDs, indices, text,
trigger character offsets and real ASR evidence. Adjacent-segment trigger
offsets refer to the two source texts joined by one space. Intervals are padded
segment spans, not fabricated word alignments or precise visual appearance
times. Padding is clipped to the original `audio_duration`; an absent duration
or invalid/nonchronological timeline is rejected rather than guessed.

Score = 2 base + 2 for local visual/deictic language + up to 2 for additional
categories + 2 formula + 2 correction + 1 technical ASR concern. This is a
heuristic priority, not a calibrated probability. Context can increase both
category coverage and false positives. Formula context includes mathematical
expressions within programming demonstrations. Correction rules avoid treating
the `replace` method name alone as an instructor revision.

Merging uses a sorted pass and shared directly triggered categories, temporal
proximity and a span cap. An ambiguous/context-only inferred category cannot
by itself join unrelated events. The group's original direct category anchors
the merge to limit chaining. Long original source segments are not truncated
to enforce the merge cap. Closely adjacent correction events sharing a domain
are linked bidirectionally; these links suggest relationships, not established
version history. Raw detections remain available regardless of merging.

SHA256 covers the exact source JSON bytes. Event IDs hash that fingerprint,
the full configuration, and deterministic raw detection membership. Runtime
statistics vary per invocation; IDs/events do not. Rule changes must bump
VERSION before reusing a release. Context scan is bounded by segment count;
sorting/merging is O(n log n), with no pairwise word scan. Events may overlap
when they represent different risks; coverage uses the interval union.

## Actual run and review

Final deliverables: `data/transcriptions/video_stage2/final_20261109/`.
Earlier `run_20261109` and `run_20261109_reviewed` are development review outputs.

- Duration: 9047.7714375 seconds; transcript segments: 2181.
- Detection time: 0.242216 seconds (excludes file read/serialization).
- 337 raw detections became 277 events (60 detections consolidated).
- HIGH 40, MEDIUM 191, LOW 46; approximately 110.215 events/hour.
- Unique coverage: 2701.37 seconds, 29.8567% of the lecture.
- Category event counts: code 156, formula 43, screen output 75, diagram 2,
  table/chart 1, slide text 2, correction 17, ambiguous reference 75,
  technical ASR concern 31. Categories overlap.
- Exact input SHA256:
  `647c17e24c18ae0b530baf100c0fc9983a861557c6c966455b7b6a9c82ec15cf`.
- 14 tests passed: 9 Stage 2 tests and 5 unchanged Stage 1 tests. Fixtures cover
  all categories, ordinary speech, acronyms without error claims, absent
  probabilities, context bounds, split phrases, rankings, merge cap, unrelated
  domains, revision links, timestamps, deterministic IDs and serialization.

Sampled real reports include Java code changes, arithmetic expressions and
output demonstrations. A preliminary false alarm on “replace method” was
removed from correction detection. Roughly 30% coverage is plausible for a
code-heavy screen tutorial, but is still broad and not measured precision.
The 40-event high shortlist should be reviewed first. The complete chronological
report retains medium/low events for recall. No labeled reference set exists;
neither precision nor recall has been measured.

## Limits and later recovery recommendation

English lexical rules can miss synonyms, visual-only content without spoken
cues, distant dependencies and domain terminology absent from the patterns.
They can flag ordinary rhetorical language or classify code expressions as
mathematics. No transcript-only system can establish what is on screen.
Timing is segment-level and inherits Stage 1 alignment limitations. This
detector does not identify wholly absent speech or independently classify
silent gaps; the Stage 1 flagged gap still needs separate review. ASR
probabilities are not calibrated correctness scores.

For a later authorized visual stage, inspect high-priority formula and code
intervals first, then screen-output events; use the recorded recovery types and
source fingerprint. Review the original and corrected versions together when
linked. Validate a small independently labeled sample and adjust thresholds
before broad visual processing. No OCR, screenshots or educational notes were
created here.

Files added: `transcription_risk.py`, `detect_transcription_risks.py`,
`tests/test_transcription_risk.py`, this guide and Stage 2 report artifacts.
No Stage 1 transcript, Task 11/12A, authorization, quota or credential files
were modified. No dependencies were added.
