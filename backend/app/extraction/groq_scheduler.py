"""
Multi-key Groq request scheduler with quota awareness.

IMPORTANT: Groq rate limits are enforced at the ORGANIZATION level, not per API key.
Multiple keys from the same organization will share the same quota and will NOT
bypass rate limits.

This scheduler is designed for scenarios where:
1. You have API keys from DIFFERENT organizations (different account owners)
2. Each organization has independent rate limits
3. You have explicit permission from each key owner to use their quota

Using multiple keys from the same organization to evade rate limits violates
Groq's terms of service and will not work anyway.
"""

import time
import random
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock


# Configure logging with safe redaction
logger = logging.getLogger(__name__)


def redact_api_key(api_key: str) -> str:
    """
    Redact API key for safe logging.
    
    Shows only first 4 and last 4 characters.
    """
    if not api_key or len(api_key) < 12:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"


@dataclass
class CredentialState:
    """
    State tracking for a single API credential.
    
    Attributes:
        key_id: Safe identifier (e.g., "key_1")
        api_key: Actual API key (never logged)
        last_request_time: Timestamp of last request
        cooldown_until: Time until which this credential is in cooldown
        consecutive_failures: Count of consecutive failures
        total_requests: Total requests made with this credential
        total_failures: Total failures encountered
        last_error: Last error message (sanitized)
        is_valid: Whether credential is valid (not auth-failed)
    """
    key_id: str
    api_key: str
    last_request_time: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    last_error: Optional[str] = None
    is_valid: bool = True
    
    def is_available(self) -> bool:
        """Check if credential is available for use"""
        if not self.is_valid:
            return False
        
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False
        
        # Exponential backoff for consecutive failures
        if self.consecutive_failures > 0:
            backoff_seconds = min(2 ** self.consecutive_failures, 300)  # Max 5 minutes
            if self.last_request_time:
                backoff_until = self.last_request_time + timedelta(seconds=backoff_seconds)
                if datetime.now() < backoff_until:
                    return False
        
        return True
    
    def record_success(self):
        """Record successful request"""
        self.last_request_time = datetime.now()
        self.total_requests += 1
        self.consecutive_failures = 0
        self.last_error = None
    
    def record_failure(self, error: str, cooldown_seconds: Optional[int] = None):
        """Record failed request with optional cooldown"""
        self.last_request_time = datetime.now()
        self.total_requests += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.last_error = error[:100]  # Truncate error message
        
        if cooldown_seconds:
            self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
    
    def mark_invalid(self, reason: str):
        """Mark credential as permanently invalid (auth failure)"""
        self.is_valid = False
        self.last_error = reason[:100]
        logger.error(f"Credential {self.key_id} marked invalid: {reason}")


