"""
Unit tests for EmbeddingService.

Tests embedding generation, batching, caching, and token handling.
"""

import pytest
from unittest.mock import Mock, patch

from src.core.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    @pytest.fixture
    def mock_sentence_transformer(self, mocker):
        """Provide a mocked SentenceTransformer."""
        mock_model = mocker.Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.max_seq_length = 512

        # Mock encode to return numpy array
        import numpy as np

        mock_model.encode.return_value = np.array([0.1] * 384)

        # Mock tokenizer
        mock_tokenizer = mocker.Mock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_model.tokenizer = mock_tokenizer

        return mock_model

    @pytest.fixture
    def embedding_service(self, mocker, mock_sentence_transformer):
        """Provide an EmbeddingService with mocked model."""
        mocker.patch(
            "src.core.embedding_service.SentenceTransformer",
            return_value=mock_sentence_transformer,
        )

        service = EmbeddingService(
            model_name="test-model", device="cpu", max_length=512
        )
        return service

    def test_initialization_success(self, embedding_service):
        """Test that service initializes successfully."""
        assert embedding_service.model_name == "test-model"
        assert embedding_service.device == "cpu"
        assert embedding_service.max_length == 512
        assert embedding_service.embedding_dim == 384

    def test_embed_single_text_success(self, embedding_service):
        """Test embedding generation for single text."""
        text = "This is a test."
        embedding = embedding_service.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_empty_text_raises_error(self, embedding_service):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.embed("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            embedding_service.embed("   ")

    def test_embed_batch_success(self, embedding_service, mock_sentence_transformer):
        """Test batch embedding generation."""
        import numpy as np

        # Mock batch output
        mock_sentence_transformer.encode.return_value = np.array(
            [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        )

        texts = ["First text", "Second text", "Third text"]
        embeddings = embedding_service.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_embed_batch_empty_list_raises_error(self, embedding_service):
        """Test that empty batch raises ValueError."""
        with pytest.raises(ValueError, match="Texts list cannot be empty"):
            embedding_service.embed_batch([])

    def test_embed_batch_filters_empty_texts(
        self, embedding_service, mock_sentence_transformer
    ):
        """Test that empty texts are filtered from batch."""
        import numpy as np

        mock_sentence_transformer.encode.return_value = np.array([[0.1] * 384])

        texts = ["Valid text", "", "   "]
        embeddings = embedding_service.embed_batch(texts)

        # Should only process valid text
        assert len(embeddings) == 1

    def test_embed_cached_returns_tuple(self, embedding_service):
        """Test that cached embedding returns hashable tuple."""
        text = "Cache me"
        embedding = embedding_service.embed_cached(text)

        assert isinstance(embedding, tuple)
        assert len(embedding) == 384

    def test_embed_cached_reuses_result(self, embedding_service, mock_sentence_transformer):
        """Test that cache avoids redundant computation."""
        text = "Cache me twice"

        # Call twice
        result1 = embedding_service.embed_cached(text)
        result2 = embedding_service.embed_cached(text)

        # Should be same object (cached)
        assert result1 is result2

        # Model should be called only once
        # Note: embed_cached calls embed which calls model.encode
        # Due to caching, second call doesn't reach model

    def test_get_embedding_dimension(self, embedding_service):
        """Test getting embedding dimension."""
        dim = embedding_service.get_embedding_dimension()
        assert dim == 384

    def test_estimate_tokens(self, embedding_service):
        """Test token estimation."""
        text = "Short text"
        tokens = embedding_service.estimate_tokens(text)

        assert isinstance(tokens, int)
        assert tokens == 5  # Mocked to return 5 tokens

    def test_estimate_tokens_empty(self, embedding_service):
        """Test token estimation for empty text."""
        tokens = embedding_service.estimate_tokens("")
        assert tokens == 0

    def test_truncate_to_max_length_no_truncation(self, embedding_service):
        """Test truncation when text is within limit."""
        text = "Short text within limit"
        truncated = embedding_service.truncate_to_max_length(text)

        assert truncated == text

    def test_truncate_to_max_length_truncates_long_text(
        self, embedding_service, mock_sentence_transformer
    ):
        """Test truncation of text exceeding limit."""
        # Mock tokenizer to return different counts
        def token_count_side_effect(text, add_special_tokens=True):
            # Simulate long text
            return len(text) * 2  # Pretend each char is 2 tokens

        mock_sentence_transformer.tokenizer.encode.side_effect = (
            token_count_side_effect
        )

        # Set low max_length for testing
        embedding_service.max_length = 10

        text = "A" * 100  # Long text
        truncated = embedding_service.truncate_to_max_length(text)

        # Should be truncated
        assert len(truncated) < len(text)

    def test_get_embedding_service_singleton(self, mocker, mock_sentence_transformer):
        """Test that get_embedding_service returns singleton."""
        mocker.patch(
            "src.core.embedding_service.SentenceTransformer",
            return_value=mock_sentence_transformer,
        )

        # Clear global singleton
        import src.core.embedding_service as em_module

        em_module._embedding_service = None

        # Get service twice
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        # Should be same instance
        assert service1 is service2


class TestEmbeddingServiceIntegration:
    """Integration tests with real model (slow, marked as integration)."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_embedding_generation(self):
        """Test embedding generation with real BGE model."""
        # This test requires actual model download
        service = EmbeddingService(
            model_name="BAAI/bge-small-en-v1.5", device="cpu", max_length=512
        )

        text = "The Pythagorean theorem states that a² + b² = c²."
        embedding = service.embed(text)

        # Verify properties
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert all(-1.5 <= x <= 1.5 for x in embedding)  # Reasonable range

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_batch_embedding(self):
        """Test batch embedding with real model."""
        service = EmbeddingService(
            model_name="BAAI/bge-small-en-v1.5", device="cpu", max_length=512
        )

        texts = [
            "First sentence about mathematics.",
            "Second sentence about computer science.",
            "Third sentence about physics.",
        ]

        embeddings = service.embed_batch(texts, batch_size=2)

        # Verify batch results
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

        # Verify embeddings are different
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]
