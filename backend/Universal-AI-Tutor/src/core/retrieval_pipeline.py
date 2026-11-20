"""
Retrieval pipeline for Universal AI Tutor.

Orchestrates hybrid retrieval: dense + BM25 + RRF fusion + reranking.
"""

import logging
from typing import List, Optional, Literal
from dataclasses import dataclass

from src.core.embedding_service import get_embedding_service
from src.core.vector_store import get_vector_store
from src.core.reranker import get_reranker_service, RerankResult
from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Result from retrieval pipeline."""
    
    chunk_id: str
    text: str
    doc_id: str
    doc_title: str
    doc_path: str
    section_path: List[str]
    chunk_index: int
    is_parent: bool
    parent_id: Optional[str]
    
    # Scores
    dense_score: Optional[float]
    bm25_score: Optional[float]
    rrf_score: Optional[float]
    rerank_score: Optional[float]
    final_score: float
    
    # Full payload for context expansion
    payload: dict


class RetrievalPipeline:
    """
    Hybrid retrieval pipeline with reranking.
    
    Pipeline stages:
    1. Dense vector search (bi-encoder similarity)
    2. BM25 full-text search (keyword matching)
    3. RRF fusion (combine signals with reciprocal rank fusion)
    4. Cross-encoder reranking (accurate relevance scoring)
    5. Parent context expansion (optional, for child chunks)
    
    Configuration:
    - dense_top_k: Number of dense results (default: 20)
    - bm25_top_k: Number of BM25 results (default: 20)
    - rrf_k: RRF parameter (default: 60)
    - rerank_top_k: Final number of results after reranking (default: 5)
    """
    
    def __init__(
        self,
        collection_name: str = "tutor_knowledge",
        dense_top_k: Optional[int] = None,
        bm25_top_k: Optional[int] = None,
        rrf_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None,
        use_reranking: bool = True,
    ):
        """
        Initialize retrieval pipeline.
        
        Args:
            collection_name: Qdrant collection name
            dense_top_k: Number of dense search results
            bm25_top_k: Number of BM25 search results
            rrf_k: RRF fusion parameter
            rerank_top_k: Number of final results after reranking
            use_reranking: Whether to use cross-encoder reranking
        """
        settings = get_settings()
        
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.reranker_service = get_reranker_service() if use_reranking else None
        
        self.collection_name = collection_name
        self.dense_top_k = dense_top_k or settings.dense_top_k
        self.bm25_top_k = bm25_top_k or settings.bm25_top_k
        self.rrf_k = rrf_k or settings.rrf_k
        self.rerank_top_k = rerank_top_k or settings.rerank_top_k
        self.use_reranking = use_reranking
        
        logger.info(
            "RetrievalPipeline initialized",
            extra={
                "collection": collection_name,
                "dense_top_k": self.dense_top_k,
                "bm25_top_k": self.bm25_top_k,
                "rerank_top_k": self.rerank_top_k,
                "use_reranking": use_reranking,
            }
        )
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        method: Literal["hybrid", "dense", "bm25"] = "hybrid",
        use_reranking: Optional[bool] = None,
        doc_path: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of final results (default: rerank_top_k)
            method: Retrieval method - "hybrid", "dense", or "bm25"
            use_reranking: Override reranking setting for this query
            
        Returns:
            List of RetrievalResult objects sorted by relevance
            
        Raises:
            ValueError: If query is empty
            RuntimeError: If retrieval fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        top_k = top_k or self.rerank_top_k
        should_rerank = use_reranking if use_reranking is not None else self.use_reranking
        
        try:
            logger.info(
                f"Starting retrieval",
                extra={
                    "query_length": len(query),
                    "method": method,
                    "top_k": top_k,
                    "use_reranking": should_rerank,
                }
            )
            
            # Stage 1-3: Get search results (method-dependent)
            if doc_path is not None:
                from qdrant_client import models
                scope = models.Filter(must=[models.FieldCondition(
                    key="doc_path", match=models.MatchValue(value=doc_path))])
                search_results = self._hybrid_search(query, scope)
            elif method == "dense":
                search_results = self._dense_only(query)
            elif method == "bm25":
                search_results = self._bm25_only(query)
            else:  # hybrid
                search_results = self._hybrid_search(query)
            
            if not search_results:
                logger.warning("No search results found")
                return []
            
            logger.info(
                f"Retrieved {len(search_results)} results before reranking"
            )
            
            # Stage 4: Reranking (optional)
            if should_rerank and self.reranker_service:
                reranked = self._rerank_results(query, search_results, top_k)
                final_results = reranked
            else:
                # Skip reranking, just take top-k by search score
                final_results = search_results[:top_k]
            
            # Stage 5: Convert to RetrievalResult objects
            retrieval_results = self._convert_to_retrieval_results(
                final_results,
                method=method,
                was_reranked=should_rerank
            )
            
            logger.info(
                f"Retrieval complete",
                extra={
                    "final_count": len(retrieval_results),
                    "top_score": retrieval_results[0].final_score if retrieval_results else 0,
                }
            )
            
            return retrieval_results
            
        except Exception as e:
            logger.error(
                f"Retrieval failed",
                extra={"query": query, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Retrieval failed: {str(e)}") from e
    
    def _dense_only(self, query: str) -> List:
        """Perform dense vector search only."""
        query_embedding = self.embedding_service.embed(query)
        
        results = self.vector_store.dense_search(
            query_vector=query_embedding,
            top_k=self.dense_top_k
        )
        
        logger.debug(f"Dense search returned {len(results)} results")
        return results
    
    def _bm25_only(self, query: str) -> List:
        """Perform BM25 full-text search only."""
        results = self.vector_store.bm25_search(
            query_text=query,
            top_k=self.bm25_top_k
        )
        
        logger.debug(f"BM25 search returned {len(results)} results")
        return results
    
    def _hybrid_search(self, query: str, scope=None) -> List:
        """Perform hybrid search with RRF fusion."""
        query_embedding = self.embedding_service.embed(query)
        
        results = self.vector_store.hybrid_search(
            query_text=query,
            query_vector=query_embedding,
            dense_top_k=self.dense_top_k,
            bm25_top_k=self.bm25_top_k,
            top_k=self.dense_top_k,  # Return combined top-k
            **({'filter': scope} if scope is not None else {}),
        )
        
        logger.debug(f"Hybrid search returned {len(results)} results")
        return results
    
    def _rerank_results(
        self,
        query: str,
        search_results: List,
        top_k: int
    ) -> List[RerankResult]:
        """Apply cross-encoder reranking."""
        reranked = self.reranker_service.rerank(
            query=query,
            chunks=search_results,
            top_k=top_k
        )
        
        logger.debug(
            f"Reranked to {len(reranked)} results",
            extra={
                "top_score": reranked[0].rerank_score if reranked else 0
            }
        )
        
        return reranked
    
    def _convert_to_retrieval_results(
        self,
        results: List,
        method: str,
        was_reranked: bool
    ) -> List[RetrievalResult]:
        """Convert search/rerank results to RetrievalResult objects."""
        retrieval_results = []
        
        for result in results:
            # Handle both RerankResult and search result objects
            if isinstance(result, RerankResult):
                payload = result.payload
                final_score = result.rerank_score
                rerank_score = result.rerank_score
                original_score = result.original_score
            else:
                payload = result.payload
                final_score = result.score
                rerank_score = None
                original_score = result.score
            
            # Extract metadata
            chunk_id = payload.get("chunk_id", "")
            doc_id = payload.get("doc_id", "")
            doc_title = payload.get("doc_title", "Unknown")
            doc_path = payload.get("doc_path", "")
            text = payload.get("text", "")
            section_path = payload.get("section_path", [])
            chunk_index = payload.get("chunk_index", 0)
            is_parent = payload.get("is_parent", False)
            parent_id = payload.get("parent_id")
            
            # Determine score breakdown
            dense_score = None
            bm25_score = None
            rrf_score = None
            
            if method == "hybrid" and not was_reranked:
                # Original score is RRF score
                rrf_score = original_score
            elif method == "dense":
                dense_score = original_score
            elif method == "bm25":
                bm25_score = original_score
            
            retrieval_results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=text,
                    doc_id=doc_id,
                    doc_title=doc_title,
                    doc_path=doc_path,
                    section_path=section_path,
                    chunk_index=chunk_index,
                    is_parent=is_parent,
                    parent_id=parent_id,
                    dense_score=dense_score,
                    bm25_score=bm25_score,
                    rrf_score=rrf_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    payload=payload,
                )
            )
        
        return retrieval_results
    
    def retrieve_with_context_expansion(
        self,
        query: str,
        top_k: Optional[int] = None,
        expand_parents: bool = True,
        max_expanded_tokens: int = 1500,
        doc_path: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve with automatic parent context expansion.
        
        For child chunks with low confidence or small size,
        includes parent chunk text for additional context.
        
        Expansion criteria (from RAG best practices):
        - Retrieved chunk < 300 tokens
        - Rerank score < 0.6 (low confidence)
        
        Expansion limits:
        - Maximum expanded context: 1500 tokens (configurable)
        - Always include original chunk
        - Fetch parent and optionally siblings
        
        Args:
            query: Search query
            top_k: Number of results
            expand_parents: Whether to expand parent context
            max_expanded_tokens: Maximum tokens in expanded context
            
        Returns:
            List of retrieval results with expanded context where appropriate
        """
        # Get base results
        results = self.retrieve(query, top_k=top_k, **({'doc_path': doc_path} if doc_path else {}))
        
        if not expand_parents:
            return results
        
        logger.info(
            f"Context expansion: evaluating {len(results)} results",
            extra={
                "query": query,
                "top_k": top_k,
                "max_expanded_tokens": max_expanded_tokens,
            }
        )
        
        # Identify child chunks that need expansion
        expansion_count = 0
        for idx, result in enumerate(results):
            # Log each chunk for diagnostics
            chunk_tokens = self.embedding_service.estimate_tokens(result.text)
            
            logger.debug(
                f"Evaluating chunk {idx}",
                extra={
                    "chunk_id": result.chunk_id,
                    "is_parent": result.is_parent,
                    "parent_id": result.parent_id,
                    "chunk_tokens": chunk_tokens,
                    "rerank_score": result.rerank_score,
                    "final_score": result.final_score,
                }
            )
            
            if not result.is_parent and result.parent_id:
                # Estimate tokens in current chunk
                
                # Check if expansion needed
                should_expand = (
                    chunk_tokens < 300 or  # Small chunk (< 300 tokens)
                    (result.rerank_score and result.rerank_score < 0.6)  # Low confidence
                )
                
                logger.debug(
                    f"Child chunk eligibility check",
                    extra={
                        "chunk_id": result.chunk_id,
                        "chunk_tokens": chunk_tokens,
                        "rerank_score": result.rerank_score,
                        "should_expand": should_expand,
                        "reason": "small_chunk" if chunk_tokens < 300 else "low_confidence" if result.rerank_score and result.rerank_score < 0.6 else "none",
                    }
                )
                
                if should_expand:
                    # Fetch parent chunk
                    parent = self.vector_store.get_point(result.parent_id)
                    
                    if not parent:
                        logger.warning(
                            f"Parent chunk not found",
                            extra={
                                "chunk_id": result.chunk_id,
                                "parent_id": result.parent_id,
                            }
                        )
                        continue
                    
                    if parent:
                        parent_text = parent.payload.get("text", "")
                        parent_tokens = self.embedding_service.estimate_tokens(parent_text)
                        
                        # Check if expanded context would exceed limit
                        total_tokens = chunk_tokens + parent_tokens
                        
                        if total_tokens <= max_expanded_tokens:
                            # Add full parent context
                            original_text = result.text
                            result.text = f"{parent_text}\n\n---\n\n{result.text}"
                            expansion_count += 1
                            
                            logger.info(
                                f"Expanded context for chunk {result.chunk_id}",
                                extra={
                                    "parent_id": result.parent_id,
                                    "original_tokens": chunk_tokens,
                                    "parent_tokens": parent_tokens,
                                    "expanded_tokens": total_tokens,
                                    "original_length": len(original_text),
                                    "expanded_length": len(result.text),
                                }
                            )
                        else:
                            # Truncate parent text to fit within limit
                            available_tokens = max_expanded_tokens - chunk_tokens
                            if available_tokens > 100:  # Only add if meaningful
                                truncated_parent = self.embedding_service.truncate_to_max_length(
                                    parent_text,
                                    max_tokens=available_tokens
                                )
                                original_text = result.text
                                result.text = f"{truncated_parent}\n\n---\n\n{result.text}"
                                expansion_count += 1
                                
                                logger.info(
                                    f"Expanded context (truncated) for chunk {result.chunk_id}",
                                    extra={
                                        "parent_id": result.parent_id,
                                        "original_tokens": chunk_tokens,
                                        "parent_tokens": parent_tokens,
                                        "available_tokens": available_tokens,
                                        "expanded_tokens": max_expanded_tokens,
                                        "parent_truncated": True,
                                        "original_length": len(original_text),
                                        "expanded_length": len(result.text),
                                    }
                                )
                            else:
                                logger.debug(
                                    f"Skipping expansion - insufficient token budget",
                                    extra={
                                        "chunk_id": result.chunk_id,
                                        "available_tokens": available_tokens,
                                    }
                                )
        
        logger.info(
            f"Context expansion complete",
            extra={
                "total_results": len(results),
                "expansions_performed": expansion_count,
            }
        )
        
        return results


def get_retrieval_pipeline(
    collection_name: str = "tutor_knowledge",
    **kwargs
) -> RetrievalPipeline:
    """
    Get RetrievalPipeline instance (factory function).
    
    Args:
        collection_name: Qdrant collection name
        **kwargs: Additional configuration parameters
        
    Returns:
        RetrievalPipeline instance
    """
    return RetrievalPipeline(collection_name=collection_name, **kwargs)
