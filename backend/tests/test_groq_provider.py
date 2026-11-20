"""
Unit tests for Groq LLM provider.

Tests credential loading, API calls, error handling, and JSON parsing
using mocked responses (no API credits consumed).
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.extraction.llm_provider import GroqProvider, GroqProviderError


class TestGroqProviderInitialization:
    """Test Groq provider initialization and credential handling."""
    
    def test_missing_api_key_raises_error(self):
        """Provider should fail clearly if API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Groq API key required"):
                GroqProvider(use_multi_key=False)
    
    def test_api_key_from_parameter(self):
        """Provider should accept API key as parameter."""
        with patch('groq.Groq') as mock_groq:
            provider = GroqProvider(api_key="test-key-123", use_multi_key=False)
            assert provider.api_key == "test-key-123"
            mock_groq.assert_called_once_with(api_key="test-key-123")
    
    def test_api_key_from_environment(self):
        """Provider should load API key from GROQ_API_KEY environment variable."""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'env-key-456'}):
            with patch('groq.Groq') as mock_groq:
                provider = GroqProvider(use_multi_key=False)
                assert provider.api_key == "env-key-456"
                mock_groq.assert_called_once_with(api_key="env-key-456")
    
    def test_custom_model_name(self):
        """Provider should accept custom model name."""
        with patch('groq.Groq'):
            provider = GroqProvider(model="custom-model", api_key="test-key", use_multi_key=False)
            assert provider.model == "custom-model"
    
    def test_default_model_name(self):
        """Provider should use default model if not specified."""
        with patch('groq.Groq'):
            provider = GroqProvider(api_key="test-key", use_multi_key=False)
            assert provider.model == "openai/gpt-oss-120b"
    
    def test_multi_key_initialization(self):
        """Provider initializes multi-key pool if multiple credentials available"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'key1',
            'GROQ_API_KEY_2': 'key2',
            'GROQ_API_KEY_3': '',  # Clear
            'GROQ_API_KEY_4': '',  # Clear
            'GROQ_API_KEY_5': ''   # Clear
        }, clear=False):
            provider = GroqProvider(use_multi_key=True)
            assert provider.key_pool is not None
            assert len(provider.key_pool.credentials) == 2
    
    def test_single_key_fallback(self):
        """Provider falls back to single-key mode if only one credential"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'single_key',
            'GROQ_API_KEY_2': '',  # Clear
            'GROQ_API_KEY_3': '',  # Clear
            'GROQ_API_KEY_4': '',  # Clear
            'GROQ_API_KEY_5': ''   # Clear
        }, clear=False):
            with patch('groq.Groq'):
                provider = GroqProvider(use_multi_key=True)
                assert provider.key_pool is None
                assert provider.client is not None


class TestGroqProviderGenerate:
    """Test Groq provider generate method with mocked API responses."""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client."""
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            yield mock_client
    
    def test_successful_generation(self, mock_groq_client):
        """Test successful API call with valid response."""
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"concepts": []}'
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        result = provider.generate("Test prompt")
        
        assert result == '{"concepts": []}'
        mock_groq_client.chat.completions.create.assert_called_once()
    
    def test_system_message_included(self, mock_groq_client):
        """Test that system message is included in API call."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "response"
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        provider.generate("User prompt", system="System message")
        
        call_args = mock_groq_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'System message'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == 'User prompt'
    
    def test_temperature_and_max_tokens_passed(self, mock_groq_client):
        """Test that temperature and max_tokens are passed to API."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "response"
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        provider.generate("Test", temperature=0.7, max_tokens=2000)
        
        call_args = mock_groq_client.chat.completions.create.call_args
        assert call_args.kwargs['temperature'] == 0.7
        assert call_args.kwargs['max_tokens'] == 2000
    
    def test_empty_response_raises_error(self, mock_groq_client):
        """Test that empty response raises ValueError."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""  # Empty string instead of None
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        
        with pytest.raises(ValueError, match="Groq API returned empty response"):
            provider.generate("Test prompt")
    
    def test_api_error_raises_runtime_error(self, mock_groq_client):
        """Test that API errors are wrapped in RuntimeError."""
        mock_groq_client.chat.completions.create.side_effect = Exception("API Error")
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        
        with pytest.raises(RuntimeError, match="Groq API call failed"):
            provider.generate("Test prompt")


