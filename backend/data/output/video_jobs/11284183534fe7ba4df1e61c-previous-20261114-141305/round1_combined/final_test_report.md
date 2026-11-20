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
  "rotation_policy": "next_free_key",
  "continue_validation_failures": true,
  "live": true,
  "source_sha256": "c3bbb1f09ab7d9f1bd403207022eaf908859365a5b175c00386023653696e5cb",
  "total_chunks": 12,
  "completed_chunks": 0,
  "recovered_truncations": 2,
  "requests_attempted": 12,
  "http_successes": 10,
  "http_429": 0,
  "input_tokens": 30327,
  "output_tokens": 13460,
  "unknown_usage_attempts": 2,
  "elapsed_seconds": 201.81282758712769,
  "errors": [
    {
      "request_id": "multimodal-20261114_082057_491621-0010",
      "chunk_number": 3,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0024",
      "chunk_number": 5,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0007",
      "chunk_number": 2,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0000",
      "chunk_number": 1,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0017",
      "chunk_number": 4,
      "type": "SchedulerHold",
      "error": "quota_exhausted: insufficient aggregate TPM headroom"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0031",
      "chunk_number": 7,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0028",
      "chunk_number": 6,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"rows\": [\\n    {\\n      \"item\": \"deep_learning_definition\",\\n      \"category\": \"definitions\",\\n      \"field\": \"term\",\\n      \"element\": 0,\\n      \"part\": \"value\",\\n      \"text\": \"deep learning\",\\n      \"refs\": [\"Q0023\"],\\n      \"basis\": \"explicit\",\\n      \"availability\": \"SOURCE_SUPPORTED\",\\n      \"literal_kind\": \"verbal\",\\n      \"instructional_role\": null,\\n      \"related_refs\": []\\n    },\\n    {\\n      \"item\": \"deep_learning_definition\",\\n      \"category\": \"definitions\",\\n      \"field\": \"definition_text\",\\n      \"element"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0045",
      "chunk_number": 9,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0038",
      "chunk_number": 8,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"rows\": [\\n    {\\n      \"item\": \"generative_ai\",\\n      \"category\": \"definitions\",\\n      \"field\": \"term\",\\n      \"element\": 0,\\n      \"part\": \"value\",\\n      \"text\": \"generative AI\",\\n      \"refs\": [\"Q0006\"],\\n      \"basis\": \"explicit\",\\n      \"availability\": \"SOURCE_SUPPORTED\",\\n      \"literal_kind\": \"verbal\",\\n      \"instructional_role\": null,\\n      \"related_refs\": []\\n    },\\n    {\\n      \"item\": \"generative_ai\",\\n      \"category\": \"definitions\",\\n      \"field\": \"definition_text\",\\n      \"element\": 0,\\n      \"part\": \""
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0052",
      "chunk_number": 10,
      "type": "SchedulerHold",
      "error": "quota_exhausted: insufficient aggregate TPM headroom"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0059",
      "chunk_number": 11,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0029",
      "chunk_number": 6,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0039",
      "chunk_number": 8,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261114_082057_491621-0042",
      "chunk_number": 8,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    }
  ],
  "assembly": "not_run",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 202.0779999999977,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 50.2190000000046,
  "token_count_note": "Input/output sums include reported usage only; missing usage is not zero consumption.",
  "unresolved_source_ids": [
    "V560b8780d224850c5719",
    "V174655c7c493daac343e",
    "V639552ec141304bc074e",
    "Vc44b2d575381057d592e",
    "Ve7c7f5fdca789b1c2644",
    "Vf934be3f7209b5fa1b74",
    "V5f2513df0d6962b753c8",
    "V87b9e7224952607e8c9f",
    "V85eb039257ef773c606d",
    "V85a536187fe40c3b7fee",
    "V608ef9ecff7b0cf54e79",
    "V53bb842d4fc62dbfb170",
    "V1b1fe6ab47189f740e97",
    "V37f990535c700bc002f6",
    "V72be74589e1ba98cd238",
    "V95796dc6d316421424b6",
    "Ve1dc7d1f8b4341acd689",
    "V341bad2a264ee8f1009c",
    "V8a5011e2aeba40276fe2",
    "Vbac48e4ab1fe8dd9a1df",
    "Vcecef7423a23cf157fd4",
    "V2d39e9bc18960253c0f4",
    "Ve9d5cc489197ac4d494f",
    "V38eee86ee178bc86206c",
    "V1d750d79cc2779093a58",
    "V5d0a90cc3ec45f43fd24",
    "V8c008cd8b12070d7fcf5",
    "V7106760f8fd7a7c26380",
    "Vc72b5ddbaca7b9bb9419",
    "V79ab3fb5bc66624a927d"
  ],
  "ingestion_status": "success",
  "source_representation_complete": false,
  "missing_chunk_serials": [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11
  ]
}

Semantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.
