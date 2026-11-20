# Full multimodal category-partitioned run

{
  "classification": "PARTIAL_OR_BLOCKED",
  "categories_attempted": [
    "facts",
    "definitions",
    "explanations",
    "concepts",
    "examples",
    "procedures",
    "relationships"
  ],
  "all_categories": [
    "facts",
    "definitions",
    "explanations",
    "concepts",
    "examples",
    "procedures",
    "relationships",
    "formulas"
  ],
  "attempted_requests": 157,
  "input_tokens": 313194,
  "output_tokens": 87950,
  "unknown_usage_attempts": 54,
  "actual_total_tokens": null,
  "source_grounding": "Mechanical validation only; no human semantic verification",
  "blocker": {
    "category": "relationships",
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
    "remaining_primary_requests": 4
  },
  "knowledge_items": 69,
  "knowledge_counts": {
    "concepts": 0,
    "definitions": 2,
    "explanations": 0,
    "examples": 0,
    "facts": 65,
    "formulas": 0,
    "procedures": 0,
    "relationships": 2
  }
}

Partial outputs are not complete lecture notes. Native per-field Task 12A claims and local validation retained. No images sent; no OCR candidates promoted. All quota/authorization gates remain mandatory.
