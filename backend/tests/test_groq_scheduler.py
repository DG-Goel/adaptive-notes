"""
Unit tests for Groq multi-key scheduler.

All tests use mocked credentials and responses - no real API calls.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.extraction.groq_scheduler import (
    CredentialState,
    GroqKeyPool,
    load_groq_credentials,
    redact_api_key
)


class TestCredentialRedaction:
    """Test API key redaction for safe logging"""
    
    def test_redact_normal_key(self):
        """Redacts middle of key, shows first and last 4 chars"""
        key = "gsk_1234567890abcdefghij"
        redacted = redact_api_key(key)
        assert redacted == "gsk_...ghij"
        assert "1234567890abcdef" not in redacted
    
    def test_redact_short_key(self):
        """Short keys are fully redacted"""
        key = "short"
        redacted = redact_api_key(key)
        assert redacted == "***"
    
    def test_redact_empty_key(self):
        """Empty keys are redacted"""
        assert redact_api_key("") == "***"
        assert redact_api_key(None) == "***"


class TestCredentialState:
    """Test credential state tracking"""
    
    def test_initial_state(self):
        """New credential is available and valid"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        assert cred.is_valid
        assert cred.is_available()
        assert cred.consecutive_failures == 0
    
    def test_record_success(self):
        """Recording success updates state"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        cred.consecutive_failures = 2
        cred.last_error = "Some error"
        
        cred.record_success()
        
        assert cred.consecutive_failures == 0
        assert cred.last_error is None
        assert cred.total_requests == 1
        assert cred.last_request_time is not None
    
    def test_record_failure_without_cooldown(self):
        """Failure increments counters"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        
        cred.record_failure("Test error")
        
        assert cred.consecutive_failures == 1
        assert cred.total_failures == 1
        assert cred.last_error == "Test error"
        assert cred.cooldown_until is None
    
    def test_record_failure_with_cooldown(self):
        """Failure with cooldown sets unavailable period"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        
        cred.record_failure("Rate limit", cooldown_seconds=60)
        
        assert cred.consecutive_failures == 1
        assert cred.cooldown_until is not None
        assert not cred.is_available()
    
    def test_exponential_backoff(self):
        """Consecutive failures cause exponential backoff"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        
        # First failure
        cred.record_failure("Error 1")
        time.sleep(0.1)  # Small delay to ensure timestamp difference
        assert not cred.is_available()  # 2^1 = 2 second backoff
        
        # Simulate time passing
        cred.last_request_time = datetime.now() - timedelta(seconds=3)
        assert cred.is_available()
        
        # Second failure
        cred.record_failure("Error 2")
        assert not cred.is_available()  # 2^2 = 4 second backoff
    
    def test_mark_invalid(self):
        """Marking invalid makes credential permanently unavailable"""
        cred = CredentialState(key_id="key_1", api_key="test_key")
        
        cred.mark_invalid("Auth failed")
        
        assert not cred.is_valid
        assert not cred.is_available()
        assert "Auth failed" in cred.last_error


class TestGroqKeyPool:
    """Test key pool scheduling and state management"""
    
    def test_initialization_single_key(self):
        """Pool initializes with single key"""
        pool = GroqKeyPool(["key1"])
        assert len(pool.credentials) == 1
        assert pool.credentials[0].key_id == "key_1"
    
    def test_initialization_multiple_keys(self):
        """Pool initializes with multiple keys"""
        pool = GroqKeyPool(["key1", "key2", "key3"])
        assert len(pool.credentials) == 3
        assert pool.credentials[0].key_id == "key_1"
        assert pool.credentials[2].key_id == "key_3"
    
    def test_initialization_empty_keys_fails(self):
        """Pool requires at least one key"""
        with pytest.raises(ValueError, match="At least one API key"):
            GroqKeyPool([])
    
    def test_round_robin_scheduling(self):
        """Credentials are selected in round-robin order"""
        pool = GroqKeyPool(["key1", "key2", "key3"])
        
        cred1 = pool.get_next_credential()
        cred2 = pool.get_next_credential()
        cred3 = pool.get_next_credential()
        cred4 = pool.get_next_credential()
        
        assert cred1.key_id == "key_1"
        assert cred2.key_id == "key_2"
        assert cred3.key_id == "key_3"
        assert cred4.key_id == "key_1"  # Wraps around
    
    def test_skips_unavailable_credentials(self):
        """Round-robin skips credentials in cooldown"""
        pool = GroqKeyPool(["key1", "key2", "key3"])
        
        # Put key_2 in cooldown
        pool.credentials[1].record_failure("Rate limit", cooldown_seconds=60)
        
        cred1 = pool.get_next_credential()
        cred2 = pool.get_next_credential()
        cred3 = pool.get_next_credential()
        
        # Should skip key_2
        assert cred1.key_id == "key_1"
        assert cred2.key_id == "key_3"
        assert cred3.key_id == "key_1"
    
    def test_all_credentials_unavailable(self):
        """Returns None when all credentials are unavailable"""
        pool = GroqKeyPool(["key1", "key2"])
        
        # Put both in cooldown
        pool.credentials[0].record_failure("Error", cooldown_seconds=60)
        pool.credentials[1].record_failure("Error", cooldown_seconds=60)
        
        cred = pool.get_next_credential()
        assert cred is None
    
    def test_handle_rate_limit(self):
        """Rate limit sets cooldown"""
        pool = GroqKeyPool(["key1"])
        cred = pool.credentials[0]
        
        pool.handle_rate_limit(cred, retry_after=30)
        
        assert cred.cooldown_until is not None
        assert not cred.is_available()
    
    def test_handle_auth_error(self):
        """Auth error marks credential invalid"""
        pool = GroqKeyPool(["key1", "key2"])
        cred = pool.credentials[0]
        
        pool.handle_auth_error(cred, "401 Unauthorized")
        
        assert not cred.is_valid
        assert not cred.is_available()
    
    def test_handle_transient_error(self):
        """Transient error records failure"""
        pool = GroqKeyPool(["key1"])
        cred = pool.credentials[0]
        
        pool.handle_transient_error(cred, "Connection timeout")
        
        assert cred.consecutive_failures == 1
        assert cred.total_failures == 1
    
    def test_record_success(self):
        """Success resets failure count"""
        pool = GroqKeyPool(["key1"])
        cred = pool.credentials[0]
        cred.consecutive_failures = 3
        
        pool.record_success(cred)
        
        assert cred.consecutive_failures == 0
        assert cred.total_requests == 1
    
    def test_get_status(self):
        """Status returns credential states with redacted keys"""
        pool = GroqKeyPool(["gsk_1234567890", "gsk_0987654321"])
        
        status = pool.get_status()
        
        assert status["total_credentials"] == 2
        assert status["valid_credentials"] == 2
        assert len(status["credentials"]) == 2
        assert "gsk_" in status["credentials"][0]["api_key_redacted"]
        assert "1234567890" not in status["credentials"][0]["api_key_redacted"]


