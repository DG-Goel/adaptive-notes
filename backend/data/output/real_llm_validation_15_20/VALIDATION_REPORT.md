# 15-20 Unit Validation Report - Groq Integration
**Date:** 2026-10-26  
**Model:** Groq `openai/gpt-oss-120b`  
**Scope:** 18 source units (10,825 characters)  
**Status:** PARTIAL - Extraction completed, JSON parsing failures encountered

---

## Executive Summary

This validation attempted to scale from 5 to 18 source units. **Critical issue encountered: JSON parsing failures from LLM**. Of 2 extraction chunks:
- Chunk 1 (1,933 tokens): ✓ SUCCESS - 25 items extracted  
- Chunk 2 (840 tokens): ✗ FAILURE - JSON parsing error

**Key Finding:** The Groq provider with `openai/gpt-oss-120b` exhibits intermittent JSON parsing failures that prevent reliable extraction at scale. This is a **blocking production issue**.

---

## 1. Sample Selection

### Selection Rationale
- **Target:** 15-20 representative content units
- **Actual:** 18 units selected
- **Criteria:** content_role='content', text length >50 chars
- **Exclusions:** 91 units excluded (pictures=15, noise=6, furniture=12, structural=13, short text=45)

### Sample Characteristics
| Metric | Value |
|--------|-------|
| Source units | 18 |
| Pages covered | 2-7 (6 pages) |
| Total characters | 10,825 |
| Average length | 601 chars/unit |
| Length range | 83-1,371 chars |

### Selected Source IDs
S0012, S0013, S0016, S0017, S0020, S0022, S0023, S0024, S0027, S0028, S0029, S0030, S0036, S0037, S0041, S0042, S0044, S0047

**Selection Method:** Manual selection of varied narrative paragraphs spanning multiple pages, representing different document sections and content complexities.

---

## 2. Extraction Results

### Chunk Processing
| Chunk | Tokens | Source Units | Status | Items | Error |
|-------|--------|--------------|--------|-------|-------|
| 1 | ~1,933 | S0012-S0030 (pages 2-5) | ✓ SUCCESS | 25 | None |
| 2 | ~840 | S0036-S0047 (pages 6-7) | ✗ FAILURE | 0 | JSON parsing: "Expecting value: line 118 column 19 (char 5510)" |

### Extraction Metrics (Chunk 1 Only)
- **Items extracted:** 25
- **Extraction time:** 17.53 seconds
- **Items per unit:** 1.4 (25 items / 18 units attempted)
- **Actual rate (successful chunk):** ~2.3 items/unit (25 items / ~11 units in chunk 1)

### Knowledge Type Distribution
| Type | Count | % |
|------|-------|---|
| Concepts | 8 | 32% |
| Definitions | 1 | 4% |
| Explanations | 2 | 8% |
| Examples | 1 | 4% |
| Facts | 8 | 32% |
| Formulas | 0 | 0% |
| Procedures | 1 | 4% |
| Relationships | 4 | 16% |
| **Total** | **25** | **100%** |

---

## 3. JSON Parsing Failures - Critical Issue

### Issue Description
The LLM (Groq `openai/gpt-oss-120b`) returns malformed JSON intermittently, causing extraction to fail for entire chunks.

### Observed Failures
**Run 1 (initial attempt):**
- Chunk 1 (1,933 tokens): "Expecting value: line 126 column 19 (char 6196)"
- Chunk 2 (840 tokens): ✓ SUCCESS - 24 items

**Run 2 (retry):**
- Chunk 1 (1,933 tokens): "Unterminated string starting at: line 217 column 18 (char 10325)"
- Chunk 2 (840 tokens): "Expecting value: line 118 column 19 (char 5510)"

**Run 3 (focused extraction):**
- Chunk 1 (1,933 tokens): ✓ SUCCESS - 25 items
- Chunk 2 (840 tokens): "Expecting value: line 118 column 19 (char 5510)"

### Analysis
- **Failure rate:** 50-67% of chunks across 3 runs
- **Pattern:** Smaller chunk (840 tokens) fails consistently in runs 2-3
- **Errors:** Unterminated strings, unexpected characters, malformed JSON structure
- **Root cause:** LLM generates syntactically invalid JSON (unescaped quotes, truncated output, or formatting errors)

