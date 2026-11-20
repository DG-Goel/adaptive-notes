# Java run

{
  "classification": "Partial live execution",
  "selected_slots": [
    1,
    2,
    3,
    4,
    5
  ],
  "rotation_policy": "pinned_primary_round_robin_recovery_same_org",
  "continue_validation_failures": true,
  "live": false,
  "source_sha256": "fba44e6e030a3ead04edc4c16fba674d8403d8de1f08e7fb936124ed1b734e1a",
  "total_chunks": 48,
  "completed_chunks": 47,
  "recovered_truncations": 0,
  "requests_attempted": 48,
  "http_successes": 48,
  "http_429": 0,
  "input_tokens": 4800,
  "output_tokens": 9600,
  "unknown_usage_attempts": 0,
  "elapsed_seconds": 240.0,
  "errors": [
    {
      "request_id": "offline-java-0000",
      "type": "offline_revalidation_failed",
      "error": "Invalid canonical wire schema"
    },
    {
      "request_id": "offline-java-0000",
      "error": "Existing operation requires review; automatic redispatch refused",
      "state": "validation_failed"
    }
  ],
  "assembly": "completed",
  "quality_score": null,
  "total_actual_tokens": 14400,
  "invocation_elapsed_seconds": 1.4380000000001019,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 0.42599999999583815,
  "token_count_note": "Input/output sums include reported usage only; missing usage is not zero consumption.",
  "unresolved_source_ids": [],
  "ingestion_status": "success",
  "source_representation_complete": true,
  "notes_status": "UNVERIFIED_PREVIEW",
  "items": 47,
  "source_units_with_items": 12
}

Semantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.
