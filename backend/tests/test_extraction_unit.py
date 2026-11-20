"""
Unit tests for knowledge extraction layer.

Tests all components independently with deterministic inputs.
"""

import json
from typing import List

from app.models.source import SourceDocument, SourceUnit, BoundingBox
from app.models.knowledge import (
    KnowledgeDocument,
    Concept,
    Definition,
    Explanation
)
from app.extraction.llm_provider import MockLLMProvider
from app.extraction.chunker import ContentChunker
from app.extraction.extractor import KnowledgeExtractor


# ============================================================================
# Fixtures
# ============================================================================

def create_test_source_units() -> List[SourceUnit]:
    """Create test source units with known IDs"""
    return [
        SourceUnit(
            source_id="S0001",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="Short stories are prose narratives.",
            position=1,
            page=1,
            bbox=BoundingBox(left=0, top=0, right=100, bottom=50)
        ),
        SourceUnit(
            source_id="S0002",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="They typically range from 1,000 to 20,000 words.",
            position=2,
            page=1
        ),
        SourceUnit(
            source_id="S0003",
            document_id="TEST",
            type="heading",
            content_role="structural",
            text="Introduction",
            position=3,
            page=2,
            section="Introduction"
        ),
        SourceUnit(
            source_id="S0004",
            document_id="TEST",
            type="paragraph",
            content_role="furniture",
            text="Page 1",
            position=4,
            page=1
        ),
        SourceUnit(
            source_id="S0005",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="The plot is central to short stories.",
            position=5,
            page=2,
            section="Introduction"
        ),
    ]


def create_test_source_document() -> SourceDocument:
    """Create a minimal source document for extraction tests (single chunk)"""
    from app.models.source import SourceDocument
    
    return SourceDocument(
        document_id="TEST_DOC",
        filename="test.pdf",
        page_count=1,
        source_units=[
            SourceUnit(
                source_id="S0001",
                document_id="TEST_DOC",
                type="paragraph",
                content_role="content",
                text="Short stories are prose narratives.",
                position=1,
                page=1
            ),
            SourceUnit(
                source_id="S0002",
                document_id="TEST_DOC",
                type="paragraph",
                content_role="content",
                text="They typically range from 1,000 to 20,000 words.",
                position=2,
                page=1
            ),
        ]
    )


# ============================================================================
# Test: MockLLMProvider
# ============================================================================

def test_mock_provider_default_response():
    """Test mock provider returns default empty response"""
    provider = MockLLMProvider()
    response = provider.generate("test prompt")
    
    data = json.loads(response)
    assert "concepts" in data
    assert "definitions" in data
    assert len(data["concepts"]) == 0
    assert provider.call_count == 1


def test_mock_provider_matched_response():
    """Test mock provider returns matched response"""
    responses = {
        "CHUNK_000": '{"concepts": [{"concept_name": "test"}]}'
    }
    provider = MockLLMProvider(responses=responses)
    
    response = provider.generate("Process CHUNK_000")
    data = json.loads(response)
    
    assert len(data["concepts"]) == 1
    assert data["concepts"][0]["concept_name"] == "test"


def test_mock_provider_call_tracking():
    """Test mock provider tracks calls correctly"""
    provider = MockLLMProvider()
    
    assert provider.call_count == 0
    provider.generate("first")
    assert provider.call_count == 1
    provider.generate("second")
    assert provider.call_count == 2
    
    provider.reset()
    assert provider.call_count == 0


# ============================================================================
# Test: ContentChunker
# ============================================================================

def test_chunker_retains_unreviewed_furniture_units():
    """Layout labels cannot authorize exclusion under the source policy."""
    units = create_test_source_units()
    chunker = ContentChunker()
    
    chunks = chunker.chunk(units, "TEST")
    
    # All units remain until an explicit whole-unit noneducational review.
    all_source_ids = []
    for chunk in chunks:
        all_source_ids.extend(chunk.source_units)
    
    assert "S0001" in all_source_ids
    assert "S0002" in all_source_ids
    assert "S0003" in all_source_ids
    assert "S0004" in all_source_ids  # Furniture alone is not an exclusion
    assert "S0005" in all_source_ids


