"""
Integration tests for IngestionService.

Tests the complete ingestion pipeline against real Qdrant 1.20.0:
- Document loading and validation
- Chunking and enrichment
- Embedding generation
- Qdrant indexing
- Duplicate detection
- Update handling
- Retrieval verification
"""

import pytest
from pathlib import Path
from uuid import uuid4

from src.services.ingestion_service import (
    IngestionService,
    get_ingestion_service,
    generate_doc_id,
    generate_chunk_id,
    compute_content_hash,
)
from src.core.vector_store import get_vector_store


@pytest.fixture
def test_collection_name():
    """Generate unique collection name for test isolation."""
    return f"test_ingestion_{uuid4().hex[:8]}"


@pytest.fixture
def ingestion_service(test_collection_name):
    """Provide IngestionService instance with test collection."""
    service = get_ingestion_service(
        embedding_batch_size=16,
        collection_name=test_collection_name
    )
    
    # Ensure collection is created
    service.vector_store.create_collection()
    
    yield service
    
    # Cleanup: delete test collection
    try:
        service.vector_store.client.delete_collection(test_collection_name)
    except:
        pass


@pytest.fixture
def sample_documents_dir():
    """Path to sample documents directory."""
    return Path(__file__).parent.parent / "fixtures" / "sample_documents"


@pytest.mark.integration
class TestIngestionServiceBasics:
    """Test basic ingestion functionality."""
    
    def test_generate_doc_id_deterministic(self):
        """Test that doc_id generation is deterministic."""
        path1 = "/path/to/document.txt"
        path2 = "/path/to/document.txt"
        path3 = "/path/to/other.txt"
        
        id1 = generate_doc_id(path1)
        id2 = generate_doc_id(path2)
        id3 = generate_doc_id(path3)
        
        # Same path should give same ID
        assert id1 == id2
        
        # Different paths should give different IDs
        assert id1 != id3
        
        # IDs should be valid UUIDs
        from uuid import UUID
        UUID(id1)  # Should not raise
        UUID(id3)  # Should not raise
    
    def test_generate_chunk_id_deterministic(self):
        """Test that chunk_id generation is deterministic."""
        doc_id = "123e4567-e89b-12d3-a456-426614174000"
        
        chunk_id_1a = generate_chunk_id(doc_id, 0)
        chunk_id_1b = generate_chunk_id(doc_id, 0)
        chunk_id_2 = generate_chunk_id(doc_id, 1)
        
        # Same doc_id and index should give same chunk_id
        assert chunk_id_1a == chunk_id_1b
        
        # Different index should give different chunk_id
        assert chunk_id_1a != chunk_id_2
    
    def test_compute_content_hash_deterministic(self):
        """Test that content hash is deterministic."""
        text1 = "This is a test document."
        text2 = "This is a test document."
        text3 = "This is a different document."
        
        hash1 = compute_content_hash(text1)
        hash2 = compute_content_hash(text2)
        hash3 = compute_content_hash(text3)
        
        # Same content should give same hash
        assert hash1 == hash2
        
        # Different content should give different hash
        assert hash1 != hash3
    
    def test_load_document_txt(self, ingestion_service, sample_documents_dir):
        """Test loading TXT document."""
        file_path = str(sample_documents_dir / "history_wwii.txt")
        
        text, metadata = ingestion_service.load_document(file_path)
        
        assert len(text) > 0
        assert "World War II" in text
        assert metadata["file_name"] == "history_wwii.txt"
        assert metadata["file_extension"] == ".txt"
        assert metadata["file_size_bytes"] > 0
    
    def test_load_document_markdown(self, ingestion_service, sample_documents_dir):
        """Test loading Markdown document."""
        file_path = str(sample_documents_dir / "math_calculus.md")
        
        text, metadata = ingestion_service.load_document(file_path)
        
        assert len(text) > 0
        assert "Calculus" in text or "calculus" in text.lower()
        assert metadata["file_name"] == "math_calculus.md"
        assert metadata["file_extension"] == ".md"
    
    def test_load_document_not_found(self, ingestion_service):
        """Test loading non-existent document raises error."""
        with pytest.raises(FileNotFoundError):
            ingestion_service.load_document("nonexistent.txt")
    
    def test_load_document_unsupported_type(self, ingestion_service, tmp_path):
        """Test loading unsupported file type raises error."""
        # Create a .pdf file (unsupported)
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            ingestion_service.load_document(str(pdf_file))
    
    def test_detect_structure(self, ingestion_service):
        """Test structure detection."""
        text = """# Main Title

## Section One

This is some content with a code block:

```python
def hello():
    print("world")
```

## Section Two

Some math: $$E = mc^2$$

- List item 1
- List item 2
"""
        
        metadata = ingestion_service.detect_structure(text, "test.md")
        
        assert metadata["title"] == "Main Title"
        assert metadata["content_hints"]["has_headings"] is True
        assert metadata["content_hints"]["has_code_blocks"] is True
        assert metadata["content_hints"]["has_math"] is True
        assert metadata["content_hints"]["has_lists"] is True


