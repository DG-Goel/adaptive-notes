"""
RAG evaluation metrics.

Provides metrics for assessing retrieval and generation quality.
"""

import logging
from typing import List, Dict, Any, Set
from dataclasses import dataclass

from src.core.retrieval_pipeline import RetrievalResult
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality."""
    
    recall_at_k: float
    """Proportion of relevant docs retrieved"""
    
    precision_at_k: float
    """Proportion of retrieved docs that are relevant"""
    
    mrr: float
    """Mean Reciprocal Rank of first relevant doc"""
    
    avg_score: float
    """Average relevance score of retrieved docs"""
    
    retrieved_count: int
    """Number of documents retrieved"""


@dataclass
class AnswerMetrics:
    """Metrics for answer quality."""
    
    groundedness_score: float
    """How well answer is grounded in sources (0.0-1.0)"""
    
    has_citations: bool
    """Whether answer includes citations"""
    
    answer_length: int
    """Length of answer in characters"""
    
    token_count: int
    """Estimated token count"""
    
    contains_admission: bool
    """Whether answer admits insufficient information"""


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    
    question: str
    retrieval_metrics: RetrievalMetrics
    answer_metrics: AnswerMetrics
    metadata: Dict[str, Any]


class RAGEvaluator:
    """
    Evaluates RAG system performance.
    
    Provides metrics for:
    - Retrieval quality (recall, precision, MRR)
    - Answer quality (groundedness, citations)
    - End-to-end performance
    """
    
    def __init__(self):
        """Initialize RAG evaluator."""
        logger.info("RAGEvaluator initialized")
    
    def evaluate_retrieval(
        self,
        retrieved_results: List[RetrievalResult],
        relevant_doc_ids: List[str],
        k: int = 5
    ) -> RetrievalMetrics:
        """
        Evaluate retrieval quality against ground truth.
        
        Args:
            retrieved_results: Retrieved documents
            relevant_doc_ids: IDs of documents that should be retrieved
            k: Top-k to evaluate
            
        Returns:
            RetrievalMetrics with recall, precision, MRR
        """
        if not retrieved_results:
            logger.warning("No retrieved results to evaluate")
            return RetrievalMetrics(
                recall_at_k=0.0,
                precision_at_k=0.0,
                mrr=0.0,
                avg_score=0.0,
                retrieved_count=0
            )
        
        # Take top-k results
        top_k_results = retrieved_results[:k]
        retrieved_ids = {r.chunk_id for r in top_k_results}
        relevant_ids = set(relevant_doc_ids)
        
        # Calculate recall@k
        relevant_retrieved = retrieved_ids & relevant_ids
        recall = len(relevant_retrieved) / len(relevant_ids) if relevant_ids else 1.0
        
        # Calculate precision@k
        precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0.0
        
        # Calculate MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, result in enumerate(top_k_results, 1):
            if result.chunk_id in relevant_ids:
                mrr = 1.0 / i
                break
        
        # Calculate average score
        avg_score = sum(r.final_score for r in top_k_results) / len(top_k_results)
        
        logger.info(
            f"Retrieval metrics: recall={recall:.2f}, precision={precision:.2f}, MRR={mrr:.2f}",
            extra={
                "recall": recall,
                "precision": precision,
                "mrr": mrr,
                "avg_score": avg_score
            }
        )
        
        return RetrievalMetrics(
            recall_at_k=recall,
            precision_at_k=precision,
            mrr=mrr,
            avg_score=avg_score,
            retrieved_count=len(top_k_results)
        )
    
    def evaluate_answer(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        mode: str = "strict"
    ) -> AnswerMetrics:
        """
        Evaluate answer quality.
        
        Checks groundedness, citations, and completeness.
        
        Args:
            answer: Generated answer
            retrieved_chunks: Source chunks used for generation
            mode: Generation mode (strict or teaching)
            
        Returns:
            AnswerMetrics with quality scores
        """
        if not answer:
            logger.warning("Empty answer provided for evaluation")
            return AnswerMetrics(
                groundedness_score=0.0,
                has_citations=False,
                answer_length=0,
                token_count=0,
                contains_admission=False
            )
        
        # Check for citations
        has_citations = self._check_citations(answer, mode)
        
        # Check groundedness (simple heuristic for MVP)
        groundedness = self._estimate_groundedness(answer, retrieved_chunks)
        
        # Check if answer admits insufficient information
        contains_admission = self._check_admission(answer)
        
        # Calculate lengths
        answer_length = len(answer)
        token_count = len(answer.split())  # Simple word count estimate
        
        logger.info(
            f"Answer metrics: groundedness={groundedness:.2f}, citations={has_citations}",
            extra={
                "groundedness": groundedness,
                "has_citations": has_citations,
                "length": answer_length,
                "tokens": token_count
            }
        )
        
        return AnswerMetrics(
            groundedness_score=groundedness,
            has_citations=has_citations,
            answer_length=answer_length,
            token_count=token_count,
            contains_admission=contains_admission
        )
    
    def _check_citations(self, answer: str, mode: str) -> bool:
        """Check if answer contains citations."""
        citation_indicators = [
            "[Source:",
            "From your notes",
            "Based on your notes",
            "According to",
            "[Document",
        ]
        
        if mode == "strict":
            # Strict mode should have explicit citations
            return any(indicator in answer for indicator in citation_indicators)
        else:
            # Teaching mode is more flexible
            return any(indicator in answer for indicator in citation_indicators[:3])
    
    def _estimate_groundedness(
        self,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> float:
        """
        Estimate how well answer is grounded in sources.
        
        Simple heuristic: checks for word overlap between answer and sources.
        For production, use NLI models for better accuracy.
        """
        if not retrieved_chunks:
            return 0.0
        
        answer_lower = answer.lower()
        answer_words = set(answer_lower.split())
        
        # Collect words from sources
        source_words: Set[str] = set()
        for chunk in retrieved_chunks:
            chunk_text = chunk.get("text", "")
            source_words.update(chunk_text.lower().split())
        
        # Calculate overlap
        if not answer_words:
            return 0.0
        
        overlap = answer_words & source_words
        groundedness = len(overlap) / len(answer_words)
        
        # Cap at 1.0
        return min(groundedness, 1.0)
    
    def _check_admission(self, answer: str) -> bool:
        """Check if answer admits insufficient information."""
        admission_phrases = [
            "don't have enough information",
            "insufficient information",
            "not enough information",
            "cannot answer",
            "can't answer"
        ]
        
        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in admission_phrases)
    
    def evaluate_end_to_end(
        self,
        question: str,
        retrieved_results: List[RetrievalResult],
        answer: str,
        retrieved_chunks: List[Dict[str, Any]],
        relevant_doc_ids: List[str],
        mode: str = "strict"
    ) -> EvaluationResult:
        """
        Evaluate complete RAG pipeline.
        
        Combines retrieval and answer metrics.
        
        Args:
            question: User question
            retrieved_results: Retrieved documents
            answer: Generated answer
            retrieved_chunks: Chunks used for generation
            relevant_doc_ids: Ground truth relevant docs
            mode: Generation mode
            
        Returns:
            EvaluationResult with all metrics
        """
        # Evaluate retrieval
        retrieval_metrics = self.evaluate_retrieval(
            retrieved_results=retrieved_results,
            relevant_doc_ids=relevant_doc_ids,
            k=5
        )
        
        # Evaluate answer
        answer_metrics = self.evaluate_answer(
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            mode=mode
        )
        
        logger.info(
            f"End-to-end evaluation complete",
            extra={
                "question": question[:50],
                "recall": retrieval_metrics.recall_at_k,
                "groundedness": answer_metrics.groundedness_score
            }
        )
        
        return EvaluationResult(
            question=question,
            retrieval_metrics=retrieval_metrics,
            answer_metrics=answer_metrics,
            metadata={
                "mode": mode,
                "relevant_docs_count": len(relevant_doc_ids)
            }
        )
    
    def aggregate_metrics(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, float]:
        """
        Aggregate metrics across multiple evaluations.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary with averaged metrics
        """
        if not results:
            return {}
        
        n = len(results)
        
        aggregated = {
            "avg_recall_at_5": sum(r.retrieval_metrics.recall_at_k for r in results) / n,
            "avg_precision_at_5": sum(r.retrieval_metrics.precision_at_k for r in results) / n,
            "avg_mrr": sum(r.retrieval_metrics.mrr for r in results) / n,
            "avg_groundedness": sum(r.answer_metrics.groundedness_score for r in results) / n,
            "citation_rate": sum(1 for r in results if r.answer_metrics.has_citations) / n,
            "admission_rate": sum(1 for r in results if r.answer_metrics.contains_admission) / n,
            "avg_answer_length": sum(r.answer_metrics.answer_length for r in results) / n,
            "total_evaluations": n
        }
        
        logger.info(
            f"Aggregated metrics over {n} evaluations",
            extra=aggregated
        )
        
        return aggregated


# Singleton instance
_evaluator_instance = None


def get_evaluator() -> RAGEvaluator:
    """
    Get RAGEvaluator instance (singleton).
    
    Returns:
        RAGEvaluator instance
    """
    global _evaluator_instance
    
    if _evaluator_instance is None:
        logger.info("Creating global RAGEvaluator instance")
        _evaluator_instance = RAGEvaluator()
    
    return _evaluator_instance
