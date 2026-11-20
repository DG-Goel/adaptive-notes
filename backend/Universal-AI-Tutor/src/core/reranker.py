"""
Cross-encoder reranker for Universal AI Tutor.

Uses MiniLM cross-encoder to rerank retrieved chunks based on query relevance.
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from sentence_transformers import CrossEncoder

from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RerankResult:
    """Result from reranking operation."""
    
    chunk_id: str
    text: str
    original_score: float
    rerank_score: float
    payload: dict


class RerankerService:
    """
    Cross-encoder reranker for improving retrieval quality.
    
    Uses a cross-encoder model to rerank retrieved chunks based on
    query-document relevance. More accurate than bi-encoder similarity
    but more computationally expensive (only used on top-k results).
    
    Model: ms-marco-MiniLM-L-6-v2
    - Trained on MS MARCO passage ranking dataset
    - 6-layer MiniLM architecture
    - Fast inference (~50ms per pair on CPU)
    - Output: relevance score (higher = more relevant)
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize reranker service.
        
        Args:
            model_name: Cross-encoder model name (default from config)
            device: Device to use ('cpu' or 'cuda', default from config)
        """
        settings = get_settings()
        
        self.model_name = model_name or settings.reranker_model
        self.device = device or settings.embedding_device  # Reuse embedding device
        
        logger.info(
            f"Initializing RerankerService",
            extra={
                "model": self.model_name,
                "device": self.device,
            },
        )
        
        try:
            self.model = CrossEncoder(self.model_name, device=self.device)
            
            logger.info("RerankerService initialized successfully")
            
        except Exception as e:
            logger.error(
                f"Failed to initialize reranker model: {e}",
                exc_info=True
            )
            raise RuntimeError(
                f"Failed to load reranker model '{self.model_name}': {str(e)}"
            ) from e
    
    def rerank(
        self,
        query: str,
        chunks: List[dict],
        top_k: Optional[int] = None,
        return_all: bool = False
    ) -> List[RerankResult]:
        """
        Rerank chunks based on cross-encoder relevance scores.
        
        Args:
            query: Search query
            chunks: List of chunk dictionaries with 'text' and metadata
            top_k: Number of top results to return (default: return all)
            return_all: If True, return all chunks reranked (default: False)
            
        Returns:
            List of RerankResult objects sorted by rerank_score (descending)
            
        Raises:
            ValueError: If query is empty or chunks list is empty
            RuntimeError: If reranking fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not chunks:
            raise ValueError("Chunks list cannot be empty")
        
        try:
            # Prepare query-document pairs
            pairs = []
            chunk_data = []
            
            for chunk in chunks:
                # Extract text - support both dict and object formats
                if isinstance(chunk, dict):
                    text = chunk.get("text", "")
                    chunk_id = chunk.get("chunk_id", chunk.get("id", ""))
                    original_score = chunk.get("score", 0.0)
                    payload = chunk
                else:
                    # Assume it's a search result object
                    text = chunk.payload.get("text", "")
                    chunk_id = chunk.payload.get("chunk_id", str(chunk.id))
                    original_score = chunk.score if hasattr(chunk, 'score') else 0.0
                    payload = chunk.payload
                
                if not text:
                    logger.warning(f"Skipping chunk with no text: {chunk_id}")
                    continue
                
                pairs.append([query, text])
                chunk_data.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "original_score": original_score,
                    "payload": payload
                })
            
            if not pairs:
                logger.warning("No valid chunks to rerank")
                return []
            
            logger.info(
                f"Reranking chunks",
                extra={
                    "query_length": len(query),
                    "num_chunks": len(pairs),
                },
            )
            
            # Get cross-encoder scores
            scores = self.model.predict(pairs)
            
            # Combine scores with chunk data
            results = []
            for chunk_info, rerank_score in zip(chunk_data, scores):
                results.append(
                    RerankResult(
                        chunk_id=chunk_info["chunk_id"],
                        text=chunk_info["text"],
                        original_score=chunk_info["original_score"],
                        rerank_score=float(rerank_score),
                        payload=chunk_info["payload"]
                    )
                )
            
            # Sort by rerank score (descending)
            results.sort(key=lambda x: x.rerank_score, reverse=True)
            
            # Apply top_k if specified
            if top_k is not None and top_k > 0 and not return_all:
                results = results[:top_k]
            
            logger.info(
                f"Reranking complete",
                extra={
                    "results_count": len(results),
                    "top_score": results[0].rerank_score if results else 0,
                },
            )
            
            return results
            
        except Exception as e:
            logger.error(
                f"Reranking failed",
                extra={"query": query, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Reranking failed: {str(e)}") from e
    
    def rerank_search_results(
        self,
        query: str,
        search_results: List,
        top_k: int = 5
    ) -> List[RerankResult]:
        """
        Convenience method to rerank search results from VectorStore.
        
        Args:
            query: Search query
            search_results: Results from VectorStore search methods
            top_k: Number of top results to return after reranking
            
        Returns:
            Top-k reranked results
        """
        return self.rerank(query, search_results, top_k=top_k)


# Global singleton instance
_reranker_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """
    Get singleton reranker service instance.
    
    Returns:
        RerankerService: Global reranker service instance
        
    Note:
        Service is initialized lazily on first call.
        Model loading happens once and is reused across the application.
    """
    global _reranker_service
    
    if _reranker_service is None:
        logger.info("Creating global RerankerService instance")
        _reranker_service = RerankerService()
    
    return _reranker_service
