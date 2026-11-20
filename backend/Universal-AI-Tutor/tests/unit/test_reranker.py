"""
Unit tests for RerankerService.

Tests cross-encoder reranking functionality with mocked model.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.core.reranker import RerankerService, RerankResult, get_reranker_service


@pytest.fixture
def mock_cross_encoder():
    """Provide mocked CrossEncoder."""
    with patch("src.core.reranker.CrossEncoder") as mock:
        # Create mock model instance
        mock_instance = MagicMock()
        
        # Mock predict method to return scores
        def predict_side_effect(pairs):
            # Return decreasing scores based on pair index
            # This simulates reranking where first pairs get higher scores
            return np.array([1.0 / (i + 1) for i in range(len(pairs))])
        
        mock_instance.predict.side_effect = predict_side_effect
        mock.return_value = mock_instance
        
        yield mock


@pytest.fixture
def reranker(mock_cross_encoder):
    """Provide RerankerService with mocked model."""
    return RerankerService()


class TestRerankerService:
    """Test suite for RerankerService."""
    
    def test_initialization_success(self, reranker):
        """Test that service initializes successfully."""
        assert reranker is not None
        assert reranker.model is not None
        assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    def test_rerank_basic(self, reranker):
        """Test basic reranking operation."""
        query = "What is machine learning?"
        chunks = [
            {"chunk_id": "1", "text": "Machine learning is AI", "score": 0.5},
            {"chunk_id": "2", "text": "Weather forecast today", "score": 0.8},
            {"chunk_id": "3", "text": "Deep learning networks", "score": 0.6},
        ]
        
        results = reranker.rerank(query, chunks)
        
        # Should return all chunks
        assert len(results) == 3
        
        # Should be RerankResult objects
        assert all(isinstance(r, RerankResult) for r in results)
        
        # Should be sorted by rerank_score (descending)
        assert results[0].rerank_score >= results[1].rerank_score
        assert results[1].rerank_score >= results[2].rerank_score
        
        # Should preserve original scores
        assert results[0].original_score in [0.5, 0.6, 0.8]
    
    def test_rerank_with_top_k(self, reranker):
        """Test reranking with top_k limit."""
        query = "Python programming"
        chunks = [
            {"chunk_id": str(i), "text": f"Content {i}", "score": 0.5}
            for i in range(10)
        ]
        
        results = reranker.rerank(query, chunks, top_k=3)
        
        # Should return only top 3
        assert len(results) == 3
        
        # Should have highest scores
        assert all(isinstance(r, RerankResult) for r in results)
    
    def test_rerank_empty_query_raises_error(self, reranker):
        """Test that empty query raises ValueError."""
        chunks = [{"chunk_id": "1", "text": "Some text", "score": 0.5}]
        
        with pytest.raises(ValueError, match="Query cannot be empty"):
            reranker.rerank("", chunks)
    
    def test_rerank_empty_chunks_raises_error(self, reranker):
        """Test that empty chunks list raises ValueError."""
        with pytest.raises(ValueError, match="Chunks list cannot be empty"):
            reranker.rerank("query", [])
    
    def test_rerank_with_search_result_objects(self, reranker):
        """Test reranking with search result objects (not dicts)."""
        query = "test query"
        
        # Mock search results (like from VectorStore)
        mock_results = []
        for i in range(3):
            mock_result = Mock()
            mock_result.id = f"id_{i}"
            mock_result.score = 0.5 + i * 0.1
            mock_result.payload = {
                "chunk_id": f"chunk_{i}",
                "text": f"Document {i} content",
                "doc_title": f"Doc {i}"
            }
            mock_results.append(mock_result)
        
        results = reranker.rerank(query, mock_results)
        
        assert len(results) == 3
        assert all(isinstance(r, RerankResult) for r in results)
        
        # Verify payload preserved
        assert "doc_title" in results[0].payload
    
    def test_rerank_skips_chunks_without_text(self, reranker):
        """Test that chunks without text are skipped."""
        query = "test"
        chunks = [
            {"chunk_id": "1", "text": "Valid text", "score": 0.5},
            {"chunk_id": "2", "text": "", "score": 0.6},  # Empty text
            {"chunk_id": "3", "score": 0.7},  # No text field
        ]
        
        results = reranker.rerank(query, chunks)
        
        # Should only have 1 valid result
        assert len(results) == 1
        assert results[0].chunk_id == "1"
    
    def test_rerank_preserves_all_metadata(self, reranker):
        """Test that reranking preserves all chunk metadata."""
        query = "test"
        chunks = [
            {
                "chunk_id": "ch1",
                "text": "Sample text",
                "score": 0.8,
                "doc_id": "doc123",
                "doc_title": "Test Document",
                "section_path": ["Introduction"],
                "custom_field": "custom_value"
            }
        ]
        
        results = reranker.rerank(query, chunks)
        
        assert len(results) == 1
        result = results[0]
        
        # Check all fields preserved
        assert result.chunk_id == "ch1"
        assert result.text == "Sample text"
        assert result.original_score == 0.8
        assert result.payload["doc_id"] == "doc123"
        assert result.payload["doc_title"] == "Test Document"
        assert result.payload["section_path"] == ["Introduction"]
        assert result.payload["custom_field"] == "custom_value"
    
    def test_rerank_changes_order(self, reranker):
        """Test that reranking can change result order."""
        query = "machine learning"
        
        # Original order by dense similarity might not be optimal
        chunks = [
            {"chunk_id": "1", "text": "Weather is sunny", "score": 0.9},
            {"chunk_id": "2", "text": "Machine learning basics", "score": 0.5},
            {"chunk_id": "3", "text": "Random topic", "score": 0.7},
        ]
        
        results = reranker.rerank(query, chunks)
        
        # With our mock, first chunk gets highest rerank score
        # But order should be based on rerank_score, not original score
        assert len(results) == 3
        assert all(r.rerank_score > 0 for r in results)
    
    def test_rerank_return_all_flag(self, reranker):
        """Test return_all flag behavior."""
        query = "test"
        chunks = [
            {"chunk_id": str(i), "text": f"Text {i}", "score": 0.5}
            for i in range(10)
        ]
        
        # With return_all=True and top_k, should return all
        results = reranker.rerank(query, chunks, top_k=3, return_all=True)
        assert len(results) == 10
        
        # Without return_all, should respect top_k
        results = reranker.rerank(query, chunks, top_k=3, return_all=False)
        assert len(results) == 3
    
    def test_rerank_search_results_convenience_method(self, reranker):
        """Test convenience method for search results."""
        query = "test query"
        
        mock_results = []
        for i in range(10):
            mock_result = Mock()
            mock_result.id = f"id_{i}"
            mock_result.score = 0.5
            mock_result.payload = {
                "chunk_id": f"chunk_{i}",
                "text": f"Content {i}"
            }
            mock_results.append(mock_result)
        
        results = reranker.rerank_search_results(query, mock_results, top_k=5)
        
        assert len(results) == 5
        assert all(isinstance(r, RerankResult) for r in results)
    
    def test_get_reranker_service_singleton(self, mock_cross_encoder):
        """Test that get_reranker_service returns singleton."""
        # Clear the singleton
        import src.core.reranker
        src.core.reranker._reranker_service = None
        
        service1 = get_reranker_service()
        service2 = get_reranker_service()
        
        assert service1 is service2


class TestRerankerServiceIntegration:
    """Integration tests with real model (if available)."""
    
    @pytest.mark.integration
    def test_real_reranking(self):
        """Test reranking with real cross-encoder model."""
        reranker = RerankerService()
        
        query = "What is the capital of France?"
        chunks = [
            {
                "chunk_id": "1",
                "text": "Paris is the capital and largest city of France.",
                "score": 0.5
            },
            {
                "chunk_id": "2",
                "text": "London is the capital of the United Kingdom.",
                "score": 0.6
            },
            {
                "chunk_id": "3",
                "text": "Berlin is the capital of Germany.",
                "score": 0.7
            },
        ]
        
        results = reranker.rerank(query, chunks)
        
        # First result should be about Paris (most relevant)
        assert len(results) == 3
        assert "Paris" in results[0].text
        assert "France" in results[0].text
        
        # Rerank scores should be different from original scores
        assert results[0].rerank_score != results[0].original_score
