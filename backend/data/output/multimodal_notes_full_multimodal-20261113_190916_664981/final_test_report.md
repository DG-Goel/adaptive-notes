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
  "total_chunks": 24,
  "completed_chunks": 0,
  "recovered_truncations": 13,
  "requests_attempted": 37,
  "http_successes": 20,
  "http_429": 0,
  "input_tokens": 55455,
  "output_tokens": 26930,
  "unknown_usage_attempts": 17,
  "elapsed_seconds": 1701.2986462116241,
  "errors": [
    {
      "request_id": "multimodal-20261113_190916_664981-0000",
      "chunk_number": 1,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Artificial intelligence (AI)\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Artificial intelligence is an overarching field in computer science where we train computers to perform tasks which humans are generally good at.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0003\"],"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0001",
      "chunk_number": 2,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0004",
      "chunk_number": 3,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0007",
      "chunk_number": 4,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0013",
      "chunk_number": 5,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0016",
      "chunk_number": 6,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"binary classification\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"two categories as an output it\\'s called binary classification\",\\n            \"refs\": [\"Q0000\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"aliases\": null,"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0017",
      "chunk_number": 7,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0020",
      "chunk_number": 8,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0023",
      "chunk_number": 9,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"unsupervised learning\",\\n        \"refs\": [\"Q0004\", \"Q0015\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Unsupervised learning is described as a type of problem\u2011solving where a learner notices patterns and categorizes data without explicit supervision.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"explanation_of_mistake\",\\n            \"ref"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0024",
      "chunk_number": 10,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0027",
      "chunk_number": 11,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"unsupervised learning\",\\n        \"refs\": [\"Q0000\", \"Q0007\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Unsupervised learning involves providing an unlabeled data set to a machine learning program, which then learns to identify patterns and structures in the data without explicit guidance.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"pre"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0028",
      "chunk_number": 12,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"unsupervised learning\",\\n        \"refs\": [\"Q0007\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Unsupervised learning provides an unlabeled data set to an ML program and it learns to identify patterns and structures in data without any explicit guidance.\",\\n            \"refs\": [\"Q0007\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n  ",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0029",
      "chunk_number": 13,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"data cleaning and exploration\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"cleaning and exploration\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"content\": {\\n        \"text\": \"cleaning and ex",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0030",
      "chunk_number": 14,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0036",
      "chunk_number": 15,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Feedback loop in learning groups\",\\n        \"refs\": [\"Q0004\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"The supervisor tells if the answer is correct and the error feedback is passed to the rest of the group, which adjusts their weights or brains to eventually arrive at the right answer.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"exp"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0037",
      "chunk_number": 16,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Error feedback loop in learning groups\",\\n        \"refs\": [\"Q0003\", \"Q0004\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"When a group makes a mistake, the supervisor provides feedback and the error information is passed to the rest of the group, which then adjusts its internal weights (or brain) to improve future answers.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n     "
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0038",
      "chunk_number": 17,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0039",
      "chunk_number": 18,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0040",
      "chunk_number": 19,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Criteria for choosing between statistical machine learning and deep learning\",\\n        \"refs\": [\"Q0000\", \"Q0001\", \"Q0002\", \"Q0003\", \"Q0004\", \"Q0005\", \"Q0006\", \"Q0007\", \"Q0008\", \"Q0009\", \"Q0010\", \"Q0011\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"You should consider a set of parameters such as feature type, data structure, and data volume when deciding between statistical ML and deep learning.\",\\n            \"basis\": \"explicit\",\\n            \"avail"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0041",
      "chunk_number": 20,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/1/content/claims/0/instructional_role' does not validate with /properties/items/items/properties/content/properties/claims/items/properties/instructional_role/anyOf/0/enum: value must be one of 'correct_demonstration', 'deliberately_incorrect_demonstration', 'identified_mistake', 'explanation_of_mistake', 'corrected_approach', 'alternative_valid_approach', 'prerequisite', 'continuation', 'unresolved'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Guideline: Use statistical machine learning for simple, structured features such as tables.\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"If you have simple features, let\\'s say structured data, tables, use statis"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0042",
      "chunk_number": 21,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0043",
      "chunk_number": 22,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0044",
      "chunk_number": 23,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0047",
      "chunk_number": 24,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Generative AI\",\\n        \"refs\": [\"Q0006\", \"Q0012\", \"Q0014\", \"Q0019\", \"Q0020\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Generative AI is a category of AI where the objective is to generate new content.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0006\"],\\n            \"related_refs\": []\\n         "
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0048",
      "chunk_number": 25,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0051",
      "chunk_number": 26,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"generative AI\",\\n        \"refs\": [\"Q0000\", \"Q0004\", \"Q0005\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"You can do the work of a poet, for example, using generative AI.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          },\\n          {\\n            \"text\": \"Modern"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0052",
      "chunk_number": 27,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"generative AI\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"You can do the work of a poet, for example, using generative AI.\",\\n            \"refs\": [\"Q0000\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"aliases\": null,\\n    ",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0053",
      "chunk_number": 28,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0054",
      "chunk_number": 29,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Large language models are trained on massive datasets\",\\n        \"refs\": [\"Q0001\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Large language models are trained on a huge volume of data such as Wikipedia articles, Google news articles, online books, and so on.\",\\n            \"refs\": [\"Q0001\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"p"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0055",
      "chunk_number": 30,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0058",
      "chunk_number": 31,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0061",
      "chunk_number": 32,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0068",
      "chunk_number": 33,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"AI agent\",\\n        \"refs\": [\"Q0019\", \"Q0020\", \"Q0024\", \"Q0032\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"An AI agent has access to tools, knowledge, memory, and an LLM and can perform autonomous tasks.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0019\"],\\n            \"related_refs\": []\\n        "
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0069",
      "chunk_number": 34,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0072",
      "chunk_number": 35,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"AI agent\",\\n        \"refs\": [\"Q0003\", \"Q0004\", \"Q0005\", \"Q0018\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"AI agent has access to tools, knowledge, memory, and uses an LLM as an integral component.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0003\"],\\n            \"related_refs\": []\\n          },\\n"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0073",
      "chunk_number": 36,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"concept_name\": {\\n        \"text\": \"Difference between AI agent and agentic AI\",\\n        \"refs\": [\"Q0001\", \"Q0003\", \"Q0004\", \"Q0008\", \"Q0010\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"An AI agent has access to tools, knowledge, memory, and uses an LLM as an integral component to perform autonomous tasks.\",\\n            \"refs\": [\"Q0003\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructio",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_190916_664981-0074",
      "chunk_number": 37,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    }
  ],
  "assembly": "not_run",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 1756.6399999999994,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 155.15499999999884,
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
  "source_representation_complete": false
}

Semantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.
