# Knowledge Extraction Layer - Known Limitations

**Version:** 1.0  
**Last Updated:** October 17, 2026

---

## Summary

This document explicitly lists what the Knowledge Extraction layer DOES NOT support. Read this before deploying to production.

---

## 1. Non-Text Content NOT Extracted

### What's Missing
- **Pictures** - Tracked but not semantically extracted
- **Charts/Graphs** - Invisible to LLM
- **Diagrams** - Not processed
- **Formulas** (without text representation) - Skipped

### What This Means
If your document has:
- Flow charts showing process steps
- Diagrams explaining concepts
- Graphs with data trends
- Pictures with important visual information

**The extraction will be incomplete.** Only surrounding text captions will be extracted.

### Workaround
- Ensure important visual content has text descriptions or captions
- Use OCR-processed documents where images contain text
- Plan for manual review of visual-heavy content

### Future Fix
- Implement vision model integration (GPT-4V, Claude 3 Opus, etc.)
- Add placeholder system for visual elements

---

## 2. Semantic Quality Not Guaranteed

### What's Not Tested
Our unit tests verify:
- ✅ JSON parsing works
- ✅ Source validation works
- ✅ Error handling works

Our unit tests DO NOT verify:
- ❌ Extracted concepts are accurate
- ❌ Definitions are complete
- ❌ Important content wasn't missed
- ❌ Relationships are correct

### Why
Unit tests use hand-crafted mock responses. Real LLM behavior varies and requires manual evaluation.

### Recommendation
**Before production:** Manually review extraction quality on 5-10 representative documents.

### Ongoing Monitoring
- Sample extracted knowledge periodically
- Collect user feedback
- Track validation warning rates

---

## 3. Chunking May Split Related Content

### The Issue
Documents are split into chunks for LLM processing. This may:
- Separate related paragraphs
- Split long explanations
- Break complex concepts across chunks

### Mitigation
- Source markers preserve provenance
- LLM can cite multiple chunks
- Section-aware chunking keeps related content together

### Impact
- Usually minimal for well-structured educational content
- More problematic for dense technical documents
- Relationships may be missed if split

---

## 4. Context Window Constraints

### Current Limits
- Default chunk size: ~2000 tokens
- Longer content requires multiple chunks
- Very long documents = many LLM calls = higher cost

### Implications
- Cost scales with document size
- Long documents take longer to process
- Token limits may require aggressive chunking

### Future Improvement
- Use models with longer context windows (100k+ tokens)
- Process entire documents in single pass
- Reduce chunking artifacts

---

## 5. API Costs and Rate Limits

### Not Handled
- **Cost tracking** - You must monitor your own API costs
- **Rate limiting** - No automatic retry or backoff
- **Budget controls** - No spending caps built in

### Your Responsibility
- Set up billing alerts in your LLM provider account
- Monitor usage during initial testing
- Estimate costs for your document volume

### Rough Cost Estimate (OpenAI GPT-4)
- Small document (5 pages): ~$0.10-0.50
- Medium document (20 pages): ~$0.50-2.00
- Large document (100 pages): ~$2.00-10.00

*Actual costs depend on document density, model choice, and content complexity.*

---

## 6. Source Validation Limitations

### What We Validate
- ✅ Source IDs exist in source document
- ✅ Invalid IDs are filtered
- ✅ Validation warnings are logged

### What We DON'T Validate
- ❌ LLM actually read the cited source (it may guess)
- ❌ Citation is accurate (LLM may misattribute)
- ❌ No important sources were omitted

### Why This Matters
**An LLM may cite a source without actually extracting from it.** Our validation only checks that the ID exists, not that the extraction is accurate.

### Implication
Source IDs provide **provenance tracking**, not **proof of accuracy**.

---

## 7. No Deduplication

### The Issue
If the same concept appears in multiple places:
- It may be extracted multiple times
- Slightly different wordings create duplicates
- No automatic merging of similar concepts

### Example
- Chunk 1: "Machine learning is a subset of AI"
- Chunk 2: "ML is part of artificial intelligence"
- Result: Two separate Concept items

### Workaround
Deduplication happens in later layers (Representation Selector).

---

## 8. Language Support

### Current Status
- **Tested with:** English educational content
- **Prompt language:** English
- **LLM training:** Primarily English

### Untested
- Non-English source documents
- Mixed-language documents
- Non-Latin scripts

### Recommendation
Test thoroughly with your target language before production use.

---

## 9. Domain Limitations

### Designed For
- Educational materials
- Textbooks
- Lecture notes
- Academic papers (text portions)

### May Not Work Well For
- Legal documents (different knowledge structure)
- Code documentation (needs code-aware extraction)
- Poetry/literature (not factual knowledge)
- Historical manuscripts (OCR quality issues)

---

## 10. No Quality Scoring

### Missing Feature
Extracted knowledge has no:
- Confidence scores
- Quality ratings
- Completeness indicators
- Importance rankings

### Impact
All extracted items treated equally, regardless of:
- How clear the source was
- How confident the LLM is
- How important the concept is

### Future Enhancement
Add confidence scoring system for filtering low-quality extractions.

---

## When NOT to Use This Layer

**Do not use** if you need:
1. ❌ Guaranteed perfect extraction accuracy
2. ❌ Visual content extraction (charts, diagrams)
3. ❌ Real-time/low-latency processing
4. ❌ Zero-cost solution (LLM calls cost money)
5. ❌ Sensitive content processing (data leaves your system)

**Consider alternatives** like:
- Manual knowledge curation
- Rule-based extraction for structured content
- Local LLMs for sensitive data
- Vision models for visual-heavy content

---

## Safe Usage Guidelines

### Do
- ✅ Test on sample documents first
- ✅ Review extraction quality manually
- ✅ Monitor API costs
- ✅ Provide feedback on accuracy
- ✅ Use for educational content with mostly text

### Don't
- ❌ Assume perfect accuracy
- ❌ Deploy without manual review
- ❌ Ignore validation warnings
- ❌ Use for mission-critical accuracy without verification
- ❌ Expect visual content extraction

---

## Getting Help

### If extraction quality is poor:
1. Check if content has lots of visual elements (not supported)
2. Review validation warnings (`invalid_refs_count`)
3. Manually inspect a few knowledge items
4. Adjust prompts if needed (see `app/extraction/prompts.py`)

### If costs are too high:
1. Use cheaper models (GPT-3.5 instead of GPT-4)
2. Reduce max_tokens_per_chunk
3. Process fewer documents
4. Consider batching

### If errors occur:
1. Check logs for validation warnings
2. Verify source document structure
3. Test with minimal example
4. Check API key and quotas

---

## Version History

- **v1.0** (Oct 2026): Initial documentation after audit
  - 22 unit tests passing
  - Source validation implemented
  - Non-text handling documented
  - Integration test added

---

## See Also

- `CONTENT_SUPPORT.md` - Detailed content type support matrix
- `tests/test_extraction_unit.py` - Unit test coverage
- `tests/test_extraction_integration.py` - Real LLM integration test

---

**Bottom Line:**

This layer extracts **text-based factual knowledge** from educational content with **good but not perfect accuracy**. Visual content is not extracted. Manual quality review is required before production use.
