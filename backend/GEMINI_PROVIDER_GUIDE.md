# Gemini Provider Integration Guide

## Overview

The Gemini provider enables knowledge extraction using Google's Gemini API. This guide covers setup, usage, testing, and troubleshooting.

## Features

- ✅ Full LLMProvider interface compliance
- ✅ JSON output mode support
- ✅ Token budget management (TPM tracking)
- ✅ Retry logic for transient failures
- ✅ Adaptive chunk splitting for truncation
- ✅ Comprehensive error handling
- ✅ Authentication and quota error detection
- ✅ Safety filter and recitation detection
- ✅ Provenance preservation
- ✅ No silent fallback to mock provider

## Setup

### 1. Install Dependencies

The required `google-genai` package is included in `requirements.txt`:

```bash
pip install google-genai==2.33.0
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Copy the key

### 3. Configure Environment

Add to `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

Available models:
- `gemini-2.0-flash-exp` (recommended, fast)
- `gemini-1.5-flash`
- `gemini-1.5-pro`
- `gemini-pro`

## Usage

### Programmatic Usage

```python
from app.extraction.llm_provider import GeminiProvider
from app.extraction.extractor import KnowledgeExtractor

# Initialize provider
provider = GeminiProvider(
    model="gemini-2.0-flash-exp",
    api_key="your_api_key",
    tokens_per_minute=15000  # Adjust based on your tier
)

# Use with extractor
extractor = KnowledgeExtractor(provider, verbose=True)
result = extractor.extract(source_document)
```

### Smoke Test (Recommended First Step)

Test the integration with a small sample before running full extraction:

```bash
python run_gemini_smoke_test.py
```

This will:
- Test API authentication
- Extract from 5 source units
- Validate JSON parsing
- Check provenance
- Report any issues

Expected output:
```
✅ SMOKE TEST PASSED
Gemini provider is working correctly!
```

### Full Document Extraction

After smoke test passes:

```bash
python run_full_document_gemini.py
```

This runs the complete pipeline with:
- Token budget management
- Automatic retry on failures
- Adaptive chunk splitting
- Detailed progress reporting

## Testing

### Unit Tests (No API Calls)

All unit tests use mocked responses and consume **zero API quota**:

```bash
# Test Gemini provider only
pytest tests/test_gemini_provider.py -v

# Test all providers
pytest tests/test_gemini_provider.py tests/test_groq_provider.py -v

# Full regression suite (excluding ingestion)
pytest tests/ --ignore=tests/test_ingestion.py --ignore=tests/test_ingestion_fast.py -v
```

### Integration Test (Real API)

Only run this when you want to test with real API calls:

```bash
# Requires GEMINI_API_KEY in environment
python run_gemini_smoke_test.py
```

## Error Handling

### Authentication Errors

```
❌ ERROR: Gemini authentication error: 401 Unauthorized
```

**Solution**: Check your API key in `.env` file.

### Rate Limit Errors

```
⚠️  Gemini rate_limit error (TPM): 429 Too Many Requests
```

**Solution**: 
- Wait for rate limit window to reset
- Reduce `tokens_per_minute` parameter
- Consider upgrading API tier

### Daily Quota Exhausted

```
❌ Gemini daily quota exhausted (tokens per day)
```

**Solution**:
- Wait until quota resets (usually 24 hours)
- Upgrade to paid tier for higher quotas
- No retries attempted (permanent error for this run)

### Truncation Errors

```
⚠️  Response truncated due to max_tokens limit
```

**Solution**: Automatic adaptive chunk splitting will attempt to handle this.

### Safety Filters

```
⚠️  Response blocked by safety filter
```

**Solution**: Content triggered Gemini's safety filters. Review source content.

### JSON Parsing Failures

```
❌ Failed to parse JSON response
```

**Solution**: 
- Check diagnostic files in `data/diagnostics/failed_responses/`
- May indicate model returning non-JSON text
- Try different model or temperature

## Token Budget Management

The provider includes automatic TPM (tokens per minute) tracking:

