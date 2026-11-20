"""
Embedding service for Universal AI Tutor.

Uses BGE-small-en-v1.5 for generating 384-dimensional embeddings.
Handles token limits, batching, and caching.
"""

from functools import lru_cache
from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer

from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using BGE-small-en-v1.5.

    Features:
    - 384-dimensional embeddings
    - 512 token max length (safe limit: 480 tokens)
    - CPU-friendly (optional GPU support)
    - Batch processing
    - LRU caching for repeated queries
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> None:
        """
        Initialize embedding service.

        Args:
            model_name: Embedding model name (default from config)
            device: Device to use ('cpu' or 'cuda', default from config)
            max_length: Maximum token length (default from config)
        """
        settings = get_settings()

        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.max_length = max_length or settings.embedding_max_length
        self.batch_size = settings.embedding_batch_size

        logger.info(
            f"Initializing EmbeddingService",
            extra={
                "model": self.model_name,
                "device": self.device,
                "max_length": self.max_length,
                "batch_size": self.batch_size,
            },
        )

        # Load model
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.model.max_seq_length = self.max_length

            # Get embedding dimension
            self.embedding_dim = self.model.get_sentence_embedding_dimension()

            logger.info(
                f"EmbeddingService initialized successfully",
                extra={"embedding_dim": self.embedding_dim},
            )
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}", exc_info=True)
            raise RuntimeError(
                f"Failed to load embedding model '{self.model_name}': {str(e)}"
            ) from e

    def embed(self, text: str, normalize: bool = True) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed
            normalize: Whether to L2-normalize the embedding (default: True)

        Returns:
            List of floats representing the embedding vector

        Raises:
            ValueError: If text is empty
            RuntimeError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            # Generate embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False,
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(
                f"Failed to generate embedding",
                extra={"text_length": len(text), "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Embedding generation failed: {str(e)}") from e

    def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        normalize: bool = True,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing (default from config)
            normalize: Whether to L2-normalize embeddings (default: True)
            show_progress: Whether to show progress bar (default: False)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts list is empty
            RuntimeError: If embedding generation fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts",
                extra={"original_count": len(texts), "valid_count": len(valid_texts)},
            )

        if not valid_texts:
            raise ValueError("All texts are empty after filtering")

        batch_size = batch_size or self.batch_size

        try:
            logger.info(
                f"Generating embeddings for batch",
                extra={
                    "text_count": len(valid_texts),
                    "batch_size": batch_size,
                },
            )

            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
            )

            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(
                f"Failed to generate batch embeddings",
                extra={"text_count": len(valid_texts), "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Batch embedding generation failed: {str(e)}") from e

    @lru_cache(maxsize=10000)
    def embed_cached(self, text: str, normalize: bool = True) -> tuple:
        """
        Generate embedding with LRU caching.

        Useful for repeated queries. Returns tuple for hashability.

        Args:
            text: Input text to embed
            normalize: Whether to L2-normalize the embedding

        Returns:
            Tuple of floats representing the embedding vector
        """
        embedding = self.embed(text, normalize=normalize)
        return tuple(embedding)

    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of embeddings.

        Returns:
            int: Embedding dimension (384 for BGE-small-en-v1.5)
        """
        return self.embedding_dim

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses the model's tokenizer for accurate estimation.

        Args:
            text: Input text

        Returns:
            int: Estimated token count
        """
        if not text:
            return 0

        try:
            tokens = self.model.tokenizer.encode(text, add_special_tokens=True)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {e}")
            # Fallback: rough estimate
            return len(text) // 4

    def truncate_to_max_length(self, text: str, *, max_tokens: int | None = None) -> str:
        """
        Truncate text to fit within max token length.

        Args:
            text: Input text
            max_tokens: Optional token budget for the caller's context

        Returns:
            str: Truncated text that fits within token limit
        """
        limit = self.max_length if max_tokens is None else max_tokens
        token_count = self.estimate_tokens(text)

        if token_count <= limit:
            return text

        logger.warning(
            f"Text exceeds max length, truncating",
            extra={"token_count": token_count, "max_length": limit},
        )

        # Binary search for appropriate length
        left, right = 0, len(text)
        result = ""

        while left <= right:
            mid = (left + right) // 2
            candidate = text[:mid]
            candidate_tokens = self.estimate_tokens(candidate)

            if candidate_tokens <= limit:
                result = candidate
                left = mid + 1
            else:
                right = mid - 1

        return result


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get singleton embedding service instance.

    Returns:
        EmbeddingService: Global embedding service instance

    Note:
        Service is initialized lazily on first call.
        Model loading happens once and is reused across the application.
    """
    global _embedding_service

    if _embedding_service is None:
        logger.info("Creating global EmbeddingService instance")
        _embedding_service = EmbeddingService()

    return _embedding_service