### Impact
- **Extraction reliability:** UNRELIABLE - Cannot guarantee successful extraction
- **Data loss:** ~40% of source units (chunk 2) not extracted
- **Production readiness:** **NOT READY** - Silent failures or partial extractions unacceptable

---

## 4. Provenance Quality (Partial - Chunk 1 Only)

### Method
Check all 25 extracted items' source_unit_ids against valid source IDs from input sample.

### Results
- **Total source references:** 25 (1 per item)
- **Valid references:** 25 (100%)
- **Invalid references:** 0

**Distribution:**
- S0012: 5 references
- S0013: 9 references
- S0016: 4 references
- S0017: 1 reference
- S0020: 3 references
- S0022: 2 references
- S0024: 1 reference

**Verdict:** ✓ Provenance tracking remains perfect for successfully extracted items.

---

## 5. Duplicate Detection (Partial - Chunk 1 Only)

### Exact Duplicates
**Method:** Group by exact content (case-insensitive, whitespace-normalized)  
**Result:** 0 exact duplicates

### Semantic Near-Duplicates
**Method:** Group by knowledge type + first 50 chars of content

**Analysis pending** - Cannot assess near-duplicates without full downstream pipeline (analysis, representation, assembly completed).

**Note:** With only 25 items from incomplete extraction, near-duplicate assessment would be misleading. Need full successful extraction first.

---

## 6. Downstream Stages - NOT COMPLETED

Due to JSON parsing failures and time constraints, the following stages were NOT completed for this validation:
- ❌ Content Analysis
- ❌ Representation Selection
- ❌ Assembly
- ❌ Rendering
- ❌ Evaluation
- ❌ Semantic Verification

**Reason:** Focused on diagnosing and documenting the critical JSON parsing issue that blocks scalability.

---

## 7. Quality Observations (Limited Scope)

### Extraction Granularity
Cannot assess granularity with only 1.4 items/unit across incomplete sample. For comparison:
- 5-unit validation: 6.2 items/unit
- 18-unit validation (partial): 1.4 items/unit (misleading due to failure)
- 18-unit validation (chunk 1 only): ~2.3 items/unit

**Assessment:** Insufficient data. Need successful full extraction.

### Unsupported Details
Cannot assess without semantic verification stage.

### OCR Artifacts
Same corrupted heading observed: "I S I S I S I Sell my Dreams ell my Dreams ell my Dreams ell my Dreams"

**Impact:** Section attribution remains unreliable.

---

## 8. Stop Criteria Assessment

| Criterion | Threshold | Actual | Status |
|-----------|-----------|--------|--------|
| Extraction rate | <12 items/unit | 1.4 items/unit | ⚠️ MISLEADING (incomplete) |
| Near-duplicates | <30% | Cannot assess | ⚠️ INCOMPLETE |
| Invalid provenance | 0% | 0% | ✓ PASS |
| Unsupported claims | <10% | Cannot assess | ⚠️ INCOMPLETE |

**Primary Stop Criterion Triggered:** **JSON parsing failure rate >50%**

---

## 9. Errors and Unresolved Limitations

###Critical Production Blocker
**Issue:** Intermittent JSON parsing failures from Groq `openai/gpt-oss-120b`  
**Frequency:** 50-67% of chunks  
**Impact:** Unreliable extraction, data loss, silent failures possible

**Root Causes (Hypotheses):**
1. LLM generates unescaped quotes in JSON strings (e.g., dialogue with nested quotes)
2. LLM truncates response mid-JSON structure
3. LLM inserts newlines or special characters breaking JSON syntax
4. Token limit causes premature termination

**Mitigation Attempts:**
- ❌ Retry: Failures persist across multiple runs
- ❌ Smaller chunks: 840-token chunk also fails
- ⚠️ Prompt engineering: Not attempted (may help)
- ⚠️ Response validation: Could add LLM retry logic

### Known Limitations (from 5-unit validation)
1. **OCR artifacts:** Corrupted section headings
2. **Verifier false positives:** Imperative verbs in procedures flagged as entity mismatches
3. **Near-duplicate risk:** 19% in 5-unit sample

---

## 10. Costs and Performance

