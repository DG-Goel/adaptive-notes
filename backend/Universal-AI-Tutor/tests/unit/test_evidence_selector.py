"""
Unit tests for EvidenceSelector.

Tests evidence sufficiency assessment logic.
"""

import pytest
from src.core.evidence_selector import (
    EvidenceSelector,
    EvidenceAssessment,
    get_evidence_selector
)
from src.core.retrieval_pipeline import RetrievalResult


@pytest.fixture
def evidence_selector():
    """Provide EvidenceSelector instance."""
    return EvidenceSelector(
        min_chunks=2,
        min_avg_score=0.4,
        min_top_score=0.5,
        min_coverage=0.3,
    )


@pytest.fixture
def sample_results():
    """Provide sample retrieval results."""
    return [
        RetrievalResult(
            chunk_id="chunk_1",
            text="Machine learning is a subset of artificial intelligence",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/docs/ml.md",
            section_path=["Introduction"],
            chunk_index=0,
            is_parent=True,
            parent_id=None,
            dense_score=0.9,
            bm25_score=0.8,
            rrf_score=0.85,
            rerank_score=0.92,
            final_score=0.92,
            payload={}
        ),
        RetrievalResult(
            chunk_id="chunk_2",
            text="Supervised learning uses labeled training data",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/docs/ml.md",
            section_path=["Types"],
            chunk_index=1,
            is_parent=False,
            parent_id="chunk_1",
            dense_score=0.85,
            bm25_score=0.75,
            rrf_score=0.8,
            rerank_score=0.87,
            final_score=0.87,
            payload={}
        ),
        RetrievalResult(
            chunk_id="chunk_3",
            text="Deep learning uses neural networks with multiple layers",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/docs/ml.md",
            section_path=["Advanced"],
            chunk_index=2,
            is_parent=False,
            parent_id="chunk_1",
            dense_score=0.8,
            bm25_score=0.7,
            rrf_score=0.75,
            rerank_score=0.82,
            final_score=0.82,
            payload={}
        ),
    ]