def test_chunker_preserves_source_markers():
    """Test chunker adds source markers to text"""
    units = create_test_source_units()
    chunker = ContentChunker()
    
    chunks = chunker.chunk(units, "TEST")
    
    # First chunk should contain [S0001] markers
    assert "[S0001]" in chunks[0].text_content
    assert "[S0002]" in chunks[0].text_content


def test_chunker_splits_on_section():
    """Test chunker creates new chunk when section changes"""
    units = create_test_source_units()
    chunker = ContentChunker()
    
    chunks = chunker.chunk(units, "TEST")
    
    # Should have at least 2 chunks (section changes at S0003)
    assert len(chunks) >= 2


def test_chunker_respects_size_limit():
    """Test chunker splits chunks exceeding size limit"""
    # Create units with lots of text
    units = []
    for i in range(10):
        units.append(SourceUnit(
            source_id=f"S{i:04d}",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="x" * 1000,  # 1000 chars each
            position=i+1,
            page=1
        ))
    
    chunker = ContentChunker(max_tokens_per_chunk=500)  # ~2000 chars max
    chunks = chunker.chunk(units, "TEST")
    
    # Should split into multiple chunks
    assert len(chunks) > 1


def test_chunker_empty_input():
    """Test chunker handles empty input"""
    chunker = ContentChunker()
    chunks = chunker.chunk([], "TEST")
    
    assert len(chunks) == 0


# ============================================================================
# Test: KnowledgeExtractor - Valid Responses
# ============================================================================

