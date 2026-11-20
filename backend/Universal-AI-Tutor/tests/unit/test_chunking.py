"""
Unit tests for ChunkingService.

Tests hierarchical chunking, contextual enrichment, and structure preservation.
"""

import pytest
from llama_index.core import Document

from src.services.chunking import ChunkingService, EnrichedChunk, get_chunking_service


class TestChunkingService:
    """Test suite for ChunkingService."""

    @pytest.fixture
    def chunking_service(self):
        """Provide ChunkingService with test configuration."""
        return ChunkingService(
            parent_chunk_size=500,
            parent_chunk_overlap=50,
            child_chunk_size=200,
            child_chunk_overlap=20,
        )

    def test_initialization(self, chunking_service):
        """Test that service initializes with correct parameters."""
        assert chunking_service.parent_chunk_size == 500
        assert chunking_service.parent_chunk_overlap == 50
        assert chunking_service.child_chunk_size == 200
        assert chunking_service.child_chunk_overlap == 20

    def test_chunk_document_creates_hierarchy(self, chunking_service):
        """Test that chunking creates two-level hierarchy."""
        text = " ".join(["Test sentence."] * 200)  # Long text
        doc = Document(text=text)

        parent_chunks, child_chunks = chunking_service.chunk_document(
            document=doc, doc_id="test_doc", doc_title="Test Document"
        )

        # Should create both parent and child chunks
        assert len(parent_chunks) > 0
        assert len(child_chunks) > 0
        # Should have more children than parents
        assert len(child_chunks) >= len(parent_chunks)

    def test_chunk_document_preserves_parent_child_links(self, chunking_service):
        """Test that child chunks link to parent chunks."""
        text = " ".join(["Test sentence."] * 200)
        doc = Document(text=text)

        parent_chunks, child_chunks = chunking_service.chunk_document(
            document=doc, doc_id="test_doc", doc_title="Test Document"
        )

        # Get parent IDs
        parent_ids = {p.id for p in parent_chunks}

        # Verify all children link to valid parents
        for child in child_chunks:
            assert child.parent_id is not None
            assert child.parent_id in parent_ids

    def test_chunk_document_enriches_children_only(self, chunking_service):
        """Test that only child chunks are contextually enriched."""
        text = "The Pythagorean theorem states that a² + b² = c²."
        doc = Document(text=text)

        parent_chunks, child_chunks = chunking_service.chunk_document(
            document=doc, doc_id="doc1", doc_title="Geometry Notes"
        )

        # Parents should not be enriched
        for parent in parent_chunks:
            assert parent.original_text == parent.contextual_text
            assert not parent.metadata.get("is_contextualized", False)

        # Children should be enriched
        for child in child_chunks:
            assert child.contextual_text != child.original_text
            assert child.metadata["is_contextualized"]
            assert "Document: Geometry Notes" in child.contextual_text

    def test_chunk_document_preserves_original_text(self, chunking_service):
        """Test that original text is preserved in children."""
        original_text = "The Pythagorean theorem."
        doc = Document(text=original_text)

        _, child_chunks = chunking_service.chunk_document(
            document=doc, doc_id="doc1", doc_title="Test Doc"
        )

        # Original text should be preserved
        for child in child_chunks:
            assert child.original_text in original_text
            assert child.metadata["original_text"] == child.original_text

    def test_chunk_empty_document_raises_error(self, chunking_service):
        """Test that empty document raises ValueError."""
        doc = Document(text="")

        with pytest.raises(ValueError, match="cannot be empty"):
            chunking_service.chunk_document(
                document=doc, doc_id="doc1", doc_title="Empty Doc"
            )

    def test_chunk_whitespace_only_raises_error(self, chunking_service):
        """Test that whitespace-only document raises ValueError."""
        doc = Document(text="   \n\n   ")

        with pytest.raises(ValueError, match="cannot be empty"):
            chunking_service.chunk_document(
                document=doc, doc_id="doc1", doc_title="Whitespace Doc"
            )

    def test_deterministic_context_includes_doc_title(self, chunking_service):
        """Test that contextual prefix includes document title."""
        enriched = chunking_service._create_deterministic_context(
            chunk_text="Test content",
            doc_title="Geometry Notes",
            section_path=[],
            parent_preview=None,
        )

        assert "Document: Geometry Notes" in enriched
        assert "Test content" in enriched

    def test_deterministic_context_includes_section_path(self, chunking_service):
        """Test that contextual prefix includes section path."""
        enriched = chunking_service._create_deterministic_context(
            chunk_text="Test content",
            doc_title="Notes",
            section_path=["Chapter 1", "Section 1.1", "Theorems"],
            parent_preview=None,
        )

        assert "Section: Chapter 1 > Section 1.1 > Theorems" in enriched
        assert "Test content" in enriched

    def test_deterministic_context_includes_parent_preview(self, chunking_service):
        """Test that contextual prefix includes parent context."""
        parent_preview = "Parent context about the topic at hand."
        enriched = chunking_service._create_deterministic_context(
            chunk_text="Test content",
            doc_title="Notes",
            section_path=[],
            parent_preview=parent_preview,
        )

        assert "Context: Parent context" in enriched
        assert "Test content" in enriched

    def test_deterministic_context_combines_all_elements(self, chunking_service):
        """Test that all context elements are combined."""
        enriched = chunking_service._create_deterministic_context(
            chunk_text="Original chunk text",
            doc_title="Math Notes",
            section_path=["Chapter 3", "Pythagorean Theorem"],
            parent_preview="Introduction to right triangles",
        )

        assert "Document: Math Notes" in enriched
        assert "Section: Chapter 3 > Pythagorean Theorem" in enriched
        assert "Context: Introduction to right triangles" in enriched
        assert "Original chunk text" in enriched

    def test_extract_section_path_from_markdown(self, chunking_service):
        """Test extracting section path from markdown headings."""
        markdown = """
# Chapter 1: Introduction

Some intro text.

## Section 1.1: Background

More text here.

### Subsection 1.1.1: Details

Detailed content.
"""
        section_path = chunking_service.extract_section_path(markdown)

        assert len(section_path) == 3
        assert section_path[0] == "Chapter 1: Introduction"
        assert section_path[1] == "Section 1.1: Background"
        assert section_path[2] == "Subsection 1.1.1: Details"

    def test_extract_section_path_only_h1(self, chunking_service):
        """Test extracting section path with only H1."""
        markdown = """
# Main Title

Content without subsections.
"""
        section_path = chunking_service.extract_section_path(markdown)

        assert len(section_path) == 1
        assert section_path[0] == "Main Title"

    def test_extract_section_path_no_headings(self, chunking_service):
        """Test extracting section path when no headings present."""
        text = "Just plain text without any markdown headings."
        section_path = chunking_service.extract_section_path(text)

        assert section_path == []

    def test_chunk_metadata_includes_required_fields(self, chunking_service):
        """Test that chunks have all required metadata fields."""
        text = "Test document content."
        doc = Document(text=text)

        parent_chunks, child_chunks = chunking_service.chunk_document(
            document=doc, doc_id="doc123", doc_title="Test Title"
        )

        # Check parent metadata
        for parent in parent_chunks:
            assert parent.metadata["doc_id"] == "doc123"
            assert parent.metadata["doc_title"] == "Test Title"
            assert "chunk_index" in parent.metadata
            assert parent.metadata["chunk_type"] == "parent"

        # Check child metadata
        for child in child_chunks:
            assert child.metadata["doc_id"] == "doc123"
            assert child.metadata["doc_title"] == "Test Title"
            assert "parent_id" in child.metadata
            assert "chunk_index" in child.metadata
            assert child.metadata["chunk_type"] == "child"
            assert "original_text" in child.metadata

    def test_get_chunking_service_returns_instance(self):
        """Test factory function returns ChunkingService."""
        service = get_chunking_service()

        assert isinstance(service, ChunkingService)


class TestEnrichedChunk:
    """Test suite for EnrichedChunk dataclass."""

    def test_enriched_chunk_creation(self):
        """Test creating EnrichedChunk instance."""
        chunk = EnrichedChunk(
            id="chunk_1",
            original_text="Original text",
            contextual_text="Document: Title\n\nOriginal text",
            parent_id="parent_1",
            chunk_index=0,
            metadata={"doc_id": "doc1", "doc_title": "Title"},
        )

        assert chunk.id == "chunk_1"
        assert chunk.original_text == "Original text"
        assert chunk.contextual_text.startswith("Document:")
        assert chunk.parent_id == "parent_1"
        assert chunk.chunk_index == 0
        assert chunk.metadata["doc_id"] == "doc1"

    def test_enriched_chunk_without_parent(self):
        """Test creating parent chunk (no parent_id)."""
        chunk = EnrichedChunk(
            id="parent_1",
            original_text="Parent content",
            contextual_text="Parent content",
            parent_id=None,
            chunk_index=0,
            metadata={"chunk_type": "parent"},
        )

        assert chunk.parent_id is None
        assert chunk.metadata["chunk_type"] == "parent"
