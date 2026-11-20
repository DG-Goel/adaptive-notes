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
  "total_chunks": 17,
  "completed_chunks": 2,
  "recovered_truncations": 6,
  "requests_attempted": 23,
  "http_successes": 15,
  "http_429": 0,
  "input_tokens": 46025,
  "output_tokens": 16951,
  "unknown_usage_attempts": 8,
  "elapsed_seconds": 812.9416117668152,
  "errors": [
    {
      "request_id": "multimodal-20261113_185444_813521-0000",
      "chunk_number": 1,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"Artificial intelligence definition\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Artificial intelligence is this overarching field in computer science where we train computers to perform tasks which we the humans are generally good at.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\""
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0001",
      "chunk_number": 2,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"When you start learning AI, you will come across so many different jargons that will most likely confuse you.\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"When you start learning AI, you will come across so many different jargons that will most likely confuse you.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequi"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0002",
      "chunk_number": 3,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0003",
      "chunk_number": 4,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"k-means etc that you use for tasks such as classification, regression etc.\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"k-means etc that you use for tasks such as classification, regression etc.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n        ",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0004",
      "chunk_number": 5,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0007",
      "chunk_number": 6,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0013",
      "chunk_number": 7,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0016",
      "chunk_number": 8,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/1/explanation_text/claims/0/instructional_role' does not validate with /properties/items/items/properties/explanation_text/properties/claims/items/properties/instructional_role/anyOf/0/enum: value must be one of 'correct_demonstration', 'deliberately_incorrect_demonstration', 'identified_mistake', 'explanation_of_mistake', 'corrected_approach', 'alternative_valid_approach', 'prerequisite', 'continuation', 'unresolved'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"Classification vs Regression\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Two categories as an output is called binary classification; for multiple categories it is called multi\u2011class classification; r"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0023",
      "chunk_number": 9,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0030",
      "chunk_number": 10,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0036",
      "chunk_number": 11,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0/topic' does not validate with /properties/items/items/properties/topic/type: expected object, but got null\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"explanation_text\": {\\n        \"text\": \"You have input layer, hidden layer, output layer. You can have any number of hidden layers and any number of neurons. In a neural network for cat and dog detection, middle neurons detect features like ears, eyes, tails, and higher layers combine these to recognize higher\u2011level patterns such as a cat\\'s head.\",\\n        \"refs\": [\\n          \"Q0010\",\\n          \"Q0011\",\\n          \"Q0012\"\\n        ],\\n        \"claims\": [\\n          {\\n            \"text\": \"Neural networks have an input layer, hidden layer(s), and an output layer.\",\\n        "
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0037",
      "chunk_number": 12,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0040",
      "chunk_number": 13,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"Choosing between statistical machine learning and deep learning\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"and now you want to figure out, should I use statistical ML or deep learning?\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n   "
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0041",
      "chunk_number": 14,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0044",
      "chunk_number": 15,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"Feed\u2011forward neural network\",\\n        \"refs\": [\"Q0001\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"A feed\u2011forward neural network has no loops; information flows from the input layer through hidden layers to the output layer.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0001\"],\\n            \"related_refs\": []\\n    "
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0045",
      "chunk_number": 16,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0046",
      "chunk_number": 17,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0047",
      "chunk_number": 18,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0054",
      "chunk_number": 19,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"With this extra power and knowledge, NowBuddy can complete the next set of words on a history subject, give you a nutrition advice, or even write a poem.\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"NowBuddy can complete the next set of words on a history subject, give you nutrition advice, or write a poem.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0058",
      "chunk_number": 21,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_185444_813521-0061",
      "chunk_number": 22,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    }
  ],
  "assembly": "completed",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 868.155999999999,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 81.43800000000192,
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
