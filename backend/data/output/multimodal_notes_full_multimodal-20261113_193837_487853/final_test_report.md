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
  "live": true,
  "source_sha256": "43eaa28edc4ffaf63192ecf61beebd16b5488c543b7e9af5d24e962335920576",
  "total_chunks": 12,
  "completed_chunks": 11,
  "recovered_truncations": 1,
  "requests_attempted": 13,
  "http_successes": 12,
  "http_429": 0,
  "input_tokens": 40810,
  "output_tokens": 2635,
  "unknown_usage_attempts": 1,
  "elapsed_seconds": 259.3212389945984,
  "errors": [
    {
      "request_id": "multimodal-20261113_193837_487853-0036",
      "chunk_number": 7,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"example_text\": {\\n        \"text\": \"will say hello sir this doesn\\'t look like koala and supervisor will be like no you are wrong.\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"will say hello sir this doesn\\'t look like koala and supervisor will be like no you are wrong.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"correct_demonstration\",\\n      "
    },
    {
      "request_id": "multimodal-20261113_193837_487853-0068",
      "chunk_number": 13,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    }
  ],
  "assembly": "completed",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 259.4529999999977,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 19.266999999999825,
  "token_count_note": "Input/output sums include reported usage only; missing usage is not zero consumption.",
  "unresolved_source_ids": [
    "V46300cc14f7db00fd74d",
    "V2aa5cbe5365003d42a81",
    "Vf06ffcd82e3db6b69787",
    "V0a7f7a1fd437cc79ffcd",
    "V885640342fce948b86a2",
    "V41638834a52fd98a30b1",
    "V60908f157bbe9aa91a4e",
    "Vb384e8207355b06dc8b1",
    "V2d8ed75e6ffa97cf5ed5",
    "Ve0431ae6c9fb71b76fa5",
    "Vdbfb0f7249993e058613",
    "V41755ec4f4de2db9b8b7",
    "Vab4ef18bf18b0c6db32c",
    "Vc68cafb4ba703147c178",
    "V5a66ff736feb0517fbef",
    "V48baadf5c6708a241fce",
    "Vd23d09c441392961ad6c",
    "V1cdfd23b329371cab4f2",
    "V83bcd4bac98c4a0a2648",
    "V15a5933b088c11c6cda1",
    "V823c39d48d50b4b4e218",
    "Vb4f0ce05d4b243c22160",
    "Vb74b2777723d157d53b9",
    "V37227bd458f5f34ab46d",
    "Ve64f9b16de05f708d6ee",
    "V6e43919c94cae0c323e5",
    "V182092b16104ce31d94e",
    "V838fe8873431c542a2a7",
    "V6b36630cafcc02f37730",
    "V334ba7769e766d055bac"
  ],
  "ingestion_status": "success",
  "source_representation_complete": false,
  "notes_status": "UNVERIFIED_PREVIEW",
  "items": 0,
  "source_units_with_items": 0
}

Semantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.