def test_extractor_valid_response():
    """Test extractor with valid JSON response"""
    doc = create_test_source_document()
    
    valid_response = json.dumps({
        "concepts": [{
            "concept_name": "short story",
            "aliases": ["narrative"],
            "content": "A literary form",
            "source_unit_ids": ["S0001"]
        }],
        "definitions": [{
            "term": "short story",
            "definition_text": "A prose narrative",
            "content": "A prose narrative",
            "source_unit_ids": ["S0001"]
        }],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=valid_response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    assert result.total_items == 2
    assert len(result.concepts) == 1
    assert len(result.definitions) == 1
    assert result.concepts[0].concept_name == "short story"
    assert result.concepts[0].source_unit_ids == ["S0001"]


def test_extractor_empty_response():
    """Test extractor with empty but valid response"""
    doc = create_test_source_document()
    
    empty_response = json.dumps({
        "concepts": [],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=empty_response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    assert result.total_items == 0
    assert len(result.concepts) == 0


def test_extractor_multiple_types():
    """Test extractor with multiple knowledge types"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "concept1",
            "content": "test",
            "source_unit_ids": ["S0001"]
        }],
        "definitions": [{
            "term": "term1",
            "definition_text": "def1",
            "content": "def1",
            "source_unit_ids": ["S0002"]
        }],
        "explanations": [{
            "topic": "topic1",
            "explanation_text": "exp1",
            "content": "exp1",
            "source_unit_ids": ["S0001", "S0002"]
        }],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    assert result.total_items == 3
    assert len(result.concepts) == 1
    assert len(result.definitions) == 1
    assert len(result.explanations) == 1


# ============================================================================
# Test: KnowledgeExtractor - Error Handling
# ============================================================================

def test_extractor_malformed_json():
    """Test extractor handles malformed JSON"""
    doc = create_test_source_document()
    
    malformed_response = "{ invalid json"
    provider = MockLLMProvider(default_response=malformed_response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    # Should not crash, but produce empty result
    result = extractor.extract(doc)
    
    # All chunks failed, so no items
    assert result.total_items == 0


def test_extractor_missing_required_fields():
    """Test extractor handles missing required fields gracefully"""
    doc = create_test_source_document()
    
    # Response missing 'content' and 'source_unit_ids'
    response = json.dumps({
        "concepts": [{
            "concept_name": "test"
            # Missing: content, source_unit_ids
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Should create item with empty defaults
    assert len(result.concepts) == 1
    assert result.concepts[0].source_unit_ids == []  # Empty list
    assert result.concepts[0].content == "test"  # Falls back to concept_name


def test_extractor_invalid_source_ids():
    """Test extractor filters out invalid source IDs"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "test",
            "content": "test",
            "source_unit_ids": ["INVALID_ID", "S0001", "S0999"]  # Only S0001 is valid
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Validation should filter out invalid IDs, keeping only S0001
    assert len(result.concepts) == 1
    assert result.concepts[0].source_unit_ids == ["S0001"]
    assert extractor.invalid_refs_count == 2


# ============================================================================
# Test: Knowledge ID Generation
# ============================================================================

def test_knowledge_id_uniqueness():
    """Test that knowledge IDs are unique"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [
            {"concept_name": "c1", "content": "c1", "source_unit_ids": ["S0001"]},
            {"concept_name": "c2", "content": "c2", "source_unit_ids": ["S0002"]},
        ],
        "definitions": [
            {"term": "d1", "definition_text": "d1", "content": "d1", "source_unit_ids": ["S0001"]},
        ],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    all_ids = [item.knowledge_id for item in result.get_all_items()]
    
    # All IDs should be unique
    assert len(all_ids) == len(set(all_ids))
    
    # IDs should have correct prefixes
    assert result.concepts[0].knowledge_id.startswith("CON_")
    assert result.concepts[1].knowledge_id.startswith("CON_")
    assert result.definitions[0].knowledge_id.startswith("DEF_")


# ============================================================================
# Test: Source Traceability
# ============================================================================

def test_source_traceability_preserved():
    """Test that source_unit_ids are preserved through extraction"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "test",
            "content": "test",
            "source_unit_ids": ["S0001", "S0002"]
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    concept = result.concepts[0]
    assert concept.source_unit_ids == ["S0001", "S0002"]
    assert concept.document_id == "TEST_DOC"
    
    # Page range should be from chunks
    assert concept.page_range is not None


def test_source_traceability_all_invalid_ids_filtered():
    """
    Test that item with ALL invalid source IDs is created but with empty source list.
    
    This is important: we do not silently create "grounded" knowledge from hallucinated sources.
    The item exists but its source_unit_ids will be empty, making it clear it's not grounded.
    """
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "hallucinated concept",
            "content": "This concept doesn't exist in source",
            "source_unit_ids": ["S9999", "S8888", "FAKE_ID"]  # None valid
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Item is created but has NO source grounding
    assert len(result.concepts) == 1
    assert result.concepts[0].source_unit_ids == []  # All filtered out
    assert extractor.invalid_refs_count == 3  # All 3 were invalid


def test_source_traceability_partial_validation():
    """Test that mix of valid and invalid IDs are filtered correctly"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "partially grounded",
            "content": "test",
            "source_unit_ids": ["S0001", "INVALID", "S0002", "FAKE"]
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Valid IDs preserved, invalid filtered
    assert result.concepts[0].source_unit_ids == ["S0001", "S0002"]
    assert extractor.invalid_refs_count == 2


def test_source_traceability_empty_list_allowed():
    """Test that empty source_unit_ids list is allowed (though not ideal)"""
    doc = create_test_source_document()
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "ungrounded",
            "content": "test",
            "source_unit_ids": []  # Empty - LLM didn't cite sources
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Item created with empty sources (validation cannot filter non-existent IDs)
    assert len(result.concepts) == 1
    assert result.concepts[0].source_unit_ids == []
    assert extractor.invalid_refs_count == 0  # No invalid IDs, just empty


def test_source_traceability_validates_against_document():
    """Test that validation uses actual document source IDs, not chunk IDs"""
    from app.models.source import SourceDocument
    
    # Document with specific IDs
    doc = SourceDocument(
        document_id="VALIDATE_TEST",
        filename="test.pdf",
        page_count=1,
        source_units=[
            SourceUnit(
                source_id="VALID_001",
                document_id="VALIDATE_TEST",
                type="paragraph",
                content_role="content",
                text="Valid content",
                position=1,
                page=1
            ),
        ]
    )
    
    response = json.dumps({
        "concepts": [{
            "concept_name": "test",
            "content": "test",
            "source_unit_ids": ["VALID_001", "S0001"]  # S0001 not in this document
        }],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    provider = MockLLMProvider(default_response=response)
    extractor = KnowledgeExtractor(provider, verbose=False)
    
    result = extractor.extract(doc)
    
    # Only VALID_001 is kept
    assert result.concepts[0].source_unit_ids == ["VALID_001"]
    assert extractor.invalid_refs_count == 1  # S0001 was invalid for this document


# ============================================================================
# Test: Chunking Limitations (known issues)
# ============================================================================

def test_chunker_retains_non_text_source_ids_but_not_content():
    """
    Non-text units (pictures, formulas) are tracked but invisible to LLM.
    
    Units without text ARE included in chunk.source_units for provenance tracking,
    but they have NO representation in chunk.text_content that goes to the LLM.
    
    This means:
    - Source IDs are preserved for citation validation
    - LLM cannot see or reference the non-text content
    - LLM cannot extract knowledge from visual elements
    - No semantic extraction happens for pictures/formulas/charts
    
    IMPORTANT: The LLM is NOT told it has inspected these elements.
    The reference exists only for validation - if LLM somehow produces
    a source_unit_id for a picture, we can verify it exists, but we do NOT
    claim the LLM has semantically processed the image.
    """
    from app.models.source import SourceUnit, BoundingBox
    
    units = [
        SourceUnit(
            source_id="S0001",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="Text before picture",
            position=1,
            page=1
        ),
        SourceUnit(
            source_id="S0002",
            document_id="TEST",
            type="picture",
            content_role="content",
            text=None,  # No OCR text
            position=2,
            page=1,
            bbox=BoundingBox(left=0, top=0, right=100, bottom=50),
            docling_ref="#/pictures/0"
        ),
        SourceUnit(
            source_id="S0003",
            document_id="TEST",
            type="paragraph",
            content_role="content",
            text="Text after picture",
            position=3,
            page=1
        ),
    ]
    
    chunker = ContentChunker()
    chunks = chunker.chunk(units, "TEST")
    
    # Picture IS tracked in source_units list
    assert len(chunks) == 1
    assert "S0001" in chunks[0].source_units
    assert "S0002" in chunks[0].source_units  # Source ID tracked
    assert "S0003" in chunks[0].source_units
    
    # BUG: But picture has no representation in text_content sent to LLM
    assert "[S0002]" not in chunks[0].text_content  # No placeholder for picture
    # The LLM won't know there's a picture between S0001 and S0003


def test_chunker_text_content_excludes_metadata():
    """
    Text content sent to LLM excludes structural metadata.
    
    The text_content string contains only the text from source units,
    prefixed with source markers like [S0001]. It does NOT include:
    - Unit type (paragraph, table, heading)
    - Bounding box coordinates
    - Docling references
    - Content role classifications
    
    This is by design - the LLM sees clean text for extraction,
    not JSON-like metadata that would confuse the extraction prompt.
    """
    from app.models.source import SourceUnit, BoundingBox
    
    units = [
        SourceUnit(
            source_id="S0001",
            document_id="TEST",
            type="table",
            content_role="content",
            text="Column A | Column B\nValue 1 | Value 2",
            position=1,
            page=1,
            bbox=BoundingBox(left=0, top=0, right=200, bottom=100),
            docling_ref="#/tables/0"
        ),
    ]
    
    chunker = ContentChunker()
    chunks = chunker.chunk(units, "TEST")
    
    # Source unit is tracked
    assert "S0001" in chunks[0].source_units
    
    # But text_content only has the text, no metadata about it being a table
    assert "table" not in chunks[0].text_content.lower()
    assert "[S0001]" in chunks[0].text_content
    assert "Column A" in chunks[0].text_content


# ============================================================================
# Test: Regression - Empty Chunk Handling
# ============================================================================

def test_empty_chunks_do_not_corrupt_extraction():
    """
    Regression test: Verify that chunks returning empty extraction results
    do not corrupt, duplicate, or remove knowledge from other chunks.
    
    This tests the end-to-end behavior where some chunks may have content
    but the LLM returns empty results, while other chunks have valid extractions.
    """
    from app.models.source import SourceDocument
    
    # Create document with 3 units that will be in separate chunks
    doc = SourceDocument(
        document_id="REGRESSION_TEST",
        filename="test.pdf",
        page_count=1,
        source_units=[
            SourceUnit(
                source_id="R0001",
                document_id="REGRESSION_TEST",
                type="paragraph",
                content_role="content",
                text="First content",
                position=1,
                page=1
            ),
            SourceUnit(
                source_id="R0002",
                document_id="REGRESSION_TEST",
                type="heading",
                content_role="structural",
                text="Section Break",
                position=2,
                page=1,
                section="Section 1"
            ),
            SourceUnit(
                source_id="R0003",
                document_id="REGRESSION_TEST",
                type="paragraph",
                content_role="content",
                text="Second content",
                position=3,
                page=1,
                section="Section 1"
            ),
        ]
    )
    
    # Mock provider with responses for specific chunks
    # Chunk 0 gets a valid response, Chunk 1 gets empty response
    provider = MockLLMProvider(
        responses={
            "CHUNK_000": json.dumps({
                "concepts": [{
                    "concept_name": "chunk 0 concept",
                    "content": "from first chunk",
                    "source_unit_ids": ["R0001"]
                }],
                "definitions": [],
                "explanations": [],
                "examples": [],
                "facts": [],
                "formulas": [],
                "procedures": [],
                "relationships": []
            }),
        },
        default_response=json.dumps({
            "concepts": [],
            "definitions": [],
            "explanations": [],
            "examples": [],
            "facts": [],
            "formulas": [],
            "procedures": [],
            "relationships": []
        })
    )
    
    extractor = KnowledgeExtractor(provider, verbose=False)
    result = extractor.extract(doc)
    
    # Verify exactly 1 concept (not 0, not duplicated)
    assert result.total_items == 1, f"Expected 1 item, got {result.total_items}"
    assert len(result.concepts) == 1, f"Expected 1 concept, got {len(result.concepts)}"
    
    # Verify it's the correct concept
    concept = result.concepts[0]
    assert concept.concept_name == "chunk 0 concept"
    assert concept.source_unit_ids == ["R0001"]
    
    # Verify no other types were added
    assert len(result.definitions) == 0
    assert len(result.explanations) == 0
    assert len(result.examples) == 0
    assert len(result.facts) == 0
    assert len(result.relationships) == 0
    
    # Verify knowledge IDs are unique
    all_ids = [item.knowledge_id for item in result.get_all_items()]
    assert len(all_ids) == len(set(all_ids)), "Duplicate knowledge IDs found"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("Running extraction unit tests...")
    print("=" * 80)
    
    # Run all test functions
    test_functions = [
        # Mock provider
        test_mock_provider_default_response,
        test_mock_provider_matched_response,
        test_mock_provider_call_tracking,
        
        # Chunker
        test_chunker_filters_content_units,
        test_chunker_preserves_source_markers,
        test_chunker_splits_on_section,
        test_chunker_respects_size_limit,
        test_chunker_empty_input,
        
        # Extractor - valid responses
        test_extractor_valid_response,
        test_extractor_empty_response,
        test_extractor_multiple_types,
        
        # Extractor - error handling
        test_extractor_malformed_json,
        test_extractor_missing_required_fields,
        test_extractor_invalid_source_ids,
        
        # Knowledge IDs
        test_knowledge_id_uniqueness,
        
        # Traceability
        test_source_traceability_preserved,
        test_source_traceability_all_invalid_ids_filtered,
        test_source_traceability_partial_validation,
        test_source_traceability_empty_list_allowed,
        test_source_traceability_validates_against_document,
        
        # Chunking limitations
        test_chunker_retains_non_text_source_ids_but_not_content,
        test_chunker_text_content_excludes_metadata,
        
        # Regression tests
        test_empty_chunks_do_not_corrupt_extraction,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"[PASS] {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {str(e) or '(assertion failed)'}")
            failed += 1
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[FAILURE] {failed} test(s) failed")
        exit(1)


def test_legacy_evidence_disabled_preserves_missing_field_defaults():
    """New evidence checks must not change the existing permissive default mode."""
    provider = MockLLMProvider(default_response=json.dumps({
        "concepts": [{"concept_name": "test"}],
    }))
    extractor = KnowledgeExtractor(provider, verbose=False)
    result = extractor.extract(create_test_source_document())
    assert len(result.concepts) == 1
    assert result.concepts[0].content == "test"
    assert result.concepts[0].source_unit_ids == []
    assert result.concepts[0].extraction_metadata is None
    assert extractor.strict_evidence is False



def test_legacy_all_categories_keep_constructor_defaults_and_explicit_empty_content():
    """Strict raw-contract checks must not alter the established legacy defaults."""
    from app.models.knowledge import ExtractionChunk
    cases = {
        "concepts": {"concept_name": "x"},
        "definitions": {"term": "x", "definition_text": "x"},
        "explanations": {"topic": "x", "explanation_text": "x"},
        "examples": {"exemplifies": "x", "example_text": "x"},
        "facts": {"fact_text": "x"},
        "formulas": {"formula_text": "x"},
        "procedures": {"procedure_name": "x", "steps": ["x"]},
        "relationships": {"relationship_type": "x", "subject": "x", "object": "x"},
    }
    extractor = KnowledgeExtractor(MockLLMProvider(), verbose=False)
    chunk = ExtractionChunk(chunk_id="JAVA_CHUNK_000", source_units=["T0022"],
                            text_content="[T0022] x")
    extractor.valid_source_ids = {"T0022"}
    for category, specific in cases.items():
        row = {**specific, "source_unit_ids": ["T0022"]}
        item = extractor._parse_response(json.dumps({category: [row]}), chunk, "JAVA")[0]
        assert item.content == ("" if category == "relationships" else "x")
        assert item.source_unit_ids == ["T0022"]
        assert item.extraction_metadata is None
        row["content"] = ""
        item = extractor._parse_response(json.dumps({category: [row]}), chunk, "JAVA")[0]
        assert item.content == ""
    assert extractor.strict_evidence is False


def test_root_and_split_child_requests_use_actual_canonical_allowlists():
    """Mock-only request assembly; no real provider, extraction job or semantic claim."""
    from unittest.mock import Mock
    from app.extraction.prompts import build_extraction_prompt, EXTRACTION_SYSTEM_PROMPT
    units = [SourceUnit(source_id=sid, document_id="JAVA", type="paragraph",
                        content_role="content", text=text, position=index)
             for index, (sid, text) in enumerate([
                 ("T0022", "First supplied unit."), ("T0023", "Second supplied unit.")], 22)]
    provider = MockLLMProvider()
    provider.generate = Mock(return_value='{"concepts": []}')
    extractor = KnowledgeExtractor(provider, verbose=False, strict_evidence=True)
    root = extractor.chunker.chunk(units, "JAVA")[0]
    children = extractor.splitter.split_chunk(root, units, num_splits=2)
    assert len(children) == 2
    assert root.chunk_id == "JAVA_CHUNK_000"
    assert root.source_units == ["T0022", "T0023"]
    for chunk in [root, *children]:
        extractor._extract_from_chunk(chunk, "JAVA")
        call = provider.generate.call_args.kwargs
        expected = build_extraction_prompt(chunk.text_content, chunk.chunk_id,
                                           allowed_source_ids=chunk.source_units)
        assert call["prompt"] == expected
        assert call["system"] == EXTRACTION_SYSTEM_PROMPT
        assert call["temperature"] == 0.0
        assert call["max_tokens"] == extractor.token_budget.calculate_budget(
            expected, system_text=EXTRACTION_SYSTEM_PROMPT).max_output_tokens
        assert "SCHEDULING ID (never cite): " + chunk.chunk_id in expected
        assert "ALLOWED CANONICAL SOURCE IDs: " + json.dumps(chunk.source_units) in expected
        assert chunk.text_content in expected
    assert provider.generate.call_count == 3  # One mock invocation per deliberately assembled request.
    assert children[0].source_units == ["T0022"]
    assert children[1].source_units == ["T0023"]


def test_prompt_optional_allowlist_preserves_older_call_signature():
    from app.extraction.prompts import build_extraction_prompt
    text = "[T0022] Exact supplied text."
    old_signature = build_extraction_prompt(text, "JAVA_CHUNK_000", 12)
    explicit = build_extraction_prompt(text, "JAVA_CHUNK_000", 12,
                                       allowed_source_ids=["T0022"])
    assert "up to ~12" in old_signature and "up to ~12" in explicit
    assert text in old_signature and text in explicit
    assert 'ALLOWED CANONICAL SOURCE IDs: ["T0022"]' in explicit
    assert "canonical IDs in the source markers below" in old_signature
    assert "SCHEDULING ID (never cite): JAVA_CHUNK_000" in explicit