class TestGroqProviderMultiKey:
    """Test multi-key scheduling behavior"""
    
    def test_multi_key_rate_limit_retry(self):
        """Multi-key mode retries with different credential on rate limit"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'key1',
            'GROQ_API_KEY_2': 'key2'
        }):
            with patch('groq.Groq') as mock_groq_class:
                # First client hits rate limit, second succeeds
                mock_client1 = MagicMock()
                mock_client2 = MagicMock()
                
                mock_groq_class.side_effect = [mock_client1, mock_client2]
                
                # First call fails with 429
                mock_client1.chat.completions.create.side_effect = Exception("429 Rate limit exceeded")
                
                # Second call succeeds
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"success": true}'
                mock_response.choices[0].finish_reason = "stop"
                mock_client2.chat.completions.create.return_value = mock_response
                
                provider = GroqProvider(use_multi_key=True)
                result = provider.generate("Test prompt")
                
                assert result == '{"success": true}'
                # Both clients should have been tried
                assert mock_client1.chat.completions.create.called
                assert mock_client2.chat.completions.create.called
    
    def test_multi_key_auth_error_skips_credential(self):
        """Multi-key mode skips invalid credentials"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'bad_key',
            'GROQ_API_KEY_2': 'good_key',
            'GROQ_API_KEY_3': '',  # Clear
            'GROQ_API_KEY_4': '',  # Clear
            'GROQ_API_KEY_5': ''   # Clear
        }, clear=False):
            with patch('groq.Groq') as mock_groq_class:
                mock_client1 = MagicMock()
                mock_client2 = MagicMock()
                
                mock_groq_class.side_effect = [mock_client1, mock_client2]
                
                # First call fails with auth error
                mock_client1.chat.completions.create.side_effect = Exception("401 Unauthorized")
                
                # Second call succeeds
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"success": true}'
                mock_response.choices[0].finish_reason = "stop"
                mock_client2.chat.completions.create.return_value = mock_response
                
                provider = GroqProvider(use_multi_key=True)
                with pytest.raises(GroqProviderError) as failure:
                    provider.generate("Test prompt")
                assert failure.value.retryable is False
                assert failure.value.category == "authentication"
                mock_client1.chat.completions.create.assert_called_once()
                mock_client2.chat.completions.create.assert_not_called()
                # First credential should be marked invalid
                status = provider.get_scheduler_status()
                assert status['valid_credentials'] == 1


