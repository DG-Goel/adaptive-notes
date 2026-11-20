"""
Unit tests for RAG evaluation metrics.

Tests retrieval and answer quality metrics.
"""

import pytest
from src.evaluation.metrics import (
    RAGEvaluator,
    get_evaluator,
    RetrievalMetrics,
    AnswerMetrics,
    EvaluationResult,
)
from src.core.retrieval_pipeline import RetrievalResult


@pytest.fixture
def evaluator():
    """Provide RAGEvaluator instance."""
    return RAGEvaluator()


@pytest.fixture
def sample_retrieval_results():
    """Provide sample retrieval results."""
    return [
        RetrievalResult(
            chunk_id="chunk_1",
            text="Machine learning is AI",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/ml.md",
            section_path=["Intro"],
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
            text="Supervised learning uses labels",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/ml.md",
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
            text="Deep learning uses neural networks",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/ml.md",
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


class TestRetrievalMetrics:
    """Test retrieval evaluation metrics."""
    
    def test_perfect_retrieval(self, evaluator, sample_retrieval_results):
        """Test metrics when all relevant docs are retrieved."""
        relevant_ids = ["chunk_1", "chunk_2", "chunk_3"]
        
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=sample_retrieval_results,
            relevant_doc_ids=relevant_ids,
            k=5
        )
        
        assert metrics.recall_at_k == 1.0  # All relevant docs found
        assert metrics.precision_at_k == 1.0  # All retrieved docs are relevant
        assert metrics.mrr == 1.0  # First doc is relevant
        assert metrics.retrieved_count == 3
        assert metrics.avg_score > 0.8
    
    def test_partial_retrieval(self, evaluator, sample_retrieval_results):
        """Test metrics when only some relevant docs are retrieved."""
        relevant_ids = ["chunk_1", "chunk_4", "chunk_5"]  # Only chunk_1 is retrieved
        
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=sample_retrieval_results,
            relevant_doc_ids=relevant_ids,
            k=5
        )
        
        assert metrics.recall_at_k == 1.0 / 3.0  # 1 out of 3 relevant docs found
        assert metrics.precision_at_k == 1.0 / 3.0  # 1 out of 3 retrieved docs is relevant
        assert metrics.mrr == 1.0  # First doc is relevant
    
    def test_no_relevant_retrieved(self, evaluator, sample_retrieval_results):
        """Test metrics when no relevant docs are retrieved."""
        relevant_ids = ["chunk_99", "chunk_100"]  # None are retrieved
        
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=sample_retrieval_results,
            relevant_doc_ids=relevant_ids,
            k=5
        )
        
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.mrr == 0.0
    
    def test_mrr_calculation(self, evaluator, sample_retrieval_results):
        """Test MRR when relevant doc is not first."""
        relevant_ids = ["chunk_2"]  # Second result is relevant
        
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=sample_retrieval_results,
            relevant_doc_ids=relevant_ids,
            k=5
        )
        
        assert metrics.mrr == 1.0 / 2.0  # Reciprocal of rank 2
    
    def test_empty_results(self, evaluator):
        """Test metrics with no retrieved results."""
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=[],
            relevant_doc_ids=["chunk_1"],
            k=5
        )
        
        assert metrics.recall_at_k == 0.0
        assert metrics.precision_at_k == 0.0
        assert metrics.mrr == 0.0
        assert metrics.retrieved_count == 0
    
    def test_top_k_limit(self, evaluator, sample_retrieval_results):
        """Test that only top-k results are evaluated."""
        relevant_ids = ["chunk_1", "chunk_2"]
        
        metrics = evaluator.evaluate_retrieval(
            retrieved_results=sample_retrieval_results,
            relevant_doc_ids=relevant_ids,
            k=2  # Only evaluate first 2
        )
        
        assert metrics.retrieved_count == 2


class TestAnswerMetrics:
    """Test answer quality metrics."""
    
    def test_well_grounded_answer_strict(self, evaluator):
        """Test metrics for well-grounded answer in strict mode."""
        answer = "Based on your notes: Machine learning is a subset of AI that uses data. [Source: ML Guide]"
        chunks = [
            {"text": "Machine learning is a subset of artificial intelligence that uses data to learn patterns"}
        ]
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="strict"
        )
        
        assert metrics.has_citations is True
        assert metrics.groundedness_score > 0.4  # Reasonable overlap expected
        assert metrics.answer_length > 0
        assert metrics.token_count > 0
        assert metrics.contains_admission is False
    
    def test_answer_without_citations(self, evaluator):
        """Test answer missing citations in strict mode."""
        answer = "Machine learning is great for solving problems"
        chunks = [{"text": "ML solves problems"}]
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="strict"
        )
        
        assert metrics.has_citations is False
    
    def test_answer_with_admission(self, evaluator):
        """Test answer that admits insufficient information."""
        answer = "I don't have enough information in your notes to answer this question."
        chunks = []
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="strict"
        )
        
        assert metrics.contains_admission is True
        assert metrics.groundedness_score >= 0.0
    
    def test_teaching_mode_flexibility(self, evaluator):
        """Test that teaching mode is more flexible with citations."""
        answer = "From your notes: ML is AI. To help understand, think of it as..."
        chunks = [{"text": "ML is AI"}]
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="teaching"
        )
        
        assert metrics.has_citations is True
    
    def test_empty_answer(self, evaluator):
        """Test metrics for empty answer."""
        metrics = evaluator.evaluate_answer(
            answer="",
            retrieved_chunks=[],
            mode="strict"
        )
        
        assert metrics.answer_length == 0
        assert metrics.token_count == 0
        assert metrics.groundedness_score == 0.0
    
    def test_groundedness_with_overlap(self, evaluator):
        """Test groundedness calculation with good overlap."""
        answer = "machine learning uses data to train models"
        chunks = [
            {"text": "machine learning is a technique that uses data to train predictive models"}
        ]
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="strict"
        )
        
        # Should have high overlap
        assert metrics.groundedness_score > 0.7
    
    def test_groundedness_without_overlap(self, evaluator):
        """Test groundedness with no overlap."""
        answer = "quantum computing enables superposition"
        chunks = [
            {"text": "machine learning uses neural networks"}
        ]
        
        metrics = evaluator.evaluate_answer(
            answer=answer,
            retrieved_chunks=chunks,
            mode="strict"
        )
        
        # Should have low overlap
        assert metrics.groundedness_score < 0.3


