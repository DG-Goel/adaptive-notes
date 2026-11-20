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
  "total_chunks": 27,
  "completed_chunks": 4,
  "recovered_truncations": 8,
  "requests_attempted": 31,
  "http_successes": 9,
  "http_429": 0,
  "input_tokens": 27969,
  "output_tokens": 7086,
  "unknown_usage_attempts": 22,
  "elapsed_seconds": 1089.562584400177,
  "errors": [
    {
      "request_id": "multimodal-20261113_194734_731372-0000",
      "chunk_number": 1,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Artificial intelligence\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Artificial intelligence is an overarching field in computer science where we train computers to perform tasks which humans are generally good at.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0003\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"tex"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0007",
      "chunk_number": 2,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"relationship_type\": {\\n        \"text\": \"trained on\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"the spam detector (human) is trained on 10,000 past spam emails and 10,000 non\u2011spam emails\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0003\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"subject\": {\\n        \"text\": \"spam detector (human)\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0013",
      "chunk_number": 3,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"machine learning\",\\n        \"refs\": [\"Q0001\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"machine learning is a discipline in computer science where we train machines on data so that they can make predictions without explicit programming\",\\n            \"refs\": [\"Q0001\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"definition"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0016",
      "chunk_number": 4,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"classification\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"classification is a supervised machine learning problem where the output is a fixed set of class labels (e.g., two categories or four categories).\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0000\", \"Q0005\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"te"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0023",
      "chunk_number": 5,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"clustering\",\\n        \"refs\": [\"Q0007\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"clustering is a technique\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0007\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"is a technique of\",\\n        \"refs\": [\"Q0004\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"clustering is a techniqu"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0030",
      "chunk_number": 6,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"unsupervised machine learning\",\\n        \"refs\": [\"Q0000\", \"Q0007\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"unsupervised machine learning provides an unlabeled data set to an ML program and it learns to identify patterns and structures in data without any explicit guidance\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n     "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0031",
      "chunk_number": 7,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"unsupervised learning\",\\n        \"refs\": [\"Q0007\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"unsupervised learning provides an unlabeled data set to an ML program and it learns to identify patterns and structures in data without any explicit guidance\",\\n            \"refs\": [\"Q0007\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n  "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0034",
      "chunk_number": 8,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"cleaning and exploration\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"cleaning and exploration\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"is a prerequisi"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0037",
      "chunk_number": 11,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Assign individual responsibility to each student to detect a specific part of the Koala\\'s body (e.g., Mike detects eyes, Mohan detects nose).\",\\n        \"refs\": [\"Q0005\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"You can make this a teamwork and give individual responsibility to each of these students such as Mike can work on detecting only eyes, Mohan can work on detecting only nose.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequi"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0038",
      "chunk_number": 12,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0041",
      "chunk_number": 13,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0044",
      "chunk_number": 14,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Mike, Mohan, Saqib (and others) detect koala\\'s eyes, nose, and ears in an image.\",\\n        \"refs\": [\"Q0000\", \"Q0001\", \"Q0002\", \"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Students provide scores for eyes, nose, and ears; if scores exceed thresholds they claim the presence of those features.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0000\", \"Q0001\"],\\n            \"related_refs\": []\\n       "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0045",
      "chunk_number": 15,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0048",
      "chunk_number": 16,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0055",
      "chunk_number": 17,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Artificial neural network\",\\n        \"refs\": [\"Q0010\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"An artificial neural network consists of an input layer, one or more hidden layers, and an output layer.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0010\", \"Q0011\", \"Q0012\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"has_part\",\\n    "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0062",
      "chunk_number": 18,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Features: simple (structured data, tables) versus complex (images, videos, etc.)\",\\n        \"refs\": [\"Q0002\", \"Q0003\", \"Q0004\", \"Q0008\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"If you have simple features, such as structured data or tables, use statistical machine learning.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0003\"],\\n            \"related_refs\": []\\n          },\\n          {\\n            \""
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0069",
      "chunk_number": 19,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"feed forward neural network\",\\n        \"refs\": [\"Q0001\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"A feed forward neural network has input, hidden, and output layers with information flowing only forward and no loops.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"PARTIALLY_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0001\"],\\n            \"related_refs\": "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0070",
      "chunk_number": 20,
      "type": "SchedulerHold",
      "error": "Operation failed validation or admission; inspect secret-free audit"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0073",
      "chunk_number": 21,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Transformer architecture\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Transformer is described as the most important architecture.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"prerequisite for modern generative AI models\",\\n        \"refs\": [\"Q0001\", \"Q000"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0076",
      "chunk_number": 22,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"generative AI\",\\n        \"refs\": [\"Q0006\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"generative AI is a category of AI where the objective is to generate new content\",\\n            \"refs\": [\"Q0006\"],\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"definition\",\\n        \"refs\": [\"Q0006\"],\\n        \"claims\": [\\n       "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0083",
      "chunk_number": 23,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Generative AI\",\\n        \"refs\": [\"Q0004\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Generative AI uses large language models (LLMs).\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0004\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"us"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0084",
      "chunk_number": 24,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Traditional AI uses tools like XGBoost and scikit\u2011learn.\",\\n        \"refs\": [\"Q0002\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Traditional AI uses tools like XGBoost and scikit\u2011learn.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0002\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0085",
      "chunk_number": 25,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"content\": {\\n        \"text\": \"generative AI can do the work of a poet\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"generative AI can do the work of a poet\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"tex",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0087",
      "chunk_number": 27,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Buddy\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Buddy doesn\\'t understand the meaning of biryani or food or cherries the way humans do.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"is a\",\\n        \"refs\": [\"Q0002\"],\\n        \"claims\": [\\n          {\\n           "
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0088",
      "chunk_number": 28,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"Buddy\",\\n        \"refs\": [\"Q0000\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Buddy doesn\\'t understand the meaning of biryani or food or cherries the way humans do.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0000\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"is a\",\\n        \"refs\": [\"Q0002\"],\\n        \"claims\": [\\n          {\\n           ",
      "recovery_status": "No smaller approved source-boundary split remains; identical retry prohibited"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0090",
      "chunk_number": 30,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"ChatGPT\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"ChatGPT\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0003\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"uses\",\\n        \"refs\": [\"Q0003\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"uses\",\\n            \"basis\": \"explicit\",\\n            \"availability\""
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0097",
      "chunk_number": 31,
      "type": "GroqProviderError",
      "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"Generated JSON does not match the expected schema. Please adjust your prompt. See 'failed_generation' for more details. Error: jsonschema: '/items/0' does not validate with /properties/items/items/required: missing properties: 'content'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"subject\": {\\n        \"text\": \"human intervention (RLHF)\",\\n        \"refs\": [\"Q0003\", \"Q0004\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"OpenAI used a similar approach of human intervention, RLHF, and a huge workforce of humans to make chat GPT less toxic.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": \"prerequisite\",\\n            \"refs\": [\"Q0003\", \"Q0004\"],\\n            \"related_refs\": []\\n          }\\n        ]\\n      },\\n      \"relationship_type\": {\\n        \"text\": \"p"
    },
    {
      "request_id": "multimodal-20261113_194734_731372-0104",
      "chunk_number": 32,
      "type": "SchedulerHold",
      "error": "quota_exhausted: insufficient aggregate headroom"
    }
  ],
  "assembly": "completed",
  "quality_score": null,
  "total_actual_tokens": null,
  "invocation_elapsed_seconds": 1155.061999999998,
  "elapsed_basis": "First durable claim to latest operation completion, including resume gaps and quota waits; invocation time is separate.",
  "physical_call_seconds": 102.28500000000349,
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
  "items": 2,
  "source_units_with_items": 1
}

Semantic checks are heuristics. Educational quality has not yet been manually reviewed. No quality score is inferred from HTTP success.