class TestGroqProviderJSONParsing:
    """Test that Groq provider responses can be parsed by extractor."""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client."""
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            yield mock_client
    
    def test_valid_json_response(self, mock_groq_client):
        """Test that valid JSON response is returned as-is."""
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
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = valid_json
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        result = provider.generate("Test prompt")
        
        # Should be parseable as JSON
        parsed = json.loads(result)
        assert "concepts" in parsed
        assert len(parsed["concepts"]) == 1
        assert parsed["concepts"][0]["concept_name"] == "Test"
    
    def test_malformed_json_not_caught_by_provider(self, mock_groq_client):
        """Provider should return response as-is; extractor handles JSON errors."""
        malformed_json = '{"concepts": [incomplete'
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = malformed_json
        mock_response.choices[0].finish_reason = "stop"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        result = provider.generate("Test prompt")
        
        # Provider returns response even if it's malformed
        # Extractor will catch the JSON decode error
        assert result == malformed_json
    
    def test_no_silent_mock_fallback(self, mock_groq_client):
        """Test that provider never falls back to mock responses."""
        mock_groq_client.chat.completions.create.side_effect = Exception("API failure")
        
        provider = GroqProvider(api_key="test-key", use_multi_key=False)
        
        # Should raise error, not return empty mock response
        with pytest.raises(RuntimeError):
            provider.generate("Test prompt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestExplicitGroqErrors:
    """SDK-shaped errors, mocked requests, and no live API calls."""

    @staticmethod
    def error(status, code="request_error", message="Request rejected", headers=None):
        import httpx
        from groq import APIStatusError
        response = httpx.Response(status, headers=headers or {},
                                  request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"))
        return APIStatusError(message, response=response,
                              body={"error": {"code": code, "message": message}})

    @staticmethod
    def response(finish_reason="stop"):
        return Mock(
            choices=[Mock(message=Mock(content='{"concepts": []}'), finish_reason=finish_reason)],
            model="openai/gpt-oss-120b",
            usage=Mock(prompt_tokens=12, completion_tokens=7, total_tokens=19),
        )

    @staticmethod
    def provider(error=None, multi=False):
        with patch("groq.Groq") as constructor:
            client = constructor.return_value
            provider = GroqProvider(api_key="test-secret-credential", use_multi_key=False)
        if error is not None:
            client.chat.completions.create.side_effect = error
        if multi:
            credential = Mock(api_key="test-secret-credential", key_id="key_1")
            provider.key_pool = Mock(credentials=[credential])
            provider.key_pool.wait_for_available_credential.return_value = credential
            provider._create_client = Mock(return_value=client)
        return provider, client

    @pytest.mark.parametrize("multi", [False, True])
    @pytest.mark.parametrize("status,code,category", [
        (400, "model_decommissioned", "permanent_model"),
        (404, "model_not_found", "permanent_model"),
        (400, "invalid_request_error", "permanent_request"),
        (422, "unprocessable_entity", "permanent_request"),
        (413, "request_too_large", "permanent_request"),
        (401, "invalid_api_key", "authentication"),
        (403, "permission_denied", "authorization"),
    ])
    def test_permanent_errors_are_not_retried_or_rotated(self, multi, status, code, category):
        provider, client = self.provider(self.error(status, code), multi=multi)
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        error = failure.value
        assert not error.retryable
        assert error.category == category
        assert error.status_code == status
        assert error.error_code == code
        client.chat.completions.create.assert_called_once()
        if multi:
            provider.key_pool.wait_for_available_credential.assert_called_once()
            provider.key_pool.handle_transient_error.assert_not_called()
            provider.key_pool.handle_rate_limit.assert_not_called()
            if status == 401:
                provider.key_pool.handle_auth_error.assert_called_once()
            else:
                provider.key_pool.handle_auth_error.assert_not_called()

    def test_single_401_invalidates_credential_and_prevents_another_network_attempt(self):
        provider, client = self.provider(self.error(401, "invalid_api_key"))
        for _ in range(2):
            with pytest.raises(GroqProviderError):
                provider.generate("test")
        assert provider.credential_is_valid is False
        client.chat.completions.create.assert_called_once()

    @pytest.mark.parametrize("header,expected", [
        ({"Retry-After": "2.5"}, 2.5),
        ({"retry-after-ms": "1250"}, 1.25),
        ({"Retry-After": "invalid"}, None),
    ])
    def test_rate_limit_metadata(self, header, expected):
        provider, client = self.provider(self.error(429, "rate_limit_exceeded", headers=header))
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        assert failure.value.category == "rate_limit"
        assert failure.value.retryable
        assert failure.value.retry_after == expected
        assert failure.value.error_code == "rate_limit_exceeded"
        assert provider.last_error_metadata["retry_after"] == expected
        client.chat.completions.create.assert_called_once()

    def test_http_date_retry_after(self):
        from datetime import datetime, timedelta, timezone
        from email.utils import format_datetime
        header = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=60), usegmt=True)
        provider, _ = self.provider(self.error(429, headers={"Retry-After": header}))
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        assert 58 <= failure.value.retry_after <= 61
        assert failure.value.retry_after_header == header

    def test_rate_limit_cooldown_does_not_invalidate_credentials(self):
        provider, client = self.provider(multi=True)
        client.chat.completions.create.side_effect = [
            self.error(429, "rate_limit_exceeded", headers={"Retry-After": "2.5"}),
            self.response(),
        ]
        assert provider.generate("test") == '{"concepts": []}'
        credential = provider.key_pool.credentials[0]
        provider.key_pool.handle_rate_limit.assert_called_once_with(credential, 3)
        provider.key_pool.handle_auth_error.assert_not_called()
        assert client.chat.completions.create.call_count == 2

    @pytest.mark.parametrize("kind", ["server", "network"])
    def test_transient_errors_retry_and_preserve_success_metadata(self, kind):
        import httpx
        error = self.error(503, "service_unavailable") if kind == "server" else httpx.ConnectError("Connection failed")
        provider, client = self.provider(multi=True)
        client.chat.completions.create.side_effect = [error, self.response()]
        with patch("time.sleep") as sleep:
            assert provider.generate("test") == '{"concepts": []}'
        assert client.chat.completions.create.call_count == 2
        assert provider.last_error_metadata["category"] == "transient_" + kind
        assert provider.last_error_metadata["retryable"] is True
        provider.key_pool.handle_auth_error.assert_not_called()
        assert sleep.call_count == 1
        assert provider.last_response_metadata == {
            "finish_reason": "stop", "model": "openai/gpt-oss-120b",
            "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
        }

    def test_exhausted_transient_error_keeps_code_and_retry_after(self):
        provider, client = self.provider(
            self.error(503, "service_unavailable", headers={"Retry-After": "7"}), multi=True,
        )
        with patch("time.sleep"), pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        assert client.chat.completions.create.call_count == provider.max_retries
        assert failure.value.retryable
        assert failure.value.error_code == "service_unavailable"
        assert failure.value.retry_after == 7

    @pytest.mark.parametrize("multi", [False, True])
    def test_diagnostics_and_logs_redact_credentials(self, multi, caplog):
        secret = "test-secret-credential"
        message = f"Rejected {secret}; Authorization: Bearer hidden-token; api_key=other-secret"
        provider, _ = self.provider(self.error(401, "invalid_api_key", message), multi=multi)
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        rendered = str(failure.value) + json.dumps(provider.last_error_metadata) + caplog.text
        assert secret not in rendered
        assert "hidden-token" not in rendered
        assert "other-secret" not in rendered
        assert failure.value.__suppress_context__
        assert failure.value.error_code == "invalid_api_key"

    def test_valid_json_and_finish_reason_behavior_are_unchanged(self):
        provider, client = self.provider()
        client.chat.completions.create.return_value = self.response()
        assert json.loads(provider.generate("test")) == {"concepts": []}
        request = client.chat.completions.create.call_args.kwargs
        assert request["model"] == "openai/gpt-oss-120b"
        assert request["response_format"] == {"type": "json_object"}
        client.chat.completions.create.return_value = self.response("length")
        with pytest.raises(ValueError, match="truncated"):
            provider.generate("test")
        assert provider.last_response_metadata["finish_reason"] == "length"
        assert provider.last_response_metadata["usage"]["total_tokens"] == 19


    def test_sdk_network_exception_is_retryable(self):
        import httpx
        from groq import APIConnectionError
        error = APIConnectionError(request=httpx.Request("POST", "https://api.groq.com"))
        provider, _ = self.provider(error)
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        assert failure.value.category == "transient_network"
        assert failure.value.retryable is True

    def test_client_creation_error_is_sanitized_and_not_rotated(self):
        provider, _ = self.provider(multi=True)
        provider._create_client.side_effect = self.error(
            400, "model_decommissioned", "Rejected test-secret-credential",
        )
        with pytest.raises(GroqProviderError) as failure:
            provider.generate("test")
        provider._create_client.assert_called_once()
        assert failure.value.retryable is False
        assert "test-secret-credential" not in str(failure.value)
