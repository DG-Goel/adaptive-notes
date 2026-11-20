"""
Unit tests for Ollama LLM provider.

All tests use mocked HTTP responses to avoid requiring a running Ollama server.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from app.extraction.llm_provider import OllamaProvider


class TestOllamaProviderInitialization:
    """Test Ollama provider initialization and setup verification"""
    
    @patch('httpx.get')
    def test_init_with_defaults(self, mock_get):
        """Provider initializes with default model and base URL"""
        # Mock successful server check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "granite4:micro"}
            ]
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'granite4:micro', 'OLLAMA_BASE_URL': 'http://localhost:11434'}):
            provider = OllamaProvider()
            assert provider.model == 'granite4:micro'
            assert provider.base_url == 'http://localhost:11434'
    
    @patch('httpx.get')
    def test_init_with_custom_model(self, mock_get):
        """Provider accepts custom model name"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "custom-model:latest"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Clear env vars to ensure test uses parameters
        with patch.dict('os.environ', {}, clear=True):
            provider = OllamaProvider(model='custom-model:latest')
            assert provider.model == 'custom-model:latest'
    
    @patch('httpx.get')
    def test_init_with_custom_base_url(self, mock_get):
        """Provider accepts custom base URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "granite4:micro"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Clear env vars to ensure test uses parameters
        with patch.dict('os.environ', {}, clear=True):
            provider = OllamaProvider(model='granite4:micro', base_url='http://192.168.1.100:11434')
            assert provider.base_url == 'http://192.168.1.100:11434'
    
    @patch('httpx.get')
    def test_init_strips_trailing_slash_from_base_url(self, mock_get):
        """Provider strips trailing slash from base URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "granite4:micro"}
            ]
        }
        mock_get.return_value = mock_response
        
        provider = OllamaProvider(model='granite4:micro', base_url='http://localhost:11434/')
        assert provider.base_url == 'http://localhost:11434'
    
    @patch('httpx.get')
    def test_init_with_env_override(self, mock_get):
        """Environment variables override parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "env-model:latest"}
            ]
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'env-model:latest', 'OLLAMA_BASE_URL': 'http://envhost:11434'}):
            provider = OllamaProvider(model='param-model', base_url='http://paramhost:11434')
            assert provider.model == 'env-model:latest'
            assert provider.base_url == 'http://envhost:11434'
    
    @patch('httpx.get')
    def test_init_server_unreachable(self, mock_get):
        """Initialization fails if Ollama server is unreachable"""
        mock_get.side_effect = Exception("Connection refused")
        
        with pytest.raises(RuntimeError, match="Cannot connect to Ollama server"):
            OllamaProvider(model='granite4:micro')
    
    @patch('httpx.get')
    def test_init_model_not_found(self, mock_get):
        """Initialization fails if model is not available"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model:latest"}
            ]
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Ollama model 'granite4:micro' not found"):
            OllamaProvider(model='granite4:micro')
    
    @patch('httpx.get')
    def test_init_model_tag_matching(self, mock_get):
        """Model name matches even if tags differ"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "granite4:latest"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Should succeed because base name matches
        provider = OllamaProvider(model='granite4:micro')
        assert provider.model == 'granite4:micro'


class TestOllamaProviderGenerate:
    """Test Ollama provider generate method"""
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_success(self, mock_post, mock_get):
        """Successful generation returns JSON content"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock generation response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {
                "role": "assistant",
                "content": '{"concepts": [], "definitions": []}'
            },
            "done": True,
            "done_reason": "stop",
            "total_duration": 1000000,
            "prompt_eval_count": 50,
            "eval_count": 20
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        result = provider.generate("test prompt")
        
        assert result == '{"concepts": [], "definitions": []}'
        assert provider.last_response_metadata['done'] is True
        assert provider.last_response_metadata['done_reason'] == "stop"
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_with_system_prompt(self, mock_post, mock_get):
        """Generation includes system message"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock generation response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": '{"test": "response"}'},
            "done": True,
            "done_reason": "stop"
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        provider.generate("test prompt", system="system instruction")
        
        # Verify system message was included
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        messages = payload['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'system instruction'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'test prompt'
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_json_format_requested(self, mock_post, mock_get):
        """Provider requests JSON format"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock generation response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": '{"test": "json"}'},
            "done": True
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        provider.generate("test prompt")
        
        # Verify JSON format was requested
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        assert payload['format'] == 'json'
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_temperature_and_max_tokens(self, mock_post, mock_get):
        """Temperature and max_tokens are passed correctly"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock generation response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": '{"test": "response"}'},
            "done": True
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        provider.generate("test", temperature=0.7, max_tokens=2000)
        
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        assert payload['options']['temperature'] == 0.7
        assert payload['options']['num_predict'] == 2000
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_empty_response(self, mock_post, mock_get):
        """Empty response raises ValueError"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock empty response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": ""},
            "done": True
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(ValueError, match="empty content"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_missing_message_field(self, mock_post, mock_get):
        """Response without message field raises ValueError"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock malformed response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "done": True
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(ValueError, match="without 'message' field"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_truncated_response(self, mock_post, mock_get):
        """Truncated response (length reason) raises error"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock truncated response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": '{"incomplete": true'},
            "done": True,
            "done_reason": "length"
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(ValueError, match="truncated due to max_tokens"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_incomplete_response(self, mock_post, mock_get):
        """Incomplete response (done=false) raises error"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock incomplete response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": '{"test": "partial'},
            "done": False
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(ValueError, match="incomplete.*done=false"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_timeout_error(self, mock_post, mock_get):
        """Timeout error is properly reported"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Import the actual exception class
        import httpx
        mock_post.side_effect = httpx.TimeoutException("Request timeout")
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(RuntimeError, match="Ollama request timeout"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_connection_error(self, mock_post, mock_get):
        """Connection error is properly reported"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Import the actual exception class
        import httpx
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(RuntimeError, match="Cannot connect to Ollama server"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_model_not_found_error(self, mock_post, mock_get):
        """Model not found (404) error is properly reported"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Import the actual exception class
        import httpx
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "model 'granite4:micro' not found"
        mock_post.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=mock_response
        )
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(RuntimeError, match="Ollama model.*not found"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_http_error(self, mock_post, mock_get):
        """HTTP errors are properly reported"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Import the actual exception class
        import httpx
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=Mock(),
            response=mock_response
        )
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(RuntimeError, match="Ollama API error.*500"):
            provider.generate("test prompt")
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_generate_malformed_json_response(self, mock_post, mock_get):
        """Malformed JSON response raises ValueError"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock response with invalid JSON
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        
        with pytest.raises(ValueError, match="Failed to parse Ollama response as JSON"):
            provider.generate("test prompt")


class TestOllamaProviderNoMockFallback:
    """Test that Ollama provider never falls back to mock responses"""
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_no_silent_mock_fallback_on_error(self, mock_post, mock_get):
        """Provider raises error instead of returning mock response"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        # Mock API failure
        mock_post.side_effect = Exception("API failure")
        
        provider = OllamaProvider(model='granite4:micro')
        
        # Should raise error, not return empty mock response
        with pytest.raises(RuntimeError):
            provider.generate("test prompt")


class TestOllamaProviderJSONParsing:
    """Test that Ollama provider responses work with extractor"""
    
    @patch('httpx.get')
    @patch('httpx.post')
    def test_valid_json_response(self, mock_post, mock_get):
        """Valid JSON response is returned as-is"""
        # Mock initialization
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "granite4:micro"}]}
        mock_get.return_value = mock_get_response
        
        valid_json = json.dumps({
            "concepts": [{"concept_name": "Test", "content": "A test", "source_unit_ids": ["S001"]}],
            "definitions": [],
            "explanations": [],
            "examples": [],
            "facts": [],
            "formulas": [],
            "procedures": [],
            "relationships": []
        })
        
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "model": "granite4:micro",
            "message": {"role": "assistant", "content": valid_json},
            "done": True
        }
        mock_post.return_value = mock_post_response
        
        provider = OllamaProvider(model='granite4:micro')
        result = provider.generate("test prompt")
        
        # Should be parseable as JSON
        parsed = json.loads(result)
        assert "concepts" in parsed
        assert len(parsed["concepts"]) == 1
        assert parsed["concepts"][0]["concept_name"] == "Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