class TestEvidenceSelector:
    """Test EvidenceSelector class."""
    
    def test_initialization(self, evidence_selector):
        """Test EvidenceSelector initialization."""
        assert evidence_selector.min_chunks == 2
        assert evidence_selector.min_avg_score == 0.4
        assert evidence_selector.min_top_score == 0.5
        assert evidence_selector.min_coverage == 0.3
    
    def test_assess_sufficient_evidence(self, evidence_selector, sample_results):
        """Test assessment with sufficient evidence."""
        assessment = evidence_selector.assess_evidence(
            query="What is machine learning?",
            retrieved_results=sample_results
        )
        
        assert assessment.is_sufficient is True
        assert assessment.reason == "Evidence appears sufficient"
        assert assessment.chunk_count == 3
        assert assessment.avg_rerank_score > 0.8
        assert assessment.top_rerank_score == 0.92
        assert assessment.coverage_score > 0.0
    
    def test_assess_no_results(self, evidence_selector):
        """Test assessment with no results."""
        assessment = evidence_selector.assess_evidence(
            query="What is quantum computing?",
            retrieved_results=[]
        )
        
        assert assessment.is_sufficient is False
        assert "No relevant content found" in assessment.reason
        assert assessment.chunk_count == 0
        assert assessment.avg_rerank_score == 0.0
    
    def test_assess_insufficient_chunks(self, evidence_selector, sample_results):
        """Test assessment with too few chunks."""
        assessment = evidence_selector.assess_evidence(
            query="What is machine learning?",
            retrieved_results=sample_results[:1]  # Only 1 chunk
        )
        
        assert assessment.is_sufficient is False
        assert "Insufficient relevant content" in assessment.reason
        assert assessment.chunk_count == 1
    
    def test_assess_low_avg_score(self, evidence_selector):
        """Test assessment with low average scores."""
        low_score_results = [
            RetrievalResult(
                chunk_id="chunk_1",
                text="Some text here",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=0,
                is_parent=True,
                parent_id=None,
                dense_score=0.3,
                bm25_score=0.3,
                rrf_score=0.3,
                rerank_score=0.35,  # Low score
                final_score=0.35,
                payload={}
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                text="More text",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=1,
                is_parent=False,
                parent_id="chunk_1",
                dense_score=0.3,
                bm25_score=0.3,
                rrf_score=0.3,
                rerank_score=0.32,  # Low score
                final_score=0.32,
                payload={}
            ),
        ]
        
        assessment = evidence_selector.assess_evidence(
            query="test query",
            retrieved_results=low_score_results
        )
        
        assert assessment.is_sufficient is False
        assert "Low relevance scores" in assessment.reason
        assert assessment.avg_rerank_score < 0.4
    
    def test_assess_low_top_score(self, evidence_selector):
        """Test assessment with low top result score."""
        low_top_results = [
            RetrievalResult(
                chunk_id="chunk_1",
                text="Some relevant text about machine learning",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=0,
                is_parent=True,
                parent_id=None,
                dense_score=0.45,
                bm25_score=0.45,
                rrf_score=0.45,
                rerank_score=0.48,  # Below min_top_score (0.5)
                final_score=0.48,
                payload={}
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                text="More text about learning",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=1,
                is_parent=False,
                parent_id="chunk_1",
                dense_score=0.4,
                bm25_score=0.4,
                rrf_score=0.4,
                rerank_score=0.42,
                final_score=0.42,
                payload={}
            ),
        ]
        
        assessment = evidence_selector.assess_evidence(
            query="machine learning",
            retrieved_results=low_top_results
        )
        
        assert assessment.is_sufficient is False
        assert "Top result low confidence" in assessment.reason
        assert assessment.top_rerank_score < 0.5
    
    def test_assess_low_coverage(self, evidence_selector):
        """Test assessment with low query term coverage."""
        # Results that don't match query terms well
        unrelated_results = [
            RetrievalResult(
                chunk_id="chunk_1",
                text="Cats and dogs are animals",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=0,
                is_parent=True,
                parent_id=None,
                dense_score=0.8,
                bm25_score=0.8,
                rrf_score=0.8,
                rerank_score=0.85,
                final_score=0.85,
                payload={}
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                text="Birds can fly in the sky",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=1,
                is_parent=False,
                parent_id="chunk_1",
                dense_score=0.75,
                bm25_score=0.75,
                rrf_score=0.75,
                rerank_score=0.8,
                final_score=0.8,
                payload={}
            ),
        ]
        
        assessment = evidence_selector.assess_evidence(
            query="quantum mechanics and string theory",  # Completely unrelated
            retrieved_results=unrelated_results
        )
        
        assert assessment.is_sufficient is False
        assert "Low query term coverage" in assessment.reason
        assert assessment.coverage_score < 0.3
    
    def test_calculate_coverage_full(self, evidence_selector, sample_results):
        """Test coverage calculation with good overlap."""
        coverage = evidence_selector._calculate_coverage(
            query="machine learning artificial intelligence",
            retrieved_results=sample_results
        )
        
        # "machine", "learning", "artificial", "intelligence" should all be found
        assert coverage == 1.0
    
    def test_calculate_coverage_partial(self, evidence_selector, sample_results):
        """Test coverage calculation with partial overlap."""
        coverage = evidence_selector._calculate_coverage(
            query="machine learning quantum physics",
            retrieved_results=sample_results
        )
        
        # "machine" and "learning" found, but not "quantum" or "physics"
        assert 0.4 < coverage < 0.6  # 2 out of 4 terms
    
    def test_calculate_coverage_none(self, evidence_selector, sample_results):
        """Test coverage calculation with no overlap."""
        coverage = evidence_selector._calculate_coverage(
            query="unrelated completely different topic",
            retrieved_results=sample_results
        )
        
        assert coverage < 0.3
    
    def test_calculate_coverage_empty_query(self, evidence_selector, sample_results):
        """Test coverage calculation with empty query."""
        coverage = evidence_selector._calculate_coverage(
            query="",
            retrieved_results=sample_results
        )
        
        # Empty query = full coverage
        assert coverage == 1.0
    
    def test_select_best_chunks_no_filters(self, evidence_selector, sample_results):
        """Test selecting chunks without filters."""
        selected = evidence_selector.select_best_chunks(
            retrieved_results=sample_results
        )
        
        assert len(selected) == 3
        assert selected == sample_results
    
    def test_select_best_chunks_max_limit(self, evidence_selector, sample_results):
        """Test selecting chunks with max limit."""
        selected = evidence_selector.select_best_chunks(
            retrieved_results=sample_results,
            max_chunks=2
        )
        
        assert len(selected) == 2
        # Should take top 2
        assert selected[0].chunk_id == "chunk_1"
        assert selected[1].chunk_id == "chunk_2"
    
    def test_select_best_chunks_min_score(self, evidence_selector, sample_results):
        """Test selecting chunks with minimum score."""
        selected = evidence_selector.select_best_chunks(
            retrieved_results=sample_results,
            min_score=0.85
        )
        
        # Only chunks with rerank_score >= 0.85
        assert len(selected) == 2
        assert all(r.rerank_score >= 0.85 for r in selected)
    
    def test_select_best_chunks_both_filters(self, evidence_selector, sample_results):
        """Test selecting chunks with both filters."""
        selected = evidence_selector.select_best_chunks(
            retrieved_results=sample_results,
            max_chunks=2,
            min_score=0.85
        )
        
        # Max 2 chunks with score >= 0.85
        assert len(selected) == 2
        assert all(r.rerank_score >= 0.85 for r in selected)
    
    def test_select_best_chunks_empty_input(self, evidence_selector):
        """Test selecting chunks from empty list."""
        selected = evidence_selector.select_best_chunks(
            retrieved_results=[]
        )
        
        assert len(selected) == 0
    
    def test_fallback_to_final_score(self, evidence_selector):
        """Test that assessment falls back to final_score if no rerank_score."""
        results_without_rerank = [
            RetrievalResult(
                chunk_id="chunk_1",
                text="Some text",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=0,
                is_parent=True,
                parent_id=None,
                dense_score=0.8,
                bm25_score=0.8,
                rrf_score=0.8,
                rerank_score=None,  # No rerank score
                final_score=0.85,
                payload={}
            ),
            RetrievalResult(
                chunk_id="chunk_2",
                text="More text",
                doc_id="doc_1",
                doc_title="Doc",
                doc_path="/doc.md",
                section_path=[],
                chunk_index=1,
                is_parent=False,
                parent_id="chunk_1",
                dense_score=0.75,
                bm25_score=0.75,
                rrf_score=0.75,
                rerank_score=None,  # No rerank score
                final_score=0.8,
                payload={}
            ),
        ]
        
        assessment = evidence_selector.assess_evidence(
            query="text",
            retrieved_results=results_without_rerank
        )
        
        # Should use final_score
        assert assessment.avg_rerank_score > 0.8
        assert assessment.top_rerank_score == 0.85
    
    def test_get_evidence_selector_singleton(self):
        """Test that get_evidence_selector returns singleton."""
        selector1 = get_evidence_selector()
        selector2 = get_evidence_selector()
        
        assert selector1 is selector2
