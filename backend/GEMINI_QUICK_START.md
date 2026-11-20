# Gemini Provider - Quick Start Guide

## 1-Minute Setup

### Step 1: Get API Key
Visit: https://aistudio.google.com/apikey

### Step 2: Add to .env
```bash
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Step 3: Install (if needed)
```bash
pip install google-genai==2.33.0
```

### Step 4: Test
```bash
python run_gemini_smoke_test.py
```

Expected output: `✅ SMOKE TEST PASSED`

### Step 5: Run Full Extraction
```bash
python run_full_document_gemini.py
```

---

## Command Cheat Sheet

```bash
# Unit tests (no API calls, instant)
pytest tests/test_gemini_provider.py -v

# Regression suite (no API calls, ~20 seconds)
pytest tests/ --ignore=tests/test_ingestion.py --ignore=tests/test_ingestion_fast.py -v

# Smoke test (5 units, minimal API usage, ~10 seconds)
python run_gemini_smoke_test.py

# Full extraction (full document, significant API usage)
python run_full_document_gemini.py

# Check configuration
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY', 'NOT SET')[:20])"
```

---

## Common Issues

### ❌ "GEMINI_API_KEY not set"
**Fix**: Add key to `.env` file

### ❌ "authentication error"
**Fix**: Check API key is valid at https://aistudio.google.com/apikey

### ❌ "rate_limit error"
**Fix**: Wait a minute or upgrade API tier

### ❌ "daily quota exhausted"
**Fix**: Wait 24 hours or upgrade to paid tier

### ⚠️ "Zero items extracted"
**Fix**: Check safety filters, review diagnostic logs

---

## Documentation Files

- `GEMINI_PROVIDER_GUIDE.md` - Complete user guide
- `GEMINI_IMPLEMENTATION_SUMMARY.md` - Technical details
- `GEMINI_QUICK_START.md` - This file
- `.env.template` - Configuration template

---

## Getting Help

1. Check error message in console output
2. Review `GEMINI_PROVIDER_GUIDE.md` troubleshooting section
3. Check diagnostic logs in `data/diagnostics/failed_responses/`
4. Verify API key and quota at https://console.cloud.google.com/

---

## Status Check

```bash
# Verify everything is ready
python -c "
from app.extraction.llm_provider import GeminiProvider
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ Import successful')
print(f'✅ API key: {\"SET\" if os.getenv(\"GEMINI_API_KEY\") else \"NOT SET\"}')
print(f'✅ Model: {os.getenv(\"GEMINI_MODEL\", \"NOT SET\")}')
try:
    p = GeminiProvider()
    print('✅ Provider initialized')
except Exception as e:
    print(f'❌ Provider error: {e}')
"
```

---

## Next Steps After Smoke Test

1. ✅ Smoke test passes → Run full extraction
2. ⚠️ Smoke test warnings → Review warnings, adjust settings
3. ❌ Smoke test fails → Check API key and quotas

---

**That's it! The provider is ready to use.**
