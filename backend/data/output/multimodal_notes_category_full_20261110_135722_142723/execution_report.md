# Full multimodal category-partitioned run

{
  "classification": "PARTIAL_OR_BLOCKED",
  "categories_attempted": [
    "facts",
    "definitions",
    "explanations"
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
  "attempted_requests": 168,
  "input_tokens": 473038,
  "output_tokens": 140785,
  "unknown_usage_attempts": 26,
  "actual_total_tokens": null,
  "source_grounding": "Mechanical validation only; no human semantic verification",
  "blocker": {
    "category": "explanations",
    "errors": [
      {
        "request_id": "multimodal-20261110_160719_210532-0007",
        "chunk_number": 2,
        "type": "GroqProviderError",
        "error": "Groq API call failed: Groq API call failed: Error code: 400 - {'error': {'message': \"max completion tokens reached before generating a valid document: the output was truncated to fit max_completion_tokens and is missing required content. Increase max_completion_tokens. See 'failed_generation' for the truncated output. Error: jsonschema: '' does not validate with /required: missing properties: 'abstentions', 'excluded'\", 'type': 'invalid_request_error', 'code': 'json_validate_failed', 'failed_generation': '{\\n  \"items\": [\\n    {\\n      \"topic\": {\\n        \"text\": \"Java functions (methods) anatomy and basics\",\\n        \"refs\": [\"Q0014\", \"Q0015\", \"Q0016\", \"Q0017\", \"Q0018\", \"Q0019\", \"Q0020\", \"Q0021\", \"Q0022\", \"Q0023\", \"Q0024\", \"Q0025\"],\\n        \"claims\": [\\n          {\\n            \"text\": \"Now let\\'s see how we can code a function in java.\",\\n            \"basis\": \"explicit\",\\n            \"availability\": \"SOURCE_SUPPORTED\",\\n            \"literal_kind\": \"verbal\",\\n            \"instructional_role\": null,\\n            \"refs\": [\"Q0014\""
      },
      {
        "request_id": "multimodal-20261110_160719_210532-0008",
        "chunk_number": 3,
        "type": "SchedulerHold",
        "error": "Operation failed validation or admission; inspect secret-free audit"
      },
      {
        "request_id": "multimodal-20261110_160719_210532-0011",
        "chunk_number": 4,
        "type": "GroqProviderError",
        "error": "Groq API call failed: Groq API call failed: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01jmkg4pjje008tpsxb8p971e6` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 196670, Requested 3733. Please try again in 2m54.095999999s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}"
      }
    ],
    "remaining_primary_requests": 66
  },
  "knowledge_items": 420,
  "knowledge_counts": {
    "concepts": 0,
    "definitions": 1,
    "explanations": 0,
    "examples": 0,
    "facts": 419,
    "formulas": 0,
    "procedures": 0,
    "relationships": 0
  }
}

Partial outputs are not complete lecture notes. Native per-field Task 12A claims and local validation retained. No images sent; no OCR candidates promoted. All quota/authorization gates remain mandatory.
