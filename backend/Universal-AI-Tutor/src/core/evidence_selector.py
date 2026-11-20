"""
Evidence selector for Universal AI Tutor.

Determines if retrieved evidence is sufficient to answer a query.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

from src.core.retrieval_pipeline import RetrievalResult
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EvidenceAssessment:
    """Result of evidence sufficiency assessment."""
    
    is_sufficient: bool
    reason: str
    confidence_score: float
    coverage_score: float
    avg_rerank_score: float
    top_rerank_score: float
    chunk_count: int


class EvidenceSelector:
    """
    Assesses whether retrieved evidence is sufficient to answer a query.
    
    Implements criteria from RAG best practices:
    - Minimum chunk count (at least 2)
    - Minimum average rerank score (0.4)
    - Minimum top result score (0.5)
    - Query term coverage (at least 30%)
    """
    
    def __init__(
        self,
        min_chunks: int = 2,
        min_avg_score: float = -2.0,  # Calibrated for MiniLM cross-encoder (-10 to +10 range)
        min_top_score: float = -1.0,  # Top result should be reasonably relevant
        min_coverage: float = 0.3,
    ):
        """
        Initialize evidence selector.
        
        Args:
            min_chunks: Minimum number of chunks required
            min_avg_score: Minimum average rerank score (default -2.0 for MiniLM cross-encoder)
            min_top_score: Minimum score for top result (default -1.0 for MiniLM cross-encoder)
            min_coverage: Minimum query term coverage ratio
            
        Note:
            MiniLM cross-encoder scores range from approximately -10 to +10:
            - Scores > 2: High relevance
            - Scores 0-2: Moderate relevance
            - Scores -2 to 0: Low but useful relevance
            - Scores < -2: Likely not relevant
            
            Default thresholds are calibrated for this range to accept marginally relevant results.
        """
        self.min_chunks = min_chunks
        self.min_avg_score = min_avg_score
        self.min_top_score = min_top_score
        self.min_coverage = min_coverage
        
        logger.info(
            "EvidenceSelector initialized",
            extra={
                "min_chunks": min_chunks,
                "min_avg_score": min_avg_score,
                "min_top_score": min_top_score,
                "min_coverage": min_coverage,
            }
        )
    
    def assess_evidence(
        self,
        query: str,
        retrieved_results: List[RetrievalResult],
    ) -> EvidenceAssessment:
        """
        Assess whether retrieved evidence is sufficient to answer query.
        
        Args:
            query: Original query text
            retrieved_results: List of retrieval results with rerank scores
            
        Returns:
            EvidenceAssessment with sufficiency determination and metrics
        """
        # Check if we have any results
        if not retrieved_results:
            logger.warning("No retrieved results to assess")
            return EvidenceAssessment(
                is_sufficient=False,
                reason="No relevant content found",
                confidence_score=0.0,
                coverage_score=0.0,
                avg_rerank_score=0.0,
                top_rerank_score=0.0,
                chunk_count=0,
            )
        
        chunk_count = len(retrieved_results)
        
        # Check minimum chunk count
        if chunk_count < self.min_chunks:
            logger.info(
                f"Insufficient chunks: {chunk_count} < {self.min_chunks}",
                extra={"chunk_count": chunk_count}
            )
            return EvidenceAssessment(
                is_sufficient=False,
                reason=f"Insufficient relevant content ({chunk_count} chunks, need {self.min_chunks})",
                confidence_score=0.0,
                coverage_score=0.0,
                avg_rerank_score=0.0,
                top_rerank_score=0.0,
                chunk_count=chunk_count,
            )
        
        # Extract rerank scores
        rerank_scores = [
            r.rerank_score for r in retrieved_results 
            if r.rerank_score is not None
        ]
        
        if not rerank_scores:
            # No rerank scores available - fall back to final_score
            rerank_scores = [r.final_score for r in retrieved_results]
            logger.debug("Using final_score instead of rerank_score")
        
        avg_score = sum(rerank_scores) / len(rerank_scores)
        top_score = rerank_scores[0] if rerank_scores else 0.0
        
        # Check average confidence
        if avg_score < self.min_avg_score:
            logger.info(
                f"Low average relevance: {avg_score:.2f} < {self.min_avg_score}",
                extra={"avg_score": avg_score}
            )
            return EvidenceAssessment(
                is_sufficient=False,
                reason=f"Low relevance scores (avg: {avg_score:.2f}, need {self.min_avg_score})",
                confidence_score=top_score,
                coverage_score=0.0,
                avg_rerank_score=avg_score,
                top_rerank_score=top_score,
                chunk_count=chunk_count,
            )
        
        # Check top result confidence
        if top_score < self.min_top_score:
            logger.info(
                f"Low top result score: {top_score:.2f} < {self.min_top_score}",
                extra={"top_score": top_score}
            )
            return EvidenceAssessment(
                is_sufficient=False,
                reason=f"Top result low confidence: {top_score:.2f} (need {self.min_top_score})",
                confidence_score=top_score,
                coverage_score=0.0,
                avg_rerank_score=avg_score,
                top_rerank_score=top_score,
                chunk_count=chunk_count,
            )
        
        # Check query term coverage
        coverage = self._calculate_coverage(query, retrieved_results)
        
        if coverage < self.min_coverage:
            logger.info(
                f"Low query coverage: {coverage:.2f} < {self.min_coverage}",
                extra={"coverage": coverage}
            )
            return EvidenceAssessment(
                is_sufficient=False,
                reason=f"Low query term coverage: {coverage:.2%} (need {self.min_coverage:.0%})",
                confidence_score=top_score,
                coverage_score=coverage,
                avg_rerank_score=avg_score,
                top_rerank_score=top_score,
                chunk_count=chunk_count,
            )
        
        # All checks passed
        logger.info(
            "Evidence is sufficient",
            extra={
                "chunk_count": chunk_count,
                "avg_score": avg_score,
                "top_score": top_score,
                "coverage": coverage,
            }
        )
        
        return EvidenceAssessment(
            is_sufficient=True,
            reason="Evidence appears sufficient",
            confidence_score=top_score,
            coverage_score=coverage,
            avg_rerank_score=avg_score,
            top_rerank_score=top_score,
            chunk_count=chunk_count,
        )
    
    def _calculate_coverage(
        self,
        query: str,
        retrieved_results: List[RetrievalResult]
    ) -> float:
        """
        Calculate query term coverage in retrieved results.
        
        Coverage = (query terms found in results) / (total query terms)
        
        Args:
            query: Query text
            retrieved_results: Retrieved chunks
            
        Returns:
            Coverage ratio (0.0 to 1.0)
        """
        # Normalize and tokenize query
        query_terms = set(query.lower().split())
        
        # Collect all terms from results
        result_terms = set()
        for result in retrieved_results:
            result_terms.update(result.text.lower().split())
        
        # Calculate coverage
        if not query_terms:
            return 1.0  # Empty query = full coverage
        
        matched_terms = query_terms & result_terms
        coverage = len(matched_terms) / len(query_terms)
        
        logger.debug(
            f"Coverage calculation",
            extra={
                "query_terms": len(query_terms),
                "matched_terms": len(matched_terms),
                "coverage": coverage,
            }
        )
        
        return coverage
    
    def select_best_chunks(
        self,
        retrieved_results: List[RetrievalResult],
        max_chunks: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """
        Select the best chunks from retrieved results.
        
        Args:
            retrieved_results: List of retrieval results
            max_chunks: Maximum number of chunks to select
            min_score: Minimum rerank score threshold
            
        Returns:
            Filtered list of best chunks
        """
        if not retrieved_results:
            return []
        
        # Filter by minimum score if specified
        if min_score is not None:
            filtered = [
                r for r in retrieved_results
                if (r.rerank_score and r.rerank_score >= min_score) or
                   (r.final_score >= min_score)
            ]
            logger.debug(
                f"Filtered by min_score={min_score}: {len(filtered)}/{len(retrieved_results)} chunks"
            )
        else:
            filtered = retrieved_results
        
        # Take top-k if specified
        if max_chunks is not None and len(filtered) > max_chunks:
            filtered = filtered[:max_chunks]
            logger.debug(f"Selected top {max_chunks} chunks")
        
        return filtered


# Singleton instance
_evidence_selector_instance: Optional[EvidenceSelector] = None


def get_evidence_selector(**kwargs) -> EvidenceSelector:
    """
    Get EvidenceSelector instance (singleton).
    
    Args:
        **kwargs: Configuration parameters for EvidenceSelector
        
    Returns:
        EvidenceSelector instance
    """
    global _evidence_selector_instance
    
    if _evidence_selector_instance is None:
        logger.info("Creating global EvidenceSelector instance")
        _evidence_selector_instance = EvidenceSelector(**kwargs)
    
    return _evidence_selector_instance
