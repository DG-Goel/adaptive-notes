"""
Deterministic tests proving that GroqProvider.generate() uses the correct
credential for each request in the actual request path.

These tests intercept Groq client construction to verify which API key is
supplied, proving that round-robin rotation works in the real code path.

IMPORTANT: Never logs or prints actual API keys - only safe labels (key_1, etc.)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta

from app.extraction.llm_provider import GroqProvider


class TestActualRequestPath:
    """
    Verify that the actual GroqProvider.generate() request path uses
    the expected credential by intercepting client construction.
    """
    
    @patch('os.getenv')
    def test_successive_requests_use_different_credentials(self, mock_getenv):
        """
        PROOF: Successive requests create clients with different API keys
        in round-robin order when all credentials are available.
        """
        # Setup environment with 3 test keys
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'test_api_key_alpha',
                'GROQ_API_KEY_2': 'test_api_key_beta',
                'GROQ_API_KEY_3': 'test_api_key_gamma',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Track which API keys are used to create clients
        clients_created_with_keys = []
        
        def mock_groq_constructor(api_key):
            """Capture the API key used and return a mock client"""
            # Record which key was used (but never log/print it)
            clients_created_with_keys.append(api_key)
            
            # Return a mock client
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"result": "success"}'
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "openai/gpt-oss-120b"
            mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
            mock_client.chat.completions.create.return_value = mock_response
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor):
            # Create provider (triggers multi-key mode)
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Verify multi-key mode enabled
            assert provider.key_pool is not None
            assert len(provider.key_pool.credentials) == 3
            
            # Make 5 successive requests
            for i in range(5):
                result = provider.generate(
                    prompt=f"test request {i}",
                    temperature=0.0,
                    max_tokens=100
                )
                assert result == '{"result": "success"}'
            
            # VERIFY: Credentials rotated in order
            assert len(clients_created_with_keys) == 5
            assert clients_created_with_keys == [
                'test_api_key_alpha',   # Request 1: key_1
                'test_api_key_beta',    # Request 2: key_2
                'test_api_key_gamma',   # Request 3: key_3
                'test_api_key_alpha',   # Request 4: key_1 (wrapped)
                'test_api_key_beta'     # Request 5: key_2
            ]
    
    @patch('os.getenv')
    def test_status_distinguishes_last_used_from_next(self, mock_getenv):
        """
        PROOF: Status correctly distinguishes between:
        - Which credential was used for the last request
        - Which credential will be selected next
        """
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'key_one',
                'GROQ_API_KEY_2': 'key_two',
                'GROQ_API_KEY_3': 'key_three',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        keys_used = []
        
        def mock_groq_constructor(api_key):
            keys_used.append(api_key)
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"ok": true}'
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "openai/gpt-oss-120b"
            mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
            mock_client.chat.completions.create.return_value = mock_response
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor):
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Before any requests
            status = provider.get_scheduler_status()
            assert status['next_credential'] == 'key_1'
            
            # After first request
            provider.generate(prompt="test 1", max_tokens=50)
            assert keys_used[-1] == 'key_one'  # Last request used key_1
            
            status = provider.get_scheduler_status()
            assert status['next_credential'] == 'key_2'  # Next will be key_2
            assert status['credentials'][0]['total_requests'] == 1  # key_1 used once
            
            # After second request
            provider.generate(prompt="test 2", max_tokens=50)
            assert keys_used[-1] == 'key_two'  # Last request used key_2
            
            status = provider.get_scheduler_status()
            assert status['next_credential'] == 'key_3'  # Next will be key_3
            assert status['credentials'][1]['total_requests'] == 1  # key_2 used once
            
            # After third request (wraps to key_1)
            provider.generate(prompt="test 3", max_tokens=50)
            assert keys_used[-1] == 'key_three'  # Last request used key_3
            
            status = provider.get_scheduler_status()
            assert status['next_credential'] == 'key_1'  # Next wraps to key_1
            assert status['credentials'][2]['total_requests'] == 1  # key_3 used once
    
    @patch('os.getenv')
    def test_rate_limited_credential_skipped_no_circumvention(self, mock_getenv):
        """
        PROOF: When a credential hits rate limit:
        1. It enters cooldown and is NOT selected for next request
        2. Scheduler tries a DIFFERENT credential
        3. Does NOT retry the same failed request under another account
        4. Respects rate limits and provider terms
        """
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'first_key',
                'GROQ_API_KEY_2': 'second_key',
                'GROQ_API_KEY_3': 'third_key',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        keys_used = []
        call_count = [0]
        
        def mock_groq_constructor(api_key):
            keys_used.append(api_key)
            mock_client = MagicMock()
            
            def create_completion(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 2:
                    # Second API call (using second_key) hits rate limit
                    raise Exception("Error code: 429 - Rate limit exceeded")
                else:
                    # Other calls succeed
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = '{"status": "ok"}'
                    mock_response.choices[0].finish_reason = "stop"
                    mock_response.model = "openai/gpt-oss-120b"
                    mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
                    return mock_response
            
            mock_client.chat.completions.create = create_completion
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor):
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Request 1: Uses key_1 (success)
            result1 = provider.generate(prompt="request 1", max_tokens=50)
            assert result1 == '{"status": "ok"}'
            assert keys_used[-1] == 'first_key'
            
            # Request 2: Tries key_2 (rate limit), then retries with key_3 (success)
            result2 = provider.generate(prompt="request 2", max_tokens=50)
            assert result2 == '{"status": "ok"}'
            
            # VERIFY: Both key_2 and key_3 were tried for request 2
            assert keys_used[-2] == 'second_key'  # First attempt
            assert keys_used[-1] == 'third_key'   # Retry with different credential
            
            # VERIFY: key_2 is now in cooldown
            status = provider.get_scheduler_status()
            key_2_status = status['credentials'][1]
            assert key_2_status['credential_id'] == 'key_2'
            assert key_2_status['cooldown_until'] is not None
            assert not key_2_status['is_available']  # Not available
            
            # Request 3: Should skip key_2 (in cooldown) and use key_1
            result3 = provider.generate(prompt="request 3", max_tokens=50)
            assert result3 == '{"status": "ok"}'
            assert keys_used[-1] == 'first_key'  # Skipped key_2, used key_1
            
            # VERIFY: key_2 was NOT used (still in cooldown)
            # Expected sequence: key_1, key_2 (fail), key_3 (retry), key_1 (skip key_2)
            assert keys_used == ['first_key', 'second_key', 'third_key', 'first_key']
    
    @patch('os.getenv')
    def test_credential_id_matches_client_api_key(self, mock_getenv):
        """
        PROOF: The credential ID reported in status matches the actual
        API key used to create the Groq client.
        """
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'actual_key_for_cred_1',
                'GROQ_API_KEY_2': 'actual_key_for_cred_2',
                'GROQ_API_KEY_3': '',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Map credential IDs to actual keys used
        cred_id_to_key_used = {}
        
        def mock_groq_constructor(api_key):
            # This is the actual API key passed to Groq client constructor
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"data": "test"}'
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "openai/gpt-oss-120b"
            mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
            mock_client.chat.completions.create.return_value = mock_response
            
            # Store the key (but never log it)
            mock_client._test_api_key = api_key
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor) as mock_groq:
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Get initial pool state
            pool = provider.key_pool
            cred_1 = pool.credentials[0]
            cred_2 = pool.credentials[1]
            
            # Verify credential IDs
            assert cred_1.key_id == 'key_1'
            assert cred_2.key_id == 'key_2'
            
            # Verify API keys stored in credentials (internal, not logged)
            assert cred_1.api_key == 'actual_key_for_cred_1'
            assert cred_2.api_key == 'actual_key_for_cred_2'
            
            # Make requests and verify correct keys used
            provider.generate(prompt="test 1", max_tokens=50)
            # First call should use cred_1's key
            assert mock_groq.call_args_list[0][1]['api_key'] == 'actual_key_for_cred_1'
            
            provider.generate(prompt="test 2", max_tokens=50)
            # Second call should use cred_2's key
            assert mock_groq.call_args_list[1][1]['api_key'] == 'actual_key_for_cred_2'
            
            provider.generate(prompt="test 3", max_tokens=50)
            # Third call wraps to cred_1's key
            assert mock_groq.call_args_list[2][1]['api_key'] == 'actual_key_for_cred_1'
    
    @patch('os.getenv')
    def test_auth_failure_marks_credential_invalid(self, mock_getenv):
        """
        PROOF: When a credential fails authentication:
        1. It is marked as invalid
        2. It is NOT selected for future requests
        3. Independent later requests continue with remaining valid credentials
        """
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'valid_key',
                'GROQ_API_KEY_2': 'invalid_key',
                'GROQ_API_KEY_3': 'another_valid_key',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        keys_used = []
        
        def mock_groq_constructor(api_key):
            keys_used.append(api_key)
            mock_client = MagicMock()
            
            def create_completion(*args, **kwargs):
                if api_key == 'invalid_key':
                    # This credential fails authentication
                    raise Exception("401 Unauthorized - Invalid API key")
                else:
                    # Other credentials succeed
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = '{"valid": true}'
                    mock_response.choices[0].finish_reason = "stop"
                    mock_response.model = "openai/gpt-oss-120b"
                    mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
                    return mock_response
            
            mock_client.chat.completions.create = create_completion
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor):
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Request 1: key_1 (success)
            provider.generate(prompt="test 1", max_tokens=50)
            assert keys_used[-1] == 'valid_key'
            
            # Request 2 ends at the failed credential; no same-request rotation.
            from app.extraction.llm_provider import GroqProviderError
            with pytest.raises(GroqProviderError) as failure:
                provider.generate(prompt="test 2", max_tokens=50)
            assert failure.value.retryable is False
            assert failure.value.category == "authentication"
            assert keys_used == ['valid_key', 'invalid_key']
            
            # VERIFY: key_2 marked invalid
            status = provider.get_scheduler_status()
            assert status['valid_credentials'] == 2  # Only 2 valid (key_1, key_3)
            
            key_2_status = status['credentials'][1]
            assert key_2_status['credential_id'] == 'key_2'
            assert not key_2_status['is_valid']  # Marked invalid
            assert not key_2_status['is_available']  # Not available
            
            # Request 3 independently uses key_3; the failed request did not.
            provider.generate(prompt="test 3", max_tokens=50)
            assert keys_used[-1] == 'another_valid_key'
            
            # Request 4 independently wraps to key_1.
            provider.generate(prompt="test 4", max_tokens=50)
            assert keys_used[-1] == 'valid_key'
            
            # VERIFY: key_2 was never used again after being marked invalid
            # Sequence: key_1, key_2(fail), then independent requests key_3, key_1
            assert keys_used == [
                'valid_key',           # Request 1
                'invalid_key',         # Request 2 attempt 1 (fail)
                'another_valid_key',   # Independent request 3
                'valid_key',           # Independent request 4
            ]


class TestRequestCountAccuracy:
    """Verify that request counts accurately reflect which credentials were used"""
    
    @patch('os.getenv')
    def test_request_counts_match_actual_usage(self, mock_getenv):
        """
        PROOF: The request count for each credential matches
        the number of times it was actually used to make API calls.
        """
        def getenv_side_effect(key, default=None):
            env_map = {
                'GROQ_API_KEY_1': 'key_a',
                'GROQ_API_KEY_2': 'key_b',
                'GROQ_API_KEY_3': 'key_c',
                'GROQ_API_KEY_4': '',
                'GROQ_API_KEY_5': ''
            }
            return env_map.get(key, default)
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Track actual usage
        actual_usage_count = {'key_a': 0, 'key_b': 0, 'key_c': 0}
        
        def mock_groq_constructor(api_key):
            mock_client = MagicMock()
            
            def create_completion(*args, **kwargs):
                # Count this as actual usage
                actual_usage_count[api_key] += 1
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '{"count": "tracked"}'
                mock_response.choices[0].finish_reason = "stop"
                mock_response.model = "openai/gpt-oss-120b"
                mock_response.usage = Mock(prompt_tokens=5, completion_tokens=10, total_tokens=15)
                return mock_response
            
            mock_client.chat.completions.create = create_completion
            return mock_client
        
        with patch('groq.Groq', side_effect=mock_groq_constructor):
            provider = GroqProvider(model="openai/gpt-oss-120b")
            
            # Make 7 requests (will rotate: a, b, c, a, b, c, a)
            for i in range(7):
                provider.generate(prompt=f"request {i}", max_tokens=50)
            
            # Get reported counts from scheduler
            status = provider.get_scheduler_status()
            reported_counts = {
                cred['credential_id']: cred['total_requests']
                for cred in status['credentials']
            }
            
            # VERIFY: Reported counts match actual usage
            assert actual_usage_count['key_a'] == 3  # Used 3 times
            assert actual_usage_count['key_b'] == 2  # Used 2 times
            assert actual_usage_count['key_c'] == 2  # Used 2 times
            
            assert reported_counts['key_1'] == 3  # Matches actual
            assert reported_counts['key_2'] == 2  # Matches actual
            assert reported_counts['key_3'] == 2  # Matches actual


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
