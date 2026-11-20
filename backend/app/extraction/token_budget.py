"""
Token budget management for LLM extraction.

Provides token estimation and budget allocation to stay within
provider limits (both per-request and rate limits like TPM).
"""

import time
from app.extraction.quota_policy import UTILIZATION_FRACTION
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class TokenBudget:
    """Token budget allocation for a request"""
    input_tokens: int
    max_output_tokens: int
    total_tokens: int
    tpm_limit: int
    is_safe: bool
    reason: str = ""


class TokenBudgetManager:
    """
    Manages token budgets to stay within provider limits.
    
    Responsibilities:
    - Estimate input tokens from text
    - Calculate safe output token limits
    - Track TPM usage over time
    - Recommend backoff when approaching limits
    """
    
    def __init__(
        self,
        tokens_per_minute: int = 8000,
        chars_per_token: float = 4.0,
        system_overhead_tokens: int = 150,  # System prompt + schema overhead
        safety_margin: float = UTILIZATION_FRACTION  # Operator hard 85% limit
    ):
        """
        Initialize budget manager.
        
        Args:
            tokens_per_minute: TPM rate limit
            chars_per_token: Character to token ratio estimate
            system_overhead_tokens: Fixed overhead for system prompt + response schema
            safety_margin: Requested fraction, clamped to the operator's hard 85% limit.
        """
        self.tpm_limit = tokens_per_minute
        self.chars_per_token = chars_per_token
        self.system_overhead = system_overhead_tokens
        if not 0 < safety_margin <= 1:
            raise ValueError('safety_margin must be in (0, 1]')
        self.safety_margin = min(safety_margin,UTILIZATION_FRACTION)
        
        # Track rolling TPM usage
        self.recent_requests = []  # List of (timestamp, tokens_used)
        self.last_rate_limit_time = None
    
    def estimate_input_tokens(self, text: str, include_system: bool = True) -> int:
        """
        Estimate input tokens from text.
        
        Args:
            text: Input text (user prompt)
            include_system: Whether to include system overhead
            
        Returns:
            Estimated token count
        """
        text_tokens = int(len(text) / self.chars_per_token)
        
        if include_system:
            return text_tokens + self.system_overhead
        
        return text_tokens
    

    def estimate_request_tokens(self, user_text: str, system_text: str) -> int:
        """Estimate the complete chat request; this is NOT an exact tokenizer count.

        No verified GPT-OSS tokenizer/vocabulary is bundled with this project.
        Use UTF-8 bytes / 3.5 (or a caller's more conservative ratio), rounded up
        per message, rather than the legacy chars / 4. Reserve 32 tokens per
        message for framing/role, 16 for assistant priming, and 64 for JSON-mode
        request overhead. These are safety estimates, not provider guarantees.
        Context and instructions are never shortened here.
        """
        import math
        ratio = min(self.chars_per_token, 3.5)
        if ratio <= 0:
            raise ValueError("Token estimation ratio must be positive")
        messages = [user_text]
        if system_text:
            messages.insert(0, system_text)
        return sum(math.ceil(len(text.encode("utf-8")) / ratio) + 32
                   for text in messages) + 16 + 64

    def calculate_budget(
        self,
        input_text: str,
        min_output_tokens: int = 500,
        preferred_output_tokens: int = 4000,
        system_text: Optional[str] = None
    ) -> TokenBudget:
        """
        Calculate safe token budget for a request.
        
        Strategy:
        - Estimate input tokens
        - Reserve output capacity (prefer preferred, minimum min)
        - Ensure total stays within TPM limit with safety margin
        
        Args:
            input_text: The user prompt text
            min_output_tokens: Minimum acceptable output tokens
            preferred_output_tokens: Preferred output token capacity
            system_text: Actual assembled system message. None preserves the legacy API;
                supply an empty string for a chat request with only a user message.
            
        Returns:
            TokenBudget with allocation
        """
        # Estimate input
        input_tokens = (self.estimate_input_tokens(input_text, include_system=True)
                        if system_text is None else self.estimate_request_tokens(input_text, system_text))
        
        # Calculate safe TPM limit
        safe_tpm = int(self.tpm_limit * self.safety_margin)
        
        # Calculate available tokens for output
        available_for_output = safe_tpm - input_tokens
        
        # Ensure preferred is at least minimum
        effective_preferred = max(preferred_output_tokens, min_output_tokens)
        
        # Determine output allocation
        if available_for_output >= effective_preferred:
            # Can use preferred
            output_tokens = effective_preferred
            is_safe = True
            reason = "Within budget"
        elif available_for_output >= min_output_tokens:
            # Use what's available
            output_tokens = available_for_output
            is_safe = True
            reason = f"Reduced to {output_tokens} tokens to fit budget"
        else:
            # Not enough space even for minimum
            output_tokens = min_output_tokens
            is_safe = False
            reason = f"Input too large: {input_tokens} tokens leaves only {available_for_output} for output (need {min_output_tokens} minimum)"
        
        total_tokens = input_tokens + output_tokens
        
        return TokenBudget(
            input_tokens=input_tokens,
            max_output_tokens=output_tokens,
            total_tokens=total_tokens,
            tpm_limit=safe_tpm,
            is_safe=is_safe,
            reason=reason
        )
    
    def record_request(self, tokens_used: int):
        """
        Record a completed request for TPM tracking.
        
        Args:
            tokens_used: Total tokens used in request
        """
        now = time.time()
        self.recent_requests.append((now, tokens_used))
        
        # Clean up requests older than 60 seconds
        cutoff = now - 60
        self.recent_requests = [
            (ts, tokens) for ts, tokens in self.recent_requests
            if ts > cutoff
        ]
    
    def get_current_tpm_usage(self) -> int:
        """
        Get current TPM usage (tokens in last 60 seconds).
        
        Returns:
            Token count used in rolling 60-second window
        """
        now = time.time()
        cutoff = now - 60
        
        return sum(
            tokens for ts, tokens in self.recent_requests
            if ts > cutoff
        )
    
    def recommend_delay(self, required_tokens: int) -> Optional[float]:
        """
        Recommend delay before next request to stay under TPM limit.
        
        Args:
            required_tokens: Tokens needed for next request
            
        Returns:
            Recommended delay in seconds, or None if no delay needed
        """
        current_usage = self.get_current_tpm_usage()
        
        if current_usage + required_tokens <= self.tpm_limit:
            return None
        
        # Calculate how long until oldest request expires
        if not self.recent_requests:
            return None
        
        now = time.time()
        oldest_ts, _ = self.recent_requests[0]
        time_until_expire = 60 - (now - oldest_ts)
        
        # Add small buffer
        return max(time_until_expire + 1, 5)
    
    def record_rate_limit_error(self):
        """Record that we hit a rate limit error."""
        self.last_rate_limit_time = time.time()
    
    def should_backoff(self) -> Tuple[bool, float]:
        """
        Check if we should back off due to recent rate limits.
        
        Returns:
            (should_wait, delay_seconds)
        """
        if self.last_rate_limit_time is None:
            return False, 0
        
        elapsed = time.time() - self.last_rate_limit_time
        
        # Exponential backoff: 10s, 20s, 30s
        if elapsed < 10:
            return True, 10 - elapsed
        elif elapsed < 30:
            return True, 30 - elapsed
        
        # Clear rate limit flag after 30 seconds
        self.last_rate_limit_time = None
        return False, 0
