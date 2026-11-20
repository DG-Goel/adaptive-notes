# Stage 4 integration report

```json
{
  "speech_segments": 900,
  "visual_records": 96,
  "exact_repeated_readings": 67,
  "high_events": 9,
  "high_events_with_candidates": 9,
  "visual_records_in_speech_gaps": 10,
  "unresolved_items": 38,
  "verified_visual_records": 0,
  "processing_seconds": 0.7432493000001159
}
```

No inference performed. Image hashes verified; historical artifact hashes checked before and after.

All raw readings retain source-artifact/index pointers, hashes, crop/task/model metadata and errors. No canonical content approved.

Same-frame conflicting path strings and other divergent readings remain unresolved. Different-time OCR changes are chronological candidates, not automatic corrections.

Future Source Unit integration must retain modality, verification status, provenance and unresolved flags; it must not treat candidate availability as verified source completeness.