```python
provider = GeminiProvider(
    tokens_per_minute=15000  # Free tier default
)
```

Common TPM limits:
- Free tier: 15,000 TPM
- Pay-as-you-go: 100,000 TPM
- Enterprise: Custom limits

The extractor will automatically:
- Estimate token usage before each request
- Track rolling window of token consumption
- Back off when approaching limits
- Retry with exponential backoff on rate limits

## Comparison with Other Providers

| Feature | Gemini | Groq | OpenAI |
|---------|--------|------|--------|
| JSON Mode | ✅ | ✅ | ✅ |
| TPM Tracking | ✅ | ✅ | ✅ |
| Free Tier | ✅ | ✅ | ❌ |
| Safety Filters | ✅ (strict) | ❌ | ✅ (moderate) |
| Speed | Fast | Very Fast | Medium |
| Cost | Low | Free | Medium-High |

## Output Format

The provider returns JSON matching the extraction schema:

```json
{
  "concepts": [...],
  "definitions": [...],
  "explanations": [...],
  "examples": [...],
  "facts": [...],
  "formulas": [...],
  "procedures": [...],
  "relationships": [...]
}
```

## Troubleshooting

### Problem: Zero items extracted

**Possible causes**:
1. Safety filters blocking all content
2. JSON parsing failures
3. Empty or malformed responses

**Debug steps**:
1. Check `data/diagnostics/failed_responses/` for raw responses
2. Review extraction metadata for error messages
3. Try smoke test with different content
4. Check model supports JSON mode

### Problem: Incomplete extraction

**Possible causes**:
1. Rate limit reached
2. Daily quota exhausted
3. Truncation without successful splitting

**Debug steps**:
1. Check `extraction_metadata.completeness`
2. Review `failed_chunks` list
3. Check for rate limit or quota errors
4. Consider reducing chunk size

### Problem: Invalid source references

**Possible causes**:
1. Model hallucinating source IDs
2. Chunking boundary issues

**Debug steps**:
1. Check warning messages in extraction log
2. Review source ID validation in knowledge document
3. Verify source markers in chunk text

## Advanced Configuration

### Custom System Instructions

```python
from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT

# Modify prompt before passing to generate()
custom_system = EXTRACTION_SYSTEM_PROMPT + "\nAdditional instructions..."

provider.generate(
    prompt=user_prompt,
    system=custom_system,
    temperature=0.0
)
```

### Temperature Control

```python
# Default: 0.0 (deterministic)
result = provider.generate(prompt, temperature=0.0)

# Higher temperature for more varied extraction (not recommended)
result = provider.generate(prompt, temperature=0.3)
```

### Max Tokens

```python
# Default: 4000 tokens
result = provider.generate(prompt, max_tokens=4000)

# Larger output budget (may trigger truncation)
result = provider.generate(prompt, max_tokens=8000)
```

## Best Practices

1. **Always run smoke test first** before full extraction
2. **Monitor extraction completeness** - aim for >95%
3. **Check provenance validity** - invalid refs indicate hallucination
4. **Review failed chunks** - may reveal content issues
5. **Use appropriate TPM limits** based on your tier
6. **Save extraction metadata** for debugging
7. **Handle quota exhaustion gracefully** - don't retry on daily quota errors

## Files Changed

- `app/extraction/llm_provider.py` - GeminiProvider implementation
- `tests/test_gemini_provider.py` - Comprehensive unit tests
- `run_gemini_smoke_test.py` - Small-scale integration test
- `run_full_document_gemini.py` - Full extraction script
- `.env.template` - Environment variable documentation
- `requirements.txt` - Dependency specification

## Support

For issues with:
- **Provider implementation**: Check unit tests and this guide
- **Gemini API**: See [Google AI Studio documentation](https://ai.google.dev/docs)
- **Extraction pipeline**: Review existing Groq provider examples
- **Rate limits**: Check your API tier at [Google Cloud Console](https://console.cloud.google.com/)

## References

- [Google Generative AI Python SDK](https://github.com/googleapis/python-generative-ai)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [API Key Management](https://aistudio.google.com/apikey)