class TestEndToEndEvaluation:
    """Test complete end-to-end evaluation."""
    
    def test_complete_evaluation(self, evaluator, sample_retrieval_results):
        """Test full pipeline evaluation."""
        question = "What is machine learning?"
        answer = "Based on your notes: Machine learning is AI. [Source: ML Guide]"
        chunks = [{"text": "Machine learning is AI"}]
        relevant_ids = ["chunk_1", "chunk_2"]
        
        result = evaluator.evaluate_end_to_end(
            question=question,
            retrieved_results=sample_retrieval_results,
            answer=answer,
            retrieved_chunks=chunks,
            relevant_doc_ids=relevant_ids,
            mode="strict"
        )
        
        assert isinstance(result, EvaluationResult)
        assert result.question == question
        assert isinstance(result.retrieval_metrics, RetrievalMetrics)
        assert isinstance(result.answer_metrics, AnswerMetrics)
        assert "mode" in result.metadata
        assert result.metadata["mode"] == "strict"
    
    def test_evaluation_with_poor_retrieval(self, evaluator, sample_retrieval_results):
        """Test evaluation when retrieval fails."""
        question = "What is quantum computing?"
        answer = "I don't have enough information in your notes to answer this question."
        chunks = []
        relevant_ids = ["chunk_99"]  # Not retrieved
        
        result = evaluator.evaluate_end_to_end(
            question=question,
            retrieved_results=sample_retrieval_results,
            answer=answer,
            retrieved_chunks=chunks,
            relevant_doc_ids=relevant_ids,
            mode="strict"
        )
        
        assert result.retrieval_metrics.recall_at_k == 0.0
        assert result.answer_metrics.contains_admission is True


class TestAggregateMetrics:
    """Test metric aggregation."""
    
    def test_aggregate_multiple_results(self, evaluator, sample_retrieval_results):
        """Test aggregating metrics across multiple evaluations."""
        # Create multiple evaluation results
        results = []
        for i in range(3):
            result = evaluator.evaluate_end_to_end(
                question=f"Question {i}",
                retrieved_results=sample_retrieval_results,
                answer=f"Answer {i} from notes [Source: Doc]",
                retrieved_chunks=[{"text": f"Content {i}"}],
                relevant_doc_ids=["chunk_1"],
                mode="strict"
            )
            results.append(result)
        
        aggregated = evaluator.aggregate_metrics(results)
        
        assert "avg_recall_at_5" in aggregated
        assert "avg_precision_at_5" in aggregated
        assert "avg_mrr" in aggregated
        assert "avg_groundedness" in aggregated
        assert "citation_rate" in aggregated
        assert "admission_rate" in aggregated
        assert "total_evaluations" in aggregated
        assert aggregated["total_evaluations"] == 3
    
    def test_aggregate_empty_list(self, evaluator):
        """Test aggregating empty results list."""
        aggregated = evaluator.aggregate_metrics([])
        
        assert aggregated == {}
    
    def test_aggregate_citation_rate(self, evaluator, sample_retrieval_results):
        """Test citation rate calculation."""
        # Create results with varying citation presence
        results = [
            evaluator.evaluate_end_to_end(
                question="Q1",
                retrieved_results=sample_retrieval_results,
                answer="Answer with [Source: Doc]",
                retrieved_chunks=[{"text": "Content"}],
                relevant_doc_ids=["chunk_1"],
                mode="strict"
            ),
            evaluator.evaluate_end_to_end(
                question="Q2",
                retrieved_results=sample_retrieval_results,
                answer="Answer without citation",
                retrieved_chunks=[{"text": "Content"}],
                relevant_doc_ids=["chunk_1"],
                mode="strict"
            ),
        ]
        
        aggregated = evaluator.aggregate_metrics(results)
        
        # 1 out of 2 has citations
        assert aggregated["citation_rate"] == 0.5


class TestEvaluatorSingleton:
    """Test evaluator singleton pattern."""
    
    def test_get_evaluator_singleton(self):
        """Test that get_evaluator returns singleton."""
        evaluator1 = get_evaluator()
        evaluator2 = get_evaluator()
        
        assert evaluator1 is evaluator2
