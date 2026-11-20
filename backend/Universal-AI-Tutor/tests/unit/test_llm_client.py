"""
Unit tests for LLM client.

Tests mock LLM client functionality.
"""

import pytest
from src.core.llm_client import (
    MockLLMClient,
    GenerationConfig,
    GenerationResult,
    get_llm_client,
    reset_llm_client
)


@pytest.fixture
def mock_client():
    """Provide MockLLMClient instance."""
    return MockLLMClient(model="test-model")


@pytest.fixture
def sample_context():
    """Provide sample context chunks."""
    return [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.",
        "Supervised learning uses labeled training data to teach algorithms to classify data or predict outcomes.",
        "Deep learning is a type of machine learning that uses neural networks with multiple layers to process complex patterns.",
    ]


class TestGenerationConfig:
    """Test GenerationConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GenerationConfig()
        
        assert config.temperature == 0.3
        assert config.max_tokens == 800
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.3
        assert config.presence_penalty == 0.0
        assert config.stop_sequences is None
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = GenerationConfig(
            temperature=0.7,
            max_tokens=1000,
            stop_sequences=["END"]
        )
        
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.stop_sequences == ["END"]


class TestGenerationResult:
    """Test GenerationResult dataclass."""
    
    def test_result_creation(self):
        """Test creating generation result."""
        result = GenerationResult(
            text="Test response",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            finish_reason="stop",
            metadata={"test": True}
        )
        
        assert result.text == "Test response"
        assert result.model == "test-model"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5
        assert result.total_tokens == 15
        assert result.finish_reason == "stop"
        assert result.metadata["test"] is True


class TestMockLLMClient:
    """Test MockLLMClient class."""
    
    def test_initialization(self, mock_client):
        """Test client initialization."""
        assert mock_client.model == "test-model"
        assert mock_client.call_count == 0
    
    def test_generate_basic(self, mock_client):
        """Test basic text generation."""
        result = mock_client.generate("Test prompt")
        
        assert isinstance(result, GenerationResult)
        assert len(result.text) > 0
        assert result.model == "test-model"
        assert result.prompt_tokens > 0
        assert result.completion_tokens > 0
        assert result.total_tokens == result.prompt_tokens + result.completion_tokens
        assert result.finish_reason == "stop"
        assert result.metadata["mock"] is True
        assert mock_client.call_count == 1
    
    def test_generate_with_config(self, mock_client):
        """Test generation with config (config ignored in mock)."""
        config = GenerationConfig(temperature=0.7, max_tokens=500)
        result = mock_client.generate("Test prompt", config=config)
        
        assert isinstance(result, GenerationResult)
        assert len(result.text) > 0
    
    def test_generate_machine_learning_keyword(self, mock_client):
        """Test response for machine learning keyword."""
        result = mock_client.generate("What is machine learning?")
        
        assert "machine learning" in result.text.lower()
        assert "artificial intelligence" in result.text.lower()
    
    def test_generate_python_keyword(self, mock_client):
        """Test response for Python keyword."""
        result = mock_client.generate("Tell me about Python")
        
        assert "python" in result.text.lower()
        assert "programming language" in result.text.lower()
    
    def test_generate_algorithm_keyword(self, mock_client):
        """Test response for algorithm keyword."""
        result = mock_client.generate("Explain algorithms")
        
        assert "algorithm" in result.text.lower()
    
    def test_generate_generic_response(self, mock_client):
        """Test generic response for unknown keywords."""
        result = mock_client.generate("Random unrelated query")
        
        assert "mock response" in result.text.lower()
    
    def test_generate_with_context_strict_mode(self, mock_client, sample_context):
        """Test contextual generation in strict mode."""
        result = mock_client.generate_with_context(
            question="What is machine learning?",
            context_chunks=sample_context,
            mode="strict"
        )
        
        assert isinstance(result, GenerationResult)
        assert len(result.text) > 0
        assert "Based on your notes" in result.text or "From your notes" in result.text
        assert "[Source:" in result.text  # Should have citation in strict mode
        assert result.metadata["mode"] == "strict"
        assert result.metadata["context_chunks_count"] == 3
        assert mock_client.call_count == 1
    
    def test_generate_with_context_teaching_mode(self, mock_client, sample_context):
        """Test contextual generation in teaching mode."""
        result = mock_client.generate_with_context(
            question="What is machine learning?",
            context_chunks=sample_context,
            mode="teaching"
        )
        
        assert isinstance(result, GenerationResult)
        assert len(result.text) > 0
        assert "From your notes" in result.text
        assert "To help understand" in result.text  # Teaching explanation
        assert result.metadata["mode"] == "teaching"
    
    def test_generate_with_context_no_context(self, mock_client):
        """Test response when no context provided."""
        result = mock_client.generate_with_context(
            question="What is quantum computing?",
            context_chunks=[],
            mode="strict"
        )
        
        assert "don't have enough information" in result.text
    
    def test_generate_with_context_irrelevant_context(self, mock_client):
        """Test response when context doesn't match question."""
        irrelevant_context = [
            "Cats are domesticated animals.",
            "Dogs are loyal companions.",
        ]
        
        result = mock_client.generate_with_context(
            question="What is quantum computing?",
            context_chunks=irrelevant_context,
            mode="strict"
        )
        
        assert "don't have enough information" in result.text
    
    def test_generate_with_context_relevant_match(self, mock_client, sample_context):
        """Test response when context matches question terms."""
        result = mock_client.generate_with_context(
            question="Explain supervised learning",
            context_chunks=sample_context,
            mode="strict"
        )
        
        # Should find "supervised" and "learning" in context
        assert "don't have enough information" not in result.text
        assert len(result.text) > 50
    
    def test_call_count_increments(self, mock_client):
        """Test that call count increments correctly."""
        assert mock_client.call_count == 0
        
        mock_client.generate("Test 1")
        assert mock_client.call_count == 1
        
        mock_client.generate("Test 2")
        assert mock_client.call_count == 2
        
        mock_client.generate_with_context("Test 3", ["context"], "strict")
        assert mock_client.call_count == 3
    
    def test_reset_call_count(self, mock_client):
        """Test resetting call counter."""
        mock_client.generate("Test")
        mock_client.generate("Test")
        assert mock_client.call_count == 2
        
        mock_client.reset_call_count()
        assert mock_client.call_count == 0
    
    def test_extract_key_terms(self, mock_client):
        """Test key term extraction."""
        terms = mock_client._extract_key_terms(
            "what is machine learning and how does it work"
        )
        
        # Should extract meaningful terms, filter stop words
        assert "machine" in terms
        assert "learning" in terms
        assert "work" in terms
        assert "what" not in terms  # Stop word
        assert "is" not in terms  # Stop word
    
    def test_extract_key_terms_filters_short_words(self, mock_client):
        """Test that short words are filtered."""
        terms = mock_client._extract_key_terms("is a cat the dog")
        
        # All words are short or stop words
        assert len(terms) == 0
    
    def test_build_prompt_strict(self, mock_client):
        """Test prompt building for strict mode."""
        prompt = mock_client._build_prompt(
            question="What is AI?",
            context="AI is artificial intelligence.",
            mode="strict"
        )
        
        assert "Answer using ONLY the provided context" in prompt
        assert "What is AI?" in prompt
        assert "AI is artificial intelligence." in prompt
    
    def test_build_prompt_teaching(self, mock_client):
        """Test prompt building for teaching mode."""
        prompt = mock_client._build_prompt(
            question="What is AI?",
            context="AI is artificial intelligence.",
            mode="teaching"
        )
        
        assert "add explanations" in prompt
        assert "What is AI?" in prompt
        assert "AI is artificial intelligence." in prompt
    
    def test_token_estimation(self, mock_client):
        """Test that token counts are estimated."""
        result = mock_client.generate("This is a test prompt with several words")
        
        # Should estimate based on word count
        assert result.prompt_tokens > 5
        assert result.completion_tokens > 0
        assert result.total_tokens == result.prompt_tokens + result.completion_tokens
    
    def test_metadata_includes_mock_flag(self, mock_client):
        """Test that metadata indicates mock client."""
        result = mock_client.generate("Test")
        
        assert result.metadata["mock"] is True
        assert "call_count" in result.metadata


class TestGetLLMClient:
    """Test get_llm_client factory function."""
    
    def test_get_mock_client_default(self):
        """Test getting mock client by default."""
        reset_llm_client()
        client = get_llm_client()
        
        assert isinstance(client, MockLLMClient)
    
    def test_get_mock_client_explicit(self):
        """Test explicitly requesting mock client."""
        reset_llm_client()
        client = get_llm_client(mock=True)
        
        assert isinstance(client, MockLLMClient)
    
    def test_get_real_client_not_implemented(self):
        """Test that real client raises NotImplementedError."""
        reset_llm_client()
        
        with pytest.raises(NotImplementedError, match="Real LLM client not implemented"):
            get_llm_client(mock=False)
    
    def test_singleton_pattern(self):
        """Test that get_llm_client returns singleton."""
        reset_llm_client()
        
        client1 = get_llm_client()
        client2 = get_llm_client()
        
        assert client1 is client2
    
    def test_reset_singleton(self):
        """Test resetting singleton instance."""
        reset_llm_client()
        
        client1 = get_llm_client()
        reset_llm_client()
        client2 = get_llm_client()
        
        assert client1 is not client2
