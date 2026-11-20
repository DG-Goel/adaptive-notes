# Content Support Matrix

## Extraction Layer Content Handling

This document explicitly defines what content types ARE and ARE NOT semantically extracted by the Knowledge Extraction layer.

---

## ✅ Supported Content (Semantically Extracted)

Content types that ARE sent to the LLM and CAN be semantically extracted:

### Text Content
- **Paragraphs** - Full semantic extraction
- **Headings** - Used for section context
- **Lists** (with text representation) - Full extraction
- **Tables** (with text/markdown representation) - Full extraction
- **Formulas** (with LaTeX/text representation) - Full extraction if text provided
- **Captions** - Full extraction

**Key Point:** Any source unit with a non-null `text` field is included in chunk text_content and visible to the LLM.

---

## ❌ NOT Supported (NOT Semantically Extracted)

Content types that are tracked for provenance but NOT sent to LLM:

### Visual Content
- **Pictures** (type=picture, text=null)
  - Source ID: ✅ Tracked in source_units
  - Bounding box: ✅ Preserved in SourceUnit
  - Text content: ❌ Not sent to LLM
  - Semantic extraction: ❌ NO
  - Can LLM reference it?: ❌ NO (shouldn't cite picture IDs)

### Mathematical Content
- **Formulas** (without text representation)
  - If formula has text/LaTeX: ✅ Extracted
  - If formula has no text: ❌ Not sent to LLM

### Embedded Objects
- **Charts/Graphs** (rendered as pictures)
  - ❌ Not sent to LLM
  - ❌ No semantic extraction

---

## Provenance vs. Semantic Extraction

**CRITICAL DISTINCTION:**

### Provenance Tracking (What We Track)
ALL content units are tracked in:
- `ExtractionChunk.source_units` - List of all source IDs in chunk
- Validation checks - Ensure cited IDs exist

This allows us to:
- Validate that cited sources exist in the document
- Maintain complete document structure
- Support future visual extraction features

### Semantic Extraction (What LLM Sees)
ONLY text units are included in:
- `ExtractionChunk.text_content` - String sent to LLM
- LLM prompt input

This means:
- LLM cannot extract from pictures
- LLM should not cite picture source IDs
- We do NOT claim to have semantically processed visual content

---

## Example: Mixed Content Chunk

### Input SourceUnits:
```
S0001: type=paragraph, text="Figure 1 shows the process flow."
S0002: type=picture, text=null, docling_ref="#/pictures/0"
S0003: type=paragraph, text="The first step involves data collection."
```

### Chunk Created:
```python
ExtractionChunk(
    chunk_id="DOC_CHUNK_000",
    source_units=["S0001", "S0002", "S0003"],  # All tracked
    text_content="""
        [S0001] Figure 1 shows the process flow.
        [S0003] The first step involves data collection.
    """  # S0002 omitted - no text
)
```

### What LLM Sees:
```
[S0001] Figure 1 shows the process flow.
[S0003] The first step involves data collection.
```

### What LLM Cannot Do:
- ❌ Extract knowledge from the picture
- ❌ Know what Figure 1 contains
- ❌ Reference S0002 in source_unit_ids
- ❌ Describe the process flow diagram

### What LLM Can Do:
- ✅ Extract that "Figure 1 shows the process flow" (from S0001 text)
- ✅ Extract that "The first step involves data collection" (from S0003)
- ✅ Create relationships between textual concepts

---

## Validation Behavior

### Source ID Validation
When LLM returns `source_unit_ids: ["S0001", "S0002"]`:

1. **Check S0001:** 
   - Exists in source document? ✅
   - Has text content? ✅
   - Keep in final knowledge item? ✅

2. **Check S0002 (picture with no text):**
   - Exists in source document? ✅
   - Has text content? ❌
   - Was visible to LLM? ❌
   - **VALIDATION DECISION:** ⚠️ Filter out with warning
   
**Rationale:** The LLM should not cite content it never saw. If it cites S0002, it's either:
- Hallucinating
- Guessing based on context
- An error in our prompt design

We filter invalid IDs but DO NOT claim semantic extraction happened.

---

## Future Enhancements

To support visual content extraction:

1. **Add Placeholders:** Include markers in text_content:
   ```
   [S0001] Figure 1 shows the process flow.
   [S0002] [PICTURE: type=diagram, page=5]
   [S0003] The first step involves data collection.
   ```

2. **Visual Extraction Pipeline:** Separate pass for pictures:
   - Send image to vision model
   - Extract visual knowledge with separate schema
   - Link to surrounding text context

3. **Multi-Modal Extraction:** Single pass with vision-capable model:
   - Send text + images together
   - Allow LLM to reference both text and visual IDs

**Current Status:** NOT IMPLEMENTED - text-only extraction

---

## Testing

See `tests/test_extraction_unit.py`:
- `test_chunker_retains_non_text_source_ids_but_not_content` - Documents current behavior
- `test_chunker_text_content_excludes_metadata` - Verifies clean text input
- `test_extractor_invalid_source_ids` - Validates filtering behavior

---

## Summary

| Content Type | Tracked | Sent to LLM | Semantically Extracted |
|--------------|---------|-------------|------------------------|
| Text (paragraph, heading) | ✅ | ✅ | ✅ |
| Table (with text) | ✅ | ✅ | ✅ |
| Formula (with text) | ✅ | ✅ | ✅ |
| Picture (no text) | ✅ | ❌ | ❌ |
| Chart (no text) | ✅ | ❌ | ❌ |
| Formula (no text) | ✅ | ❌ | ❌ |

**Key Principle:** We track everything for provenance, but only extract from what the LLM actually sees.
