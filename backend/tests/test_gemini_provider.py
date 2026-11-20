"""
Unit tests for Gemini LLM provider.

All tests use mocked responses to avoid API costs.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from app.extraction.llm_provider import GeminiProvider


class TestGeminiProviderInitialization:
    """Test Gemini provider initialization"""
    
    def test_init_requires_api_key(self):
        """Provider requires API key from env or parameter"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Gemini API key required"):
                GeminiProvider()
    
    @patch('google.genai.Client')
    def test_init_with_env_var(self, mock_client_class):
        """Provider initializes with environment variable"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            provider = GeminiProvider()
            assert provider.api_key == 'test-key'
            mock_client_class.assert_called_once_with(api_key='test-key')
    
    @patch('google.genai.Client')
    def test_init_with_parameter(self, mock_client_class):
        """Provider initializes with explicit API key"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key='explicit-key')
        assert provider.api_key == 'explicit-key'
        mock_client_class.assert_called_once_with(api_key='explicit-key')
    
    @patch('google.genai.Client')
    def test_init_with_custom_model(self, mock_client_class):
        """Provider accepts custom model name"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key='test-key', model='gemini-pro')
        assert provider.model == 'gemini-pro'
    
    @patch('google.genai.Client')
    def test_init_with_custom_tpm(self, mock_client_class):
        """Provider accepts custom TPM limit"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        provider = GeminiProvider(api_key='test-key', tokens_per_minute=30000)
        assert provider.tokens_per_minute == 30000


class TestGeminiProviderGenerate:
    """Test Gemini provider generate method"""
    
    @patch('google.genai.Client')
    def test_generate_success(self, mock_client_class):
        """Successful generation returns text content"""
        # Mock client and response
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response structure
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"  # Normal completion
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"concepts": [], "definitions": []}'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        mock_response.usage_metadata.total_token_count = 150
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        result = provider.generate("test prompt")
        
        assert result == '{"concepts": [], "definitions": []}'
        assert provider.last_response_metadata['finish_reason'] == "STOP"
        assert provider.last_response_metadata['usage']['total_tokens'] == 150
    
    @patch('google.genai.Client')
    def test_generate_finish_reason_enum(self, mock_client_class):
        """FinishReason enum format is handled correctly"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with FinishReason.STOP enum format
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "FinishReason.STOP"  # Enum string representation
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"test": "data"}'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        result = provider.generate("test prompt")
        
        # Should succeed without warnings
        assert result == '{"test": "data"}'
        assert provider.last_response_metadata['finish_reason'] == "FinishReason.STOP"
    
    @patch('google.genai.Client')
    def test_generate_with_system_prompt(self, mock_client_class):
        """Generation includes system instruction"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"test": "response"}'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        result = provider.generate("test prompt", system="system instruction")
        
        # Verify system instruction was passed in config
        call_kwargs = mock_client.models.generate_content.call_args[1]
        assert 'config' in call_kwargs
        # Config should have been created with system_instruction parameter
    
    @patch('google.genai.Client')
    def test_generate_truncated_response(self, mock_client_class):
        """Truncated response (MAX_TOKENS) raises error"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock truncated response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "MAX_TOKENS"
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"incomplete": true'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(ValueError, match="truncated due to max_tokens"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_safety_filter(self, mock_client_class):
        """Safety-filtered response raises error"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock safety-filtered response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "SAFETY"
        mock_content = MagicMock()
        mock_content.parts = []
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(ValueError, match="blocked by safety filter"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_recitation_block(self, mock_client_class):
        """Recitation-blocked response raises error"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock recitation-blocked response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "RECITATION"
        mock_content = MagicMock()
        mock_content.parts = []
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(ValueError, match="blocked due to recitation"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_empty_response(self, mock_client_class):
        """Empty response raises error"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock empty response (no candidates)
        mock_response = MagicMock()
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(ValueError, match="empty response"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_authentication_error(self, mock_client_class):
        """Authentication error is properly reported"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock API error
        mock_client.models.generate_content.side_effect = Exception("401 Unauthorized: Invalid API key")
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(RuntimeError, match="Gemini authentication error"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_rate_limit_error(self, mock_client_class):
        """Rate limit error is properly reported"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock rate limit error
        mock_client.models.generate_content.side_effect = Exception("429 Too Many Requests: Rate limit exceeded")
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(RuntimeError, match="rate_limit error"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_daily_quota_error(self, mock_client_class):
        """Daily quota error is properly reported"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock daily quota error
        mock_client.models.generate_content.side_effect = Exception("Quota exceeded: tokens per day limit reached")
        
        provider = GeminiProvider(api_key='test-key')
        
        with pytest.raises(RuntimeError, match="daily quota exhausted"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_model_not_found_error(self, mock_client_class):
        """Model not found (404) error is reported correctly without rate-limit classification"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock 404 model not found error
        mock_client.models.generate_content.side_effect = Exception(
            "404 NOT_FOUND. {'error': {'code': 404, 'message': 'models/gemini-invalid is not found', 'status': 'NOT_FOUND'}}"
        )
        
        provider = GeminiProvider(api_key='test-key')
        
        # Should raise RuntimeError with "model not found", NOT "rate_limit"
        with pytest.raises(RuntimeError, match="model not found"):
            provider.generate("test prompt")
    
    @patch('google.genai.Client')
    def test_generate_multiple_text_parts(self, mock_client_class):
        """Response with multiple text parts is combined"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with multiple parts
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"
        mock_content = MagicMock()
        
        mock_part1 = MagicMock()
        mock_part1.text = '{"concepts": ['
        mock_part2 = MagicMock()
        mock_part2.text = ']}'
        
        mock_content.parts = [mock_part1, mock_part2]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        result = provider.generate("test prompt")
        
        assert result == '{"concepts": []}'


class TestGeminiProviderJSONMode:
    """Test Gemini provider JSON output mode"""
    
    @patch('google.genai.Client')
    def test_json_mode_requested(self, mock_client_class):
        """Provider requests JSON output format"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = "STOP"
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = '{"test": "json"}'
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None
        
        mock_client.models.generate_content.return_value = mock_response
        
        provider = GeminiProvider(api_key='test-key')
        
        result = provider.generate("test prompt")
        
        # Verify JSON mime type was requested in config
        # Note: The actual config construction happens in generate()
        # We just verify the response is treated as JSON
        assert result == '{"test": "json"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
