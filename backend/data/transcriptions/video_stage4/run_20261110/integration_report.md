# Stage 4 integration report

```json
{
  "speech_segments": 2181,
  "visual_records": 501,
  "exact_repeated_readings": 188,
  "high_events": 40,
  "high_events_with_candidates": 40,
  "visual_records_in_speech_gaps": 26,
  "unresolved_items": 241,
  "verified_visual_records": 0,
  "processing_seconds": 0.8191953999994439
}
```

No inference performed. Image hashes verified; historical artifact hashes checked before and after.

All raw readings retain source-artifact/index pointers, hashes, crop/task/model metadata and errors. No canonical content approved.

Same-frame conflicting path strings and other divergent readings remain unresolved. Different-time OCR changes are chronological candidates, not automatic corrections.

Mortgage remains VISUAL_CONTEXT_REQUIRED; Windows-path candidate remains unverified; successful changed-task retry and historical errors are retained. Clipped monthly-interest characters remain unresolved.

Future Source Unit integration must retain modality, verification status, provenance and unresolved flags; it must not treat candidate availability as verified source completeness.

Validation: all 6 offline Stage 4 tests passed. Real output checks passed for exact speech preservation, chronological timeline, unique evidence IDs and no canonical promotion.

Files added: multimodal_transcript.py, tests/test_multimodal_transcript.py, TRANSCRIPTION_STAGE4.md and the five files in this versioned output directory. No prior stage artifacts modified. See TRANSCRIPTION_STAGE4.md for deduplication, conflict and model-interpretation limitations.