class GroqKeyPool:
    """
    Pool of Groq API credentials with round-robin scheduling and quota awareness.
    
    WARNING: This assumes credentials are from DIFFERENT organizations.
    Using multiple keys from the same organization will NOT bypass rate limits.
    """
    
    def __init__(self, api_keys: List[str], max_retries: int = 3):
        """
        Initialize key pool.
        
        Args:
            api_keys: List of API keys from different organizations
            max_retries: Maximum retry attempts per request
        """
        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.credentials: List[CredentialState] = []
        for i, key in enumerate(api_keys, 1):
            key_id = f"key_{i}"
            self.credentials.append(CredentialState(key_id=key_id, api_key=key))
            logger.info(f"Registered {key_id}: {redact_api_key(key)}")
        
        self.max_retries = max_retries
        self.current_index = 0
        self.lock = Lock()
        
        logger.info(f"GroqKeyPool initialized with {len(self.credentials)} credentials")
        logger.warning(
            "IMPORTANT: Multi-key usage assumes keys from DIFFERENT organizations. "
            "Groq rate limits are enforced at organization level. "
            "Using multiple keys from the same organization will NOT bypass limits."
        )
    
    def get_next_credential(self) -> Optional[CredentialState]:
        """
        Get next available credential using round-robin with availability check.
        
        Returns:
            Next available credential or None if all are unavailable
        """
        with self.lock:
            # Try each credential starting from current index
            for _ in range(len(self.credentials)):
                cred = self.credentials[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.credentials)
                
                if cred.is_available():
                    return cred
            
            # No credentials available
            return None
    
    def get_credential_by_id(self, key_id: str) -> Optional[CredentialState]:
        """Get credential by its safe ID"""
        with self.lock:
            for cred in self.credentials:
                if cred.key_id == key_id:
                    return cred
        return None
    
    def handle_rate_limit(self, cred: CredentialState, retry_after: Optional[int] = None):
        """
        Handle rate limit error for a credential.
        
        Args:
            cred: Credential that hit rate limit
            retry_after: Seconds to wait before retry (from Retry-After header)
        """
        cooldown = retry_after if retry_after else 60  # Default 60s cooldown
        cred.record_failure(f"Rate limit (429), cooldown for {cooldown}s", cooldown)
        
        logger.warning(
            f"{cred.key_id} hit rate limit. "
            f"Cooldown until {cred.cooldown_until.isoformat() if cred.cooldown_until else 'unknown'}. "
            f"Consecutive failures: {cred.consecutive_failures}"
        )
    
    def handle_auth_error(self, cred: CredentialState, error: str):
        """
        Handle authentication error.
        
        Marks credential as permanently invalid.
        """
        cred.mark_invalid(f"Auth error: {error}")
        
        # Check if any credentials remain valid
        valid_count = sum(1 for c in self.credentials if c.is_valid)
        if valid_count == 0:
            logger.error("All credentials are invalid! No API access available.")
        else:
            logger.info(f"{valid_count}/{len(self.credentials)} credentials remain valid")
    
    def handle_transient_error(self, cred: CredentialState, error: str):
        """
        Handle transient error (connection, timeout, server error).
        
        Records failure with exponential backoff.
        """
        cred.record_failure(error)
        logger.warning(
            f"{cred.key_id} transient error: {error[:50]}. "
            f"Consecutive failures: {cred.consecutive_failures}"
        )
    
    def record_success(self, cred: CredentialState):
        """Record successful request"""
        cred.record_success()
        logger.debug(f"{cred.key_id} request successful. Total: {cred.total_requests}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all credentials.
        
        Returns:
            Dictionary with credential states (API keys redacted)
        """
        with self.lock:
            # Determine next credential that will be selected by round-robin
            # Start from current_index and find first available
            next_cred = None
            for i in range(len(self.credentials)):
                idx = (self.current_index + i) % len(self.credentials)
                if self.credentials[idx].is_available():
                    next_cred = self.credentials[idx].key_id
                    break
            
            return {
                "total_credentials": len(self.credentials),
                "valid_credentials": sum(1 for c in self.credentials if c.is_valid),
                "available_credentials": sum(1 for c in self.credentials if c.is_available()),
                "next_credential": next_cred,
                "credentials": [
                    {
                        "credential_id": c.key_id,
                        "key_id": c.key_id,  # Keep for backward compat
                        "api_key_redacted": redact_api_key(c.api_key),
                        "is_valid": c.is_valid,
                        "is_available": c.is_available(),
                        "consecutive_failures": c.consecutive_failures,
                        "total_requests": c.total_requests,
                        "total_failures": c.total_failures,
                        "cooldown_until": c.cooldown_until.isoformat() if c.cooldown_until else None,
                        "last_error": c.last_error
                    }
                    for c in self.credentials
                ]
            }
    
    def wait_for_available_credential(self, timeout: float = 60.0) -> Optional[CredentialState]:
        """
        Wait for a credential to become available.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Available credential or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            cred = self.get_next_credential()
            if cred:
                return cred
            
            # Calculate minimum wait time
            with self.lock:
                min_wait = float('inf')
                for c in self.credentials:
                    if not c.is_valid:
                        continue
                    
                    if c.cooldown_until:
                        wait = (c.cooldown_until - datetime.now()).total_seconds()
                        if wait > 0 and wait < min_wait:
                            min_wait = wait
                    
                    if c.consecutive_failures > 0 and c.last_request_time:
                        backoff = min(2 ** c.consecutive_failures, 300)
                        wait_until = c.last_request_time + timedelta(seconds=backoff)
                        wait = (wait_until - datetime.now()).total_seconds()
                        if wait > 0 and wait < min_wait:
                            min_wait = wait
                
                if min_wait == float('inf') or min_wait <= 0:
                    # No valid credentials or all permanently failed
                    logger.error("No credentials available and none will become available")
                    return None
                
                # Wait with jitter
                wait_time = min(min_wait + random.uniform(0, 1), timeout - (time.time() - start_time))
                if wait_time > 0:
                    logger.info(f"All credentials unavailable. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        logger.error(f"Timeout waiting for available credential after {timeout}s")
        return None


def load_groq_credentials() -> List[str]:
    """
    Load Groq API credentials from environment variables.
    
    Reads GROQ_API_KEY_1 through GROQ_API_KEY_5.
    Ignores empty or missing variables.
    
    Returns:
        List of API keys
        
    Raises:
        ValueError: If no valid credentials found
    """
    import os
    
    keys = []
    for i in range(1, 6):
        key = os.getenv(f"GROQ_API_KEY_{i}")
        if key and key.strip():
            keys.append(key.strip())
            logger.info(f"Loaded GROQ_API_KEY_{i}: {redact_api_key(key)}")
        else:
            logger.debug(f"GROQ_API_KEY_{i} not configured")
    
    if not keys:
        # Fall back to single GROQ_API_KEY for backward compatibility
        single_key = os.getenv("GROQ_API_KEY")
        if single_key and single_key.strip():
            keys.append(single_key.strip())
            logger.info(f"Loaded GROQ_API_KEY (backward compatibility): {redact_api_key(single_key)}")
    
    if not keys:
        raise ValueError(
            "No Groq API credentials configured. "
            "Set GROQ_API_KEY_1 through GROQ_API_KEY_5 or GROQ_API_KEY environment variable."
        )
    
    logger.info(f"Loaded {len(keys)} Groq API credential(s)")
    return keys
