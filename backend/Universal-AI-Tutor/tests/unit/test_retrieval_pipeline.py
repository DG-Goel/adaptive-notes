"""
Unit tests for RetrievalPipeline.

Tests hybrid retrieval orchestration with mocked components.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

from src.core.retrieval_pipeline import (
    RetrievalPipeline,
    RetrievalResult,
    get_retrieval_pipeline
)
from src.core.reranker import RerankResult


@dataclass
class MockSearchResult:
    """Mock search result object."""
    id: str
    score: float
    payload: dict


@pytest.fixture
def mock_embedding_service():
    """Provide mocked EmbeddingService."""
    with patch("src.core.retrieval_pipeline.get_embedding_service") as mock:
        service = MagicMock()
        service.embed.return_value = [0.1] * 384
        # Mock estimate_tokens to return small values for child chunks
        def estimate_tokens_side_effect(text):
            # Short texts simulate small chunks
            if len(text) < 50:
                return 50  # Small chunk
            else:
                return 200  # Larger chunk with parent context
        service.estimate_tokens.side_effect = estimate_tokens_side_effect
        # Mock truncate method
        service.truncate_to_max_length.side_effect = lambda text, max_tokens: text[:max_tokens*4]
        mock.return_value = service
        yield service


@pytest.fixture
def mock_vector_store():
    """Provide mocked VectorStore."""
    with patch("src.core.retrieval_pipeline.get_vector_store") as mock:
        store = MagicMock()
        
        # Mock search methods
        def create_mock_results(count=5):
            return [
                MockSearchResult(
                    id=f"id_{i}",
                    score=0.9 - i * 0.1,
                    payload={
                        "chunk_id": f"chunk_{i}",
                        "text": f"Result {i} text",
                        "doc_id": f"doc_{i}",
                        "doc_title": f"Document {i}",
                        "doc_path": f"/path/doc_{i}.md",
                        "section_path": ["Section"],
                        "chunk_index": i,
                        "is_parent": False,
                        "parent_id": f"parent_{i}",
                    }
                )
                for i in range(count)
            ]
        
        store.dense_search.return_value = create_mock_results()
        store.bm25_search.return_value = create_mock_results()
        store.hybrid_search.return_value = create_mock_results()
        
        mock.return_value = store
        yield store


@pytest.fixture
def mock_reranker():
    """Provide mocked RerankerService."""
    with patch("src.core.retrieval_pipeline.get_reranker_service") as mock:
        service = MagicMock()
        
        def rerank_side_effect(query, chunks, top_k=5):
            # Return RerankResult objects
            results = []
            for i, chunk in enumerate(chunks[:top_k]):
                if isinstance(chunk, MockSearchResult):
                    payload = chunk.payload
                    original_score = chunk.score
                else:
                    payload = chunk
                    original_score = chunk.get("score", 0.5)
                
                results.append(
                    RerankResult(
                        chunk_id=payload.get("chunk_id", f"chunk_{i}"),
                        text=payload.get("text", ""),
                        original_score=original_score,
                        rerank_score=1.0 - i * 0.15,  # Descending scores
                        payload=payload
                    )
                )
            return results
        
        service.rerank.side_effect = rerank_side_effect
        mock.return_value = service
        yield service


@pytest.fixture
def pipeline(mock_embedding_service, mock_vector_store, mock_reranker):
    """Provide RetrievalPipeline with mocked dependencies."""
    return RetrievalPipeline()


class TestRetrievalPipeline:
    """Test suite for RetrievalPipeline."""
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with correct defaults."""
        assert pipeline is not None
        assert pipeline.dense_top_k == 20
        assert pipeline.bm25_top_k == 20
        assert pipeline.rerank_top_k == 5
        assert pipeline.use_reranking is True
    
    def test_retrieve_hybrid_with_reranking(
        self,
        pipeline,
        mock_embedding_service,
        mock_vector_store,
        mock_reranker
    ):
        """Test hybrid retrieval with reranking enabled."""
        query = "What is machine learning?"
        results = pipeline.retrieve(query, method="hybrid")
        
        # Should call embedding service
        mock_embedding_service.embed.assert_called_once_with(query)
        
        # Should call hybrid search
        mock_vector_store.hybrid_search.assert_called_once()
        
        # Should call reranker
        mock_reranker.rerank.assert_called_once()
        
        # Should return RetrievalResult objects
        assert len(results) == 5  # rerank_top_k
        assert all(isinstance(r, RetrievalResult) for r in results)
        
        # Should have rerank scores
        assert all(r.rerank_score is not None for r in results)
    
    def test_retrieve_dense_only(
        self,
        pipeline,
        mock_vector_store,
        mock_reranker
    ):
        """Test dense-only retrieval."""
        results = pipeline.retrieve("test query", method="dense")
        
        # Should call dense search
        mock_vector_store.dense_search.assert_called_once()
        
        # Should NOT call hybrid or bm25
        mock_vector_store.hybrid_search.assert_not_called()
        mock_vector_store.bm25_search.assert_not_called()
        
        # Should still rerank
        mock_reranker.rerank.assert_called_once()
        
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)
    
    def test_retrieve_bm25_only(
        self,
        pipeline,
        mock_vector_store
    ):
        """Test BM25-only retrieval."""
        results = pipeline.retrieve("test query", method="bm25")
        
        # Should call BM25 search
        mock_vector_store.bm25_search.assert_called_once()
        
        # Should NOT call dense or hybrid
        mock_vector_store.dense_search.assert_not_called()
        mock_vector_store.hybrid_search.assert_not_called()
        
        assert len(results) > 0
    
    def test_retrieve_without_reranking(
        self,
        pipeline,
        mock_reranker
    ):
        """Test retrieval with reranking disabled."""
        results = pipeline.retrieve(
            "test query",
            use_reranking=False
        )
        
        # Should NOT call reranker
        mock_reranker.rerank.assert_not_called()
        
        # Should still return results
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)
    
    def test_retrieve_custom_top_k(self, pipeline):
        """Test retrieval with custom top_k."""
        results = pipeline.retrieve("test query", top_k=3)
        
        assert len(results) == 3
    
    def test_retrieve_empty_query_raises_error(self, pipeline):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            pipeline.retrieve("")
    
    def test_retrieve_no_results(
        self,
        pipeline,
        mock_vector_store
    ):
        """Test handling of no search results."""
        mock_vector_store.hybrid_search.return_value = []
        
        results = pipeline.retrieve("query with no results")
        
        assert len(results) == 0
    
    def test_retrieval_result_metadata(self, pipeline):
        """Test that RetrievalResult contains all required metadata."""
        results = pipeline.retrieve("test query")
        
        assert len(results) > 0
        result = results[0]
        
        # Check all required fields
        assert hasattr(result, "chunk_id")
        assert hasattr(result, "text")
        assert hasattr(result, "doc_id")
        assert hasattr(result, "doc_title")
        assert hasattr(result, "doc_path")
        assert hasattr(result, "section_path")
        assert hasattr(result, "chunk_index")
        assert hasattr(result, "is_parent")
        assert hasattr(result, "parent_id")
        assert hasattr(result, "final_score")
        assert hasattr(result, "payload")
        
        # Verify types
        assert isinstance(result.chunk_id, str)
        assert isinstance(result.text, str)
        assert isinstance(result.final_score, (int, float))
        assert isinstance(result.payload, dict)
    
    def test_retrieval_result_scores(self, pipeline):
        """Test that scores are properly assigned."""
        results = pipeline.retrieve("test query", method="hybrid")
        
        result = results[0]
        
        # With reranking, should have rerank_score
        assert result.rerank_score is not None
        assert result.final_score == result.rerank_score
    
    def test_retrieve_with_context_expansion(
        self,
        pipeline,
        mock_vector_store
    ):
        """Test retrieval with parent context expansion."""
        # Mock parent chunk retrieval
        mock_parent = MockSearchResult(
            id="parent_0",
            score=0.5,
            payload={
                "chunk_id": "parent_0",
                "text": "This is the parent chunk context that should be prepended.",
                "doc_id": "doc_0",
                "is_parent": True,
                "parent_id": None,
            }
        )
        mock_vector_store.get_point.return_value = mock_parent
        
        results = pipeline.retrieve_with_context_expansion(
            "test query",
            expand_parents=True
        )
        
        # Should have results
        assert len(results) > 0
        
        # Verify that parent context was included in at least one result
        # Check if parent text appears in any of the expanded results
        parent_text = "This is the parent chunk context that should be prepended."
        assert any(parent_text in r.text for r in results), \
            "Parent context should be included in expanded results"
    
    def test_context_expansion_only_for_children(
        self,
        pipeline,
        mock_vector_store
    ):
        """Test that context expansion only applies to child chunks."""
        # Create results with parent chunks
        mock_vector_store.hybrid_search.return_value = [
            MockSearchResult(
                id="parent_chunk",
                score=0.9,
                payload={
                    "chunk_id": "parent_chunk",
                    "text": "Parent chunk text",
                    "doc_id": "doc_1",
                    "doc_title": "Doc",
                    "doc_path": "/path",
                    "section_path": [],
                    "chunk_index": 0,
                    "is_parent": True,  # This is a parent
                    "parent_id": None,
                }
            )
        ]
        
        results = pipeline.retrieve_with_context_expansion(
            "test query",
            expand_parents=True
        )
        
        # Parent chunks should not be expanded
        assert len(results) > 0
        assert results[0].is_parent is True
        # Parent fetch should not be called for parent chunks
        mock_vector_store.get_point.assert_not_called()
    
    def test_get_retrieval_pipeline_factory(
        self,
        mock_embedding_service,
        mock_vector_store,
        mock_reranker
    ):
        """Test factory function."""
        pipeline = get_retrieval_pipeline(collection_name="test_collection")
        
        assert pipeline is not None
        assert isinstance(pipeline, RetrievalPipeline)
        assert pipeline.collection_name == "test_collection"
    
    def test_pipeline_without_reranker(
        self,
        mock_embedding_service,
        mock_vector_store
    ):
        """Test pipeline initialization without reranker."""
        with patch("src.core.retrieval_pipeline.get_reranker_service") as mock_reranker:
            pipeline = RetrievalPipeline(use_reranking=False)
            
            # Should not create reranker
            assert pipeline.reranker_service is None
            
            # Should still work
            results = pipeline.retrieve("test query")
            assert len(results) > 0
