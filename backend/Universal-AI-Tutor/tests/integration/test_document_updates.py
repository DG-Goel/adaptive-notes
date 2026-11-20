"""
Integration tests for document update handling.

Tests proper cleanup and replacement of document chunks when content changes.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from src.services.ingestion_service import (
    get_ingestion_service,
    generate_doc_id,
    generate_chunk_id,
    compute_content_hash,
)


@pytest.fixture
def test_collection_name():
    """Generate unique collection name for test isolation."""
    return f"test_updates_{uuid4().hex[:8]}"


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


@pytest.mark.integration
class TestDocumentUpdates:
    """Test document update handling with proper cleanup."""
    
    def test_unchanged_document_skipped(self, ingestion_service, tmp_path):
        """Test that unchanged document ingestion is skipped."""
        # Create test document
        test_file = tmp_path / "test_doc.md"
        test_file.write_text("# Test Document\n\nThis is test content.")
        
        # First ingestion
        result1 = ingestion_service.ingest_document(str(test_file))
        assert result1.success is True
        assert result1.chunks_indexed > 0
        chunks_count_1 = result1.chunks_indexed
        
        # Second ingestion without changes
        result2 = ingestion_service.ingest_document(str(test_file))
        assert result2.success is True
        assert result2.chunks_indexed == 0  # Skipped
        assert result2.was_update is False
        
        # Verify total count unchanged
        total_count = ingestion_service.vector_store.count_points()
        assert total_count == chunks_count_1
    
    def test_modified_document_replaces_old_chunks(self, ingestion_service, tmp_path):
        """Test that modified document properly replaces old chunks."""
        test_file = tmp_path / "test_doc.md"
        
        # Original content
        original_content = "# Original Title\n\nOriginal content here."
        test_file.write_text(original_content)
        
        # First ingestion
        result1 = ingestion_service.ingest_document(str(test_file))
        assert result1.success is True
        assert result1.chunks_indexed > 0
        doc_id = result1.doc_id
        original_chunk_count = result1.chunks_indexed
        original_hash = compute_content_hash(original_content)
        
        # Store original chunk IDs
        original_chunk_ids = [generate_chunk_id(doc_id, i) for i in range(result1.chunks_indexed)]
        
        # Verify chunks exist with original content
        original_chunks = ingestion_service.vector_store.get_points(original_chunk_ids)
        assert len(original_chunks) == result1.chunks_indexed
        for chunk in original_chunks:
            assert chunk.payload["content_hash"] == original_hash
            assert "Original" in chunk.payload["text"]
        
        # Modify content
        modified_content = "# Modified Title\n\nCompletely different content now."
        test_file.write_text(modified_content)
        modified_hash = compute_content_hash(modified_content)
        
        # Second ingestion with changes
        result2 = ingestion_service.ingest_document(str(test_file))
        assert result2.success is True
        assert result2.chunks_indexed > 0
        assert result2.was_update is True
        assert result2.doc_id == doc_id  # Same doc_id
        
        # Verify new chunks exist with new content
        # Note: deterministic IDs mean same positions get same IDs
        new_chunk_ids = [generate_chunk_id(doc_id, i) for i in range(result2.chunks_indexed)]
        new_chunks = ingestion_service.vector_store.get_points(new_chunk_ids)
        assert len(new_chunks) == result2.chunks_indexed
        
        # Verify content and hash updated
        for chunk in new_chunks:
            assert chunk.payload["content_hash"] == modified_hash
            assert "Modified" in chunk.payload["text"]
            assert "Original" not in chunk.payload["text"]
        
        # Verify total count in collection matches new version
        total_count = ingestion_service.vector_store.count_points()
        assert total_count == result2.chunks_indexed
    
    def test_document_update_preserves_other_documents(self, ingestion_service, tmp_path):
        """Test that updating one document doesn't affect others."""
        # Create two documents
        doc1_file = tmp_path / "doc1.md"
        doc2_file = tmp_path / "doc2.md"
        
        doc1_file.write_text("# Document 1\n\nContent of first document.")
        doc2_file.write_text("# Document 2\n\nContent of second document.")
        
        # Ingest both
        result1 = ingestion_service.ingest_document(str(doc1_file))
        result2 = ingestion_service.ingest_document(str(doc2_file))
        
        assert result1.success is True
        assert result2.success is True
        
        doc1_id = result1.doc_id
        doc2_id = result2.doc_id
        doc2_chunks_count = result2.chunks_indexed
        
        # Get doc2 chunk IDs
        doc2_chunk_ids = [generate_chunk_id(doc2_id, i) for i in range(doc2_chunks_count)]
        
        # Modify doc1
        doc1_file.write_text("# Document 1 Modified\n\nCompletely new content.")
        
        # Re-ingest doc1
        result1_updated = ingestion_service.ingest_document(str(doc1_file))
        assert result1_updated.success is True
        assert result1_updated.was_update is True
        
        # Verify doc2 chunks still exist and unchanged
        doc2_chunks_after = ingestion_service.vector_store.get_points(doc2_chunk_ids)
        assert len(doc2_chunks_after) == doc2_chunks_count, "Doc2 chunks should be preserved"
        
        # Verify doc2 content unchanged
        for chunk in doc2_chunks_after:
            assert "second document" in chunk.payload["text"].lower()
    
    def test_section_length_changes(self, ingestion_service, tmp_path):
        """Test document update when sections grow or shrink."""
        test_file = tmp_path / "test_doc.md"
        
        # Short content
        short_content = "# Title\n\nShort paragraph."
        test_file.write_text(short_content)
        
        result1 = ingestion_service.ingest_document(str(test_file))
        assert result1.success is True
        short_chunk_count = result1.chunks_indexed
        
        # Long content (should create more chunks)
        long_content = "# Title\n\n" + ("Long paragraph with lots of content. " * 200)
        test_file.write_text(long_content)
        
        result2 = ingestion_service.ingest_document(str(test_file))
        assert result2.success is True
        assert result2.was_update is True
        long_chunk_count = result2.chunks_indexed
        
        # More chunks should be created
        assert long_chunk_count > short_chunk_count
        
        # Verify total count matches new version only
        total_count = ingestion_service.vector_store.count_points()
        assert total_count == long_chunk_count
    
    def test_removed_sections(self, ingestion_service, tmp_path):
        """Test document update when sections are removed."""
        test_file = tmp_path / "test_doc.md"
        
        # Multi-section content with enough text to create multiple chunks
        full_content = """# Document
        
## Section 1
""" + ("Content for section 1. " * 50) + """

## Section 2
""" + ("Content for section 2. " * 50) + """

## Section 3
""" + ("Content for section 3. " * 50)
        
        test_file.write_text(full_content)
        
        result1 = ingestion_service.ingest_document(str(test_file))
        assert result1.success is True
        full_chunk_count = result1.chunks_indexed
        
        # Remove sections 2 and 3
        reduced_content = """# Document
        
## Section 1
""" + ("Content for section 1. " * 50)
        
        test_file.write_text(reduced_content)
        
        result2 = ingestion_service.ingest_document(str(test_file))
        assert result2.success is True
        assert result2.was_update is True
        reduced_chunk_count = result2.chunks_indexed
        
        # Fewer chunks should exist
        assert reduced_chunk_count < full_chunk_count, \
            f"Expected fewer chunks after removal: {reduced_chunk_count} < {full_chunk_count}"
        
        # Verify total count matches new version only
        total_count = ingestion_service.vector_store.count_points()
        assert total_count == reduced_chunk_count
        
        # Verify removed content not retrievable
        query = "section 2"
        query_embedding = ingestion_service.embedding_service.embed(query)
        results = ingestion_service.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=10
        )
        
        # All results should be from this document (the only one in collection)
        for result in results:
            assert result.payload["doc_id"] == result2.doc_id
            # Section 2 and 3 should not appear
            text_lower = result.payload["text"].lower()
            assert "section 2" not in text_lower
            assert "section 3" not in text_lower
    
    def test_update_with_overwrite_flag(self, ingestion_service, tmp_path):
        """Test overwrite flag forces reindexing even if unchanged."""
        test_file = tmp_path / "test_doc.md"
        test_file.write_text("# Test\n\nUnchanged content.")
        
        # First ingestion
        result1 = ingestion_service.ingest_document(str(test_file))
        assert result1.success is True
        chunks_count_1 = result1.chunks_indexed
        
        # Second ingestion with overwrite=True (no content changes)
        result2 = ingestion_service.ingest_document(str(test_file), overwrite=True)
        assert result2.success is True
        assert result2.chunks_indexed > 0  # Not skipped
        assert result2.chunks_indexed == chunks_count_1
        
        # Total count should still match (old deleted, new inserted)
        total_count = ingestion_service.vector_store.count_points()
        assert total_count == chunks_count_1
    
    def test_deterministic_chunk_ids_after_update(self, ingestion_service, tmp_path):
        """Test that chunk IDs are deterministic and stable for same content."""
        test_file = tmp_path / "test_doc.md"
        content = "# Test Document\n\nStable content for ID testing."
        test_file.write_text(content)
        
        # First ingestion
        result1 = ingestion_service.ingest_document(str(test_file))
        doc_id = result1.doc_id
        chunk_ids_1 = [generate_chunk_id(doc_id, i) for i in range(result1.chunks_indexed)]
        
        # Modify and update
        test_file.write_text("# Test Document\n\nDifferent content now.")
        result2 = ingestion_service.ingest_document(str(test_file))
        
        # Revert to original
        test_file.write_text(content)
        result3 = ingestion_service.ingest_document(str(test_file))
        
        # Chunk IDs should match first ingestion (same content, same position)
        chunk_ids_3 = [generate_chunk_id(doc_id, i) for i in range(result3.chunks_indexed)]
        
        assert result1.chunks_indexed == result3.chunks_indexed
        assert chunk_ids_1 == chunk_ids_3
        
        # Retrieve and verify content matches
        chunks_3 = ingestion_service.vector_store.get_points(chunk_ids_3)
        assert len(chunks_3) == len(chunk_ids_3)
        
        for chunk in chunks_3:
            assert "Stable content" in chunk.payload["text"]
    
    def test_direct_chunk_retrieval_by_id(self, ingestion_service, tmp_path):
        """Test that chunks can be retrieved directly by deterministic ID."""
        test_file = tmp_path / "test_doc.md"
        test_file.write_text("# Test\n\nContent for retrieval test.")
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        doc_id = result.doc_id
        
        # Generate deterministic chunk IDs
        chunk_ids = [generate_chunk_id(doc_id, i) for i in range(result.chunks_indexed)]
        
        # Retrieve each chunk by ID
        for i, chunk_id in enumerate(chunk_ids):
            chunk = ingestion_service.vector_store.get_point(chunk_id)
            assert chunk is not None, f"Chunk {i} should be retrievable by ID"
            assert chunk.payload["doc_id"] == doc_id
            assert chunk.payload["chunk_id"] == chunk_id
    
    def test_parent_child_ids_preserved_after_update(self, ingestion_service, tmp_path):
        """Test that parent-child relationships use correct IDs after update."""
        test_file = tmp_path / "test_doc.md"
        
        # Content that will create parent-child hierarchy
        content = "# Document\n\n" + ("Content paragraph. " * 100)  # Long enough for chunking
        test_file.write_text(content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        doc_id = result.doc_id
        
        # Find child chunks
        chunk_ids = [generate_chunk_id(doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        child_chunks = [c for c in chunks if not c.payload.get("is_parent", True)]
        assert len(child_chunks) > 0, "Should have child chunks"
        
        # Verify parent IDs are valid chunk IDs from this document
        for child in child_chunks:
            parent_id = child.payload.get("parent_id")
            assert parent_id is not None
            
            # Parent ID should be in our chunk_ids list
            assert parent_id in chunk_ids, f"Parent ID {parent_id} should be a valid chunk ID"
            
            # Verify parent exists and is marked as parent
            parent_chunk = ingestion_service.vector_store.get_point(parent_id)
            assert parent_chunk is not None
            assert parent_chunk.payload["is_parent"] is True
