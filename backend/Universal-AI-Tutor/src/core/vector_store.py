"""
Vector store for Universal AI Tutor using Qdrant.

Provides:
- Dense vector storage and search
- Native BM25 full-text indexing (Qdrant 1.20+)
- Hybrid search with RRF fusion
- Collection management
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    Vector store using Qdrant for dense embeddings and BM25 sparse search.

    Features:
    - Qdrant 1.20+ native BM25 on full-text index
    - Hybrid search (dense + BM25) with RRF fusion
    - Metadata filtering
    - Batch operations
    """

    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        collection_name: Optional[str] = None,
        embedding_dim: int = 384,
    ) -> None:
        """
        Initialize vector store.

        Args:
            client: Qdrant client (default: create from config)
            collection_name: Collection name (default from config)
            embedding_dim: Embedding dimension (default: 384 for BGE-small)
        """
        settings = get_settings()

        self.collection_name = collection_name or settings.qdrant_collection_name
        self.embedding_dim = embedding_dim

        # Initialize client
        if client is None:
            qdrant_url = settings.qdrant_url
            qdrant_api_key = settings.qdrant_api_key or None

            logger.info(
                f"Connecting to Qdrant",
                extra={"url": qdrant_url, "has_api_key": bool(qdrant_api_key)},
            )

            try:
                self.client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=30,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}", exc_info=True)
                raise ConnectionError(
                    f"Failed to connect to Qdrant at {qdrant_url}: {str(e)}"
                ) from e
        else:
            self.client = client

        logger.info(
            f"VectorStore initialized",
            extra={
                "collection": self.collection_name,
                "embedding_dim": self.embedding_dim,
            },
        )

    def create_collection(self, recreate: bool = False) -> None:
        """
        Create Qdrant collection with dense vectors and BM25 text index.

        Args:
            recreate: If True, delete existing collection first

        Raises:
            RuntimeError: If collection creation fails
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            exists = any(
                col.name == self.collection_name for col in collections.collections
            )

            if exists:
                if recreate:
                    logger.warning(
                        f"Deleting existing collection: {self.collection_name}"
                    )
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection '{self.collection_name}' already exists")
                    return

            # Create collection with dense vectors
            logger.info(f"Creating collection: {self.collection_name}")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=self.embedding_dim, distance=Distance.COSINE
                    )
                },
            )

            # Create full-text index for BM25 (Qdrant 1.20+)
            logger.info("Creating BM25 full-text index on 'text' field")

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="text",
                field_schema=models.TextIndexParams(
                    type=models.TextIndexType.TEXT,
                    tokenizer=models.TokenizerType.WORD,
                    lowercase=True,
                    scoring=True,  # Enable BM25 scoring
                ),
            )

            logger.info(
                f"Collection '{self.collection_name}' created successfully with BM25 index"
            )

        except Exception as e:
            logger.error(f"Failed to create collection: {e}", exc_info=True)
            raise RuntimeError(
                f"Collection creation failed for '{self.collection_name}': {str(e)}"
            ) from e

    def collection_exists(self) -> bool:
        """
        Check if collection exists.

        Returns:
            bool: True if collection exists
        """
        try:
            collections = self.client.get_collections()
            return any(col.name == self.collection_name for col in collections.collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}", exc_info=True)
            return False

    def insert(
        self,
        id: Union[str, int],
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """
        Insert single point into collection.

        Args:
            id: Point ID (string will be converted to UUID, int used as-is)
            vector: Dense embedding vector
            payload: Metadata dict (must include 'text' for BM25)

        Raises:
            ValueError: If payload missing 'text' field
            RuntimeError: If insert fails
        """
        if "text" not in payload:
            raise ValueError("Payload must include 'text' field for BM25 indexing")

        try:
            # Convert string ID to UUID if needed
            if isinstance(id, str):
                # If it looks like a UUID, use it directly; otherwise hash it
                try:
                    from uuid import UUID
                    point_id = UUID(id)
                except ValueError:
                    # Not a valid UUID string, create deterministic UUID from string
                    import hashlib
                    hash_bytes = hashlib.md5(id.encode()).digest()
                    from uuid import UUID
                    point_id = UUID(bytes=hash_bytes)
            else:
                point_id = id

            point = PointStruct(
                id=point_id,
                vector={"dense": vector},
                payload=payload,
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            logger.debug(
                f"Inserted point",
                extra={"point_id": str(point_id), "payload_keys": list(payload.keys())},
            )

        except Exception as e:
            logger.error(
                f"Failed to insert point",
                extra={"point_id": str(id), "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Point insertion failed: {str(e)}") from e

    def insert_batch(
        self,
        ids: List[Union[str, int]],
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> None:
        """
        Insert multiple points in batch.

        Args:
            ids: List of point IDs (strings converted to UUIDs, ints used as-is)
            vectors: List of dense embedding vectors
            payloads: List of metadata dicts

        Raises:
            ValueError: If lists have different lengths or payloads missing 'text'
            RuntimeError: If batch insert fails
        """
        if not (len(ids) == len(vectors) == len(payloads)):
            raise ValueError("ids, vectors, and payloads must have same length")

        # Validate all payloads have 'text'
        for i, payload in enumerate(payloads):
            if "text" not in payload:
                raise ValueError(
                    f"Payload at index {i} missing 'text' field for BM25 indexing"
                )

        try:
            # Convert string IDs to UUIDs
            converted_ids = []
            for id_val in ids:
                if isinstance(id_val, str):
                    try:
                        from uuid import UUID
                        converted_ids.append(UUID(id_val))
                    except ValueError:
                        # Not a valid UUID string, create deterministic UUID
                        import hashlib
                        hash_bytes = hashlib.md5(id_val.encode()).digest()
                        from uuid import UUID
                        converted_ids.append(UUID(bytes=hash_bytes))
                else:
                    converted_ids.append(id_val)

            points = [
                PointStruct(
                    id=point_id,
                    vector={"dense": vector},
                    payload=payload,
                )
                for point_id, vector, payload in zip(converted_ids, vectors, payloads)
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            logger.info(
                f"Inserted batch",
                extra={"point_count": len(points)},
            )

        except Exception as e:
            logger.error(
                f"Failed to insert batch",
                extra={"point_count": len(ids), "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Batch insertion failed: {str(e)}") from e

    def dense_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[models.Filter] = None,
    ) -> List[models.ScoredPoint]:
        """
        Perform dense vector similarity search.

        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of scored points sorted by relevance

        Raises:
            RuntimeError: If search fails
        """
        try:
            logger.debug(f"Dense search", extra={"top_k": top_k})

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                using="dense",
                query_filter=filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            logger.debug(
                f"Dense search complete",
                extra={"results_count": len(results.points)},
            )

            return results.points

        except Exception as e:
            logger.error(f"Dense search failed: {e}", exc_info=True)
            raise RuntimeError(f"Dense search failed: {str(e)}") from e

    def bm25_search(
        self,
        query_text: str,
        top_k: int = 5,
        filter: Optional[models.Filter] = None,
    ) -> List[models.ScoredPoint]:
        """
        Perform BM25 full-text search.

        Uses Qdrant 1.20+ native BM25 scoring on full-text index.

        Args:
            query_text: Query text
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of scored points sorted by BM25 relevance

        Raises:
            RuntimeError: If search fails
        """
        try:
            logger.debug(f"BM25 search", extra={"query": query_text[:100], "top_k": top_k})

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=models.TextQuery(text=query_text),
                using="text",  # Full-text index
                query_filter=filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            logger.debug(
                f"BM25 search complete",
                extra={"results_count": len(results.points)},
            )

            return results.points

        except Exception as e:
            logger.error(f"BM25 search failed: {e}", exc_info=True)
            raise RuntimeError(f"BM25 search failed: {str(e)}") from e

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        dense_top_k: Optional[int] = None,
        bm25_top_k: Optional[int] = None,
        filter: Optional[models.Filter] = None,
    ) -> List[models.ScoredPoint]:
        """
        Perform hybrid search combining dense and BM25 with RRF fusion.

        Uses Qdrant 1.20+ native RRF (Reciprocal Rank Fusion).

        Args:
            query_text: Query text for BM25
            query_vector: Query embedding for dense search
            top_k: Number of final results after fusion
            dense_top_k: Number of dense candidates (default: 20)
            bm25_top_k: Number of BM25 candidates (default: 20)
            filter: Optional metadata filter

        Returns:
            List of scored points sorted by fused relevance

        Raises:
            RuntimeError: If search fails
        """
        settings = get_settings()
        dense_top_k = dense_top_k or settings.dense_top_k
        bm25_top_k = bm25_top_k or settings.bm25_top_k

        try:
            logger.debug(
                f"Hybrid search",
                extra={
                    "query": query_text[:100],
                    "top_k": top_k,
                    "dense_top_k": dense_top_k,
                    "bm25_top_k": bm25_top_k,
                },
            )

            # Qdrant 1.20+ native hybrid search with RRF
            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    # BM25 search
                    models.Prefetch(
                        query=models.TextQuery(text=query_text),
                        using="text",
                        limit=bm25_top_k,
                    ),
                    # Dense vector search
                    models.Prefetch(
                        query=query_vector,
                        using="dense",
                        limit=dense_top_k,
                    ),
                ],
                # RRF fusion of prefetches
                query=models.RrfQuery(rrf=models.Rrf()),
                query_filter=filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )

            logger.debug(
                f"Hybrid search complete",
                extra={"results_count": len(results.points)},
            )

            return results.points

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}", exc_info=True)
            raise RuntimeError(f"Hybrid search failed: {str(e)}") from e

    def get_point(self, point_id: Union[str, int]) -> Optional[models.Record]:
        """
        Retrieve single point by ID.

        Args:
            point_id: Point ID (string converted to UUID, int used as-is)

        Returns:
            Point record or None if not found
        """
        try:
            # Convert string ID to UUID if needed
            if isinstance(point_id, str):
                try:
                    from uuid import UUID
                    converted_id = UUID(point_id)
                except ValueError:
                    import hashlib
                    hash_bytes = hashlib.md5(point_id.encode()).digest()
                    from uuid import UUID
                    converted_id = UUID(bytes=hash_bytes)
            else:
                converted_id = point_id

            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[converted_id],
                with_payload=True,
                with_vectors=True,
            )

            return points[0] if points else None

        except Exception as e:
            logger.error(
                f"Failed to get point",
                extra={"point_id": str(point_id), "error": str(e)},
                exc_info=True,
            )
            return None
    
    def get_points(self, point_ids: List[Union[str, int]]) -> List[models.Record]:
        """
        Get multiple points by their IDs.
        
        Args:
            point_ids: List of point IDs
            
        Returns:
            List of point records found (may be fewer than requested)
        """
        try:
            if not point_ids:
                return []
            
            # Convert all IDs to UUIDs
            converted_ids = []
            for point_id in point_ids:
                if isinstance(point_id, str):
                    try:
                        from uuid import UUID
                        converted_ids.append(UUID(point_id))
                    except ValueError:
                        import hashlib
                        hash_bytes = hashlib.md5(point_id.encode()).digest()
                        from uuid import UUID
                        converted_ids.append(UUID(bytes=hash_bytes))
                else:
                    converted_ids.append(point_id)
            
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=converted_ids,
                with_payload=True,
                with_vectors=False,
            )
            
            return result if result else []
            
        except Exception as e:
            logger.error(
                f"Failed to retrieve points",
                extra={"count": len(point_ids), "error": str(e)},
                exc_info=True,
            )
            return []

    def delete_points(self, point_ids: List[Union[str, int]]) -> None:
        """
        Delete multiple points by ID.

        Args:
            point_ids: List of point IDs to delete (strings converted to UUIDs)

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            # Convert string IDs to UUIDs
            converted_ids = []
            for id_val in point_ids:
                if isinstance(id_val, str):
                    try:
                        from uuid import UUID
                        converted_ids.append(UUID(id_val))
                    except ValueError:
                        import hashlib
                        hash_bytes = hashlib.md5(id_val.encode()).digest()
                        from uuid import UUID
                        converted_ids.append(UUID(bytes=hash_bytes))
                else:
                    converted_ids.append(id_val)

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=converted_ids),
            )

            logger.info(f"Deleted points", extra={"count": len(point_ids)})

        except Exception as e:
            logger.error(
                f"Failed to delete points",
                extra={"count": len(point_ids), "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Point deletion failed: {str(e)}") from e
    
    def delete_by_filter(self, filter_condition: models.Filter) -> int:
        """
        Delete points matching a filter condition.
        
        Args:
            filter_condition: Qdrant filter to match points
            
        Returns:
            Number of points deleted
            
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            # First, count how many points match
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=filter_condition,
                exact=True
            )
            count = count_result.count
            
            if count == 0:
                logger.info("No points matched filter for deletion")
                return 0
            
            # Delete using filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(filter=filter_condition),
            )
            
            logger.info(f"Deleted points by filter", extra={"count": count})
            return count
            
        except Exception as e:
            logger.error(
                f"Failed to delete points by filter",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Filtered deletion failed: {str(e)}") from e
    
    def scroll_points(
        self, 
        filter_condition: Optional[models.Filter] = None,
        limit: int = 100,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[models.Record]:
        """
        Scroll through points in the collection.
        
        Useful for finding all points matching a condition without
        loading everything into memory at once.
        
        Args:
            filter_condition: Optional filter to match points
            limit: Maximum number of points to return
            with_payload: Include payload data
            with_vectors: Include vector data
            
        Returns:
            List of matching point records
            
        Raises:
            RuntimeError: If scroll fails
        """
        try:
            records = []
            offset = None
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=filter_condition,
                    limit=min(limit - len(records), 100),  # Qdrant scroll limit per call
                    offset=offset,
                    with_payload=with_payload,
                    with_vectors=with_vectors,
                )
                
                if not result[0]:  # No more results
                    break
                
                records.extend(result[0])
                offset = result[1]  # Next offset
                
                if offset is None or len(records) >= limit:
                    break
            
            logger.debug(
                f"Scrolled points",
                extra={"count": len(records), "limit": limit}
            )
            
            return records
            
        except Exception as e:
            logger.error(
                f"Failed to scroll points",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Point scroll failed: {str(e)}") from e

    def get_all_chunks(self, limit: int = 10000) -> List[Dict]:
        """
        Get all chunks from the collection.
        
        Convenience method for evaluation and debugging.
        
        Args:
            limit: Maximum number of chunks to return
            
        Returns:
            List of chunk dictionaries with id, text, and metadata
        """
        records = self.scroll_points(limit=limit, with_payload=True, with_vectors=False)
        
        chunks = []
        for record in records:
            chunk = {
                "id": str(record.id),
                "chunk_id": str(record.id),
                "text": record.payload.get("text", ""),
                "metadata": {
                    "source": record.payload.get("source", ""),
                    "section_title": record.payload.get("section_title", ""),
                    "doc_id": record.payload.get("doc_id", ""),
                    "chunk_index": record.payload.get("chunk_index", 0)
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def count_points(self) -> int:
        """
        Count total points in collection.

        Returns:
            int: Number of points
        """
        try:
            result = self.client.count(collection_name=self.collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count points: {e}", exc_info=True)
            return 0

    def close(self) -> None:
        """Close Qdrant client connection."""
        try:
            self.client.close()
            logger.info("VectorStore connection closed")
        except Exception as e:
            logger.warning(f"Error closing VectorStore: {e}")


# Global singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get singleton vector store instance.

    Returns:
        VectorStore: Global vector store instance

    Note:
        Store is initialized lazily on first call.
        Connection is reused across the application.
    """
    global _vector_store

    if _vector_store is None:
        logger.info("Creating global VectorStore instance")
        _vector_store = VectorStore()

    return _vector_store