### API Usage
- **Successful chunk:** 1,933 tokens → 25 items in ~8-10 seconds
- **Failed chunks:** 840-1,933 tokens → 0 items in ~7-9 seconds (wasted)
- **Total time (3 runs):** ~88 seconds (46s + 25s + 17s)
- **Total successful items:** 25
- **Total API calls:** 6 chunks attempted, 2-3 successful

**Cost Efficiency:** LOW - Multiple failures waste API credits and time.

**Note:** Groq does not provide token usage in API responses. Estimated tokens based on chunker calculation.

---

## 11. Go/No-Go Recommendation

### Recommendation: **NO-GO** ❌

**Do NOT proceed to larger validation (full document or production deployment) until JSON parsing issue is resolved.**

### Justification

| Factor | Status | Rationale |
|--------|--------|-----------|
| **Extraction reliability** | ❌ FAIL | 50-67% chunk failure rate |
| **Data completeness** | ❌ FAIL | 40% of source units not extracted |
| **Silent failures** | ⚠️ RISK | Partial extractions may appear successful |
| **Provenance (partial)** | ✓ PASS | 100% valid for extracted items |
| **Production readiness** | ❌ FAIL | Unreliable pipeline cannot be deployed |

### Blocking Issues
1. **Critical:** JSON parsing failures (50-67% rate)
2. **Major:** Incomplete extraction prevents quality assessment
3. **Major:** Cannot verify semantic faithfulness without full pipeline

---

## 12. Required Actions Before Next Validation

### Immediate (Blocking)
1. **Diagnose JSON parsing failures**
   - Inspect raw LLM responses from failed chunks
   - Identify specific malformed JSON patterns
   - Determine if issue is in LLM output or parsing logic

2. **Implement mitigation**
   - Add JSON repair logic (e.g., escape unescaped quotes)
   - Add retry with exponential backoff
   - Consider streaming response validation
   - Test prompt modifications to encourage valid JSON

3. **Validate fix**
   - Rerun 18-unit extraction with mitigations
   - Verify 0% JSON parsing failure rate
   - Confirm all 18 units successfully extracted

### Secondary (Quality)
4. **Complete downstream pipeline**
   - Run analysis, representation, assembly, rendering
   - Generate semantic verification report
   - Assess near-duplicates and granularity

5. **Manual spot-check**
   - Review 10% of claims for factual accuracy
   - Verify no new issues introduced at scale

### Only After Success
6. **Proceed to next milestone:** Full document extraction (109 units)

---

## 13. Alternative Approaches

If JSON parsing issues persist:

### Option A: Switch LLM Provider
- Try different Groq model (e.g., `llama-3.1-70b-versatile`)
- Try OpenAI `gpt-4o-mini` or `gpt-3.5-turbo`
- Compare reliability across providers

### Option B: Reduce Chunk Size
- Current: 1,933 tokens (max)
- Try: 1,000 tokens or 500 tokens
- Trade-off: More API calls, higher cost, but higher reliability

### Option C: Add JSON Repair
- Use `json_repair` library to fix common malformations
- Add validation + retry loop (max 3 attempts)
- Log all repair actions for monitoring

### Option D: Change Output Format
- Request simpler JSON structure (fewer nested objects)
- Use line-delimited JSON (one item per line)
- Parse incrementally instead of full document

---

## 14. Lessons Learned

### What Worked
- ✓ Sample selection methodology (18 representative units)
- ✓ Provenance tracking (100% valid for extracted items)
- ✓ Error visibility (failures logged clearly)

### What Failed
- ✗ LLM JSON generation reliability
- ✗ Assumption that 5-unit success would scale to 18 units
- ✗ No retry or error recovery logic

### What's Unclear
- ? Exact cause of JSON malformation (need raw response inspection)
- ? Whether issue is model-specific or prompt-specific
- ? Optimal chunk size for reliability vs. efficiency

---

## 15. Conclusion

The 15-20 unit validation **failed to complete** due to critical JSON parsing failures affecting 50-67% of extraction chunks. While provenance tracking remains perfect for successfully extracted items (25/25), the unreliable extraction pipeline is **not production-ready**.

**Next Steps:**
1. Diagnose and fix JSON parsing failures
2. Rerun 18-unit validation with mitigations
3. Only proceed to full-document extraction after achieving 0% failure rate

**Current Status:** **BLOCKED** - Cannot recommend production deployment or larger validation until extraction reliability is resolved.