class TestLoadGroqCredentials:
    """Test credential loading from environment"""
    
    def test_load_multiple_credentials(self):
        """Loads credentials from GROQ_API_KEY_1 through GROQ_API_KEY_5"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'key1',
            'GROQ_API_KEY_2': 'key2',
            'GROQ_API_KEY_3': 'key3'
        }, clear=True):
            keys = load_groq_credentials()
            assert len(keys) == 3
            assert keys[0] == 'key1'
            assert keys[2] == 'key3'
    
    def test_load_partial_credentials(self):
        """Loads only configured credentials"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': 'key1',
            'GROQ_API_KEY_3': 'key3',
            'GROQ_API_KEY_5': 'key5'
        }, clear=True):
            keys = load_groq_credentials()
            assert len(keys) == 3
            assert 'key1' in keys
            assert 'key3' in keys
            assert 'key5' in keys
    
    def test_load_backward_compatible(self):
        """Falls back to GROQ_API_KEY if numbered keys not found"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'single_key'
        }, clear=True):
            keys = load_groq_credentials()
            assert len(keys) == 1
            assert keys[0] == 'single_key'
    
    def test_load_no_credentials_fails(self):
        """Fails clearly if no credentials configured"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="No Groq API credentials configured"):
                load_groq_credentials()
    
    def test_strips_whitespace(self):
        """Strips whitespace from keys"""
        with patch.dict('os.environ', {
            'GROQ_API_KEY_1': '  key1  ',
            'GROQ_API_KEY_2': '\nkey2\n'
        }, clear=True):
            keys = load_groq_credentials()
            assert keys[0] == 'key1'
            assert keys[1] == 'key2'


class TestWaitForAvailableCredential:
    """Test waiting behavior when all credentials are temporarily unavailable"""
    
    def test_returns_immediately_if_available(self):
        """Returns immediately if credential is available"""
        pool = GroqKeyPool(["key1"])
        
        start = time.time()
        cred = pool.wait_for_available_credential(timeout=5.0)
        elapsed = time.time() - start
        
        assert cred is not None
        assert elapsed < 0.5  # Should be immediate
    
    def test_waits_and_returns_when_available(self):
        """Waits for credential to become available"""
        pool = GroqKeyPool(["key1"])
        
        # Put in very short cooldown
        pool.credentials[0].cooldown_until = datetime.now() + timedelta(seconds=0.5)
        
        cred = pool.wait_for_available_credential(timeout=2.0)
        
        assert cred is not None
        assert cred.key_id == "key_1"
    
    def test_times_out_if_none_available(self):
        """Returns None immediately when all credentials permanently invalid"""
        pool = GroqKeyPool(["key1"])
        
        # Mark as invalid (permanently unavailable)
        pool.credentials[0].mark_invalid("Test")
        
        start = time.time()
        cred = pool.wait_for_available_credential(timeout=0.5)
        elapsed = time.time() - start
        
        assert cred is None
        # Should return immediately since no credentials will become available
        assert elapsed < 0.1


class TestSecretRedaction:
    """Test that secrets are never logged"""
    
    def test_status_redacts_keys(self):
        """Status output redacts API keys"""
        pool = GroqKeyPool(["gsk_secret123456", "gsk_secret789012"])
        status = pool.get_status()
        
        status_str = str(status)
        assert "secret123456" not in status_str
        assert "secret789012" not in status_str
        assert "gsk_" in status_str  # Prefix should be visible
    
    def test_credential_state_does_not_expose_key(self):
        """CredentialState doesn't expose full key in common operations"""
        cred = CredentialState(key_id="key_1", api_key="gsk_secretkey123")
        
        # The actual API key is stored internally (necessary for HTTP requests)
        # but should never appear in logs or status outputs
        # This test verifies the principle: redact_api_key() is used for display
        redacted = redact_api_key(cred.api_key)
        assert "secretkey" not in redacted  # Middle part should be redacted
        assert redacted.startswith("gsk_")
        assert redacted.endswith("...y123")  # Last 4 chars of "gsk_secretkey123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