@pytest.mark.integration
class TestIngestionServicePipeline:
    """Test complete ingestion pipeline."""
    
    def test_ingest_single_document(self, ingestion_service, sample_documents_dir):
        """Test ingesting a single document."""
        file_path = str(sample_documents_dir / "programming_python.md")
        
        result = ingestion_service.ingest_document(file_path)
        
        # Verify result
        assert result.success is True
        assert result.chunks_created > 0
        assert result.chunks_indexed > 0
        assert result.chunks_created == result.chunks_indexed
        assert result.doc_path == file_path
        assert result.error is None
        assert result.processing_time_seconds > 0
        
        # Verify doc_id is deterministic
        expected_doc_id = generate_doc_id(file_path)
        assert result.doc_id == expected_doc_id
    
    def test_ingest_creates_retrievable_chunks(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test that ingested chunks are retrievable from Qdrant."""
        file_path = str(sample_documents_dir / "math_calculus.md")
        
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # Verify we can count chunks
        count = ingestion_service.vector_store.count_points()
        assert count == result.chunks_indexed
        assert count > 0
        
        # Verify we can retrieve chunks via search (since IDs are UUIDs)
        query = "derivative"
        query_embedding = ingestion_service.embedding_service.embed(query)
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=1
        )
        
        assert len(search_results) > 0
        point = search_results[0]
        assert point.payload["doc_id"] == result.doc_id
        assert "text" in point.payload
        assert "enriched_text" in point.payload
    
    def test_ingest_preserves_metadata(self, ingestion_service, sample_documents_dir):
        """Test that ingestion preserves all required metadata."""
        file_path = str(sample_documents_dir / "physics_mechanics.md")
        
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # Get a chunk via search and verify metadata
        query = "Newton"
        query_embedding = ingestion_service.embedding_service.embed(query)
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=1
        )
        
        assert len(search_results) > 0
        point = search_results[0]
        payload = point.payload
        
        # Source identification
        assert payload["doc_id"] == result.doc_id
        assert "chunk_id" in payload
        assert payload["doc_path"] == file_path
        assert "doc_title" in payload
        
        # Content versioning
        assert "content_hash" in payload
        assert "indexed_at" in payload
        
        # Chunk metadata
        assert "chunk_index" in payload
        assert "chunk_type" in payload
        assert "is_parent" in payload
        
        # Original text preserved (separate from enrichment)
        assert "text" in payload
        assert "enriched_text" in payload
        
        # Structure metadata
        assert "section_path" in payload
        
        # File metadata
        assert payload["file_name"] == "physics_mechanics.md"
        assert payload["file_extension"] == ".md"
    
    def test_ingest_duplicate_skips_unchanged(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test that duplicate ingestion of unchanged document is skipped."""
        file_path = str(sample_documents_dir / "theory_algorithms.md")
        
        # First ingestion
        result1 = ingestion_service.ingest_document(file_path)
        assert result1.success is True
        assert result1.chunks_indexed > 0
        
        # Second ingestion (no changes)
        result2 = ingestion_service.ingest_document(file_path)
        assert result2.success is True
        assert result2.chunks_indexed == 0  # Skipped
        assert result2.was_update is False
        
        # Doc IDs should match
        assert result1.doc_id == result2.doc_id
    
    def test_ingest_with_overwrite_flag(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test that overwrite flag forces reindexing."""
        file_path = str(sample_documents_dir / "history_wwii.txt")
        
        # First ingestion
        result1 = ingestion_service.ingest_document(file_path)
        assert result1.success is True
        chunks_count_1 = result1.chunks_indexed
        
        # Second ingestion with overwrite
        result2 = ingestion_service.ingest_document(file_path, overwrite=True)
        assert result2.success is True
        assert result2.chunks_indexed > 0  # Not skipped
        
        # Should create same number of chunks
        assert result2.chunks_indexed == chunks_count_1
    
    def test_ingest_batch_documents(self, ingestion_service, sample_documents_dir):
        """Test batch ingestion of multiple documents."""
        file_paths = [
            str(sample_documents_dir / "math_calculus.md"),
            str(sample_documents_dir / "physics_mechanics.md"),
            str(sample_documents_dir / "programming_python.md"),
        ]
        
        result = ingestion_service.ingest_documents(file_paths)
        
        assert result.total_files == 3
        assert result.successful == 3
        assert result.failed == 0
        assert result.total_chunks_indexed > 0
        assert len(result.results) == 3
        
        # All individual results should be successful
        for individual_result in result.results:
            assert individual_result.success is True
            assert individual_result.chunks_indexed > 0
    
    def test_ingest_batch_with_failure(self, ingestion_service, sample_documents_dir):
        """Test batch ingestion handles individual failures gracefully."""
        file_paths = [
            str(sample_documents_dir / "math_calculus.md"),
            "nonexistent_file.txt",  # This will fail
            str(sample_documents_dir / "physics_mechanics.md"),
        ]
        
        result = ingestion_service.ingest_documents(file_paths)
        
        assert result.total_files == 3
        assert result.successful == 2
        assert result.failed == 1
        
        # Check individual results
        assert result.results[0].success is True
        assert result.results[1].success is False
        assert result.results[1].error is not None
        assert result.results[2].success is True


@pytest.mark.integration
class TestIngestionServiceRetrieval:
    """Test that ingested documents are properly retrievable."""
    
    def test_dense_search_after_ingestion(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test dense vector search on ingested documents."""
        # Ingest a document
        file_path = str(sample_documents_dir / "math_calculus.md")
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # Generate embedding for a query
        query = "What is the derivative of x squared?"
        query_embedding = ingestion_service.embedding_service.embed(query)
        
        # Search
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=5
        )
        
        # Verify results
        assert len(search_results) > 0
        assert len(search_results) <= 5
        
        # All results should be from our document
        for search_result in search_results:
            assert search_result.payload["doc_id"] == result.doc_id
            assert "text" in search_result.payload
            assert search_result.score > 0
    
    def test_bm25_search_after_ingestion(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test BM25 text search on ingested documents."""
        # Ingest a document
        file_path = str(sample_documents_dir / "programming_python.md")
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # BM25 search
        search_results = ingestion_service.vector_store.bm25_search(
            query_text="list comprehension python",
            top_k=5
        )
        
        # Verify results
        assert len(search_results) > 0
        
        # Results should contain relevant content
        top_result = search_results[0]
        assert top_result.payload["doc_id"] == result.doc_id
        
        # The text should contain related terms
        text_lower = top_result.payload["text"].lower()
        assert any(term in text_lower for term in ["list", "comprehension", "python"])
    
    def test_hybrid_search_after_ingestion(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test hybrid search (dense + BM25 with RRF) on ingested documents."""
        # Ingest a document
        file_path = str(sample_documents_dir / "physics_mechanics.md")
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # Hybrid search
        query = "Newton's second law force and acceleration"
        query_embedding = ingestion_service.embedding_service.embed(query)
        
        search_results = ingestion_service.vector_store.hybrid_search(
            query_text=query,
            query_vector=query_embedding,
            top_k=5
        )
        
        # Verify results
        assert len(search_results) > 0
        assert len(search_results) <= 5
        
        # Results should be from our document
        for search_result in search_results:
            assert search_result.payload["doc_id"] == result.doc_id
    
    def test_retrieval_across_multiple_documents(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test retrieval works correctly across multiple ingested documents."""
        # Ingest multiple documents
        file_paths = [
            str(sample_documents_dir / "math_calculus.md"),
            str(sample_documents_dir / "physics_mechanics.md"),
            str(sample_documents_dir / "programming_python.md"),
        ]
        
        batch_result = ingestion_service.ingest_documents(file_paths)
        assert batch_result.successful == 3
        
        # Get doc IDs
        doc_ids = {result.doc_id for result in batch_result.results}
        assert len(doc_ids) == 3
        
        # Query that should match physics document
        query = "What is Newton's first law?"
        query_embedding = ingestion_service.embedding_service.embed(query)
        
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=3
        )
        
        assert len(search_results) > 0
        
        # Top result should be from physics document
        physics_doc_id = generate_doc_id(
            str(sample_documents_dir / "physics_mechanics.md")
        )
        assert search_results[0].payload["doc_id"] == physics_doc_id
    
    def test_chunk_parent_child_relationships(
        self, 
        ingestion_service, 
        sample_documents_dir
    ):
        """Test that parent-child chunk relationships are preserved."""
        file_path = str(sample_documents_dir / "theory_algorithms.md")
        result = ingestion_service.ingest_document(file_path)
        assert result.success is True
        
        # Search for child chunks (is_parent should be False)
        query = "algorithm"
        query_embedding = ingestion_service.embedding_service.embed(query)
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=20
        )
        
        # Find child chunks
        child_chunks = [r for r in search_results if not r.payload.get("is_parent", True)]
        
        # Verify children exist and have valid parent references
        assert len(child_chunks) > 0, "Should have some child chunks"
        
        for child in child_chunks:
            # Child chunks should have parent_id
            assert child.payload.get("parent_id") is not None
            assert child.payload["is_parent"] is False


@pytest.mark.integration
class TestIngestionServiceEdgeCases:
    """Test edge cases and error handling."""
    
    def test_ingest_empty_file(self, ingestion_service, tmp_path):
        """Test ingesting empty file raises error."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = ingestion_service.ingest_document(str(empty_file))
        
        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.lower()
    
    def test_ingest_very_small_document(self, ingestion_service, tmp_path):
        """Test ingesting very small document."""
        small_file = tmp_path / "small.txt"
        small_file.write_text("This is a tiny document.")
        
        result = ingestion_service.ingest_document(str(small_file))
        
        # Should succeed and create at least one chunk
        assert result.success is True
        assert result.chunks_indexed >= 1
    
    def test_ingest_large_document(self, ingestion_service, tmp_path):
        """Test ingesting large document with many chunks."""
        # Create a large document
        large_content = "This is a sentence. " * 10000  # ~10k sentences
        large_file = tmp_path / "large.txt"
        large_file.write_text(large_content)
        
        result = ingestion_service.ingest_document(str(large_file))
        
        # Should succeed and create many chunks
        assert result.success is True
        assert result.chunks_indexed > 10  # Should be split into multiple chunks
    
    def test_ingest_unicode_content(self, ingestion_service, tmp_path):
        """Test ingesting document with Unicode characters."""
        unicode_content = """
        # Mathematical Symbols
        
        Σ (sigma) represents summation
        ∫ (integral) for integration
        √ (square root)
        π (pi) ≈ 3.14159
        
        # Other Languages
        
        Chinese: 你好世界
        Arabic: مرحبا بالعالم
        Russian: Привет мир
        """
        
        unicode_file = tmp_path / "unicode.md"
        unicode_file.write_text(unicode_content, encoding="utf-8")
        
        result = ingestion_service.ingest_document(str(unicode_file))
        
        assert result.success is True
        assert result.chunks_indexed > 0
        
        # Verify content is preserved via search
        query = "mathematical symbols"
        query_embedding = ingestion_service.embedding_service.embed(query)
        search_results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=1
        )
        
        assert len(search_results) > 0
        text = search_results[0].payload["text"]
        
        # Should contain some Unicode characters
        assert any(ord(char) > 127 for char in text)
