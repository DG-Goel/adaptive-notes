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
  "total_chunks": 20,
  "completed_chunks": 18,
  "recovered_truncations": 0,
  "requests_attempted": 20,
  "http_successes": 19,
  "http_429": 0,
  "input_tokens": 55390,
  "output_tokens": 3983,
  "unknown_usage_attempts": 1,
  "elapsed_seconds": 268.8204438686371,
  "errors": [
    {
      "request_id": "multimodal-20261113_194301_052125-0111",
      "chunk_number": 18,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194301_052125-0118",
      "chunk_number": 19,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'procedure_name', 'steps', 'prerequisites', 'outcomes'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"content\": {\\n        \"procedure_name\": {\\n          \"text\": \"Onboard a new employee using an agentic AI workflow in n8n\",\\n          \"refs\": [\"Q0005\", \"Q0007\"],\\n          \"claims\": [\\n            {\\n              \"text\": \"Onboard a new employee using an agentic AI workflow in n8n\",\\n              \"basis\": \"explicit\",\\n              \"availability\": \"SOURCE_SUPPORTED\",\\n              \"literal_kind\": \"verbal\",\\n              \"instructional_role\": \"correct_demonstration\",\\n              \"refs\": [\"Q0005\", \"Q0007\"],\\n              \"related_refs\": []\\n     "
    }
  ],
  "assembly": "completed",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 268.96900000000096,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 22.90599999999904,
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
