"""
LLM provider abstraction for knowledge extraction.

Provides a unified interface for different LLM backends
and enables testing with mock responses.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate response from prompt.
        
        Args:
            prompt: User prompt
            system: Optional system message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider.
    
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            api_key: Optional API key (defaults to env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Install with: pip install openai"
            )
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """Generate response using OpenAI API"""
        
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content



class GroqProviderError(RuntimeError):
    """Sanitized provider failure with an explicit retry contract for callers."""

    def __init__(self, message, *, category, retryable, status_code=None,
                 error_code=None, retry_after=None, retry_after_header=None):
        super().__init__("Groq API call failed: " + message)
        self.category = category
        self.retryable = retryable
        self.status_code = status_code
        self.error_code = error_code
        self.retry_after = retry_after
        self.retry_after_header = retry_after_header

    def diagnostics(self):
        return {
            "category": self.category, "retryable": self.retryable,
            "status_code": self.status_code, "error_code": self.error_code,
            "retry_after": self.retry_after,
            "retry_after_header": self.retry_after_header,
            "message": str(self),
        }


class GroqProvider(LLMProvider):
    """
    Groq LLM provider using OpenAI-compatible client.
    
    Supports both single-key (backward compatible) and multi-key operation.
    
    For single-key: Set GROQ_API_KEY environment variable or pass api_key parameter.
    For multi-key: Set GROQ_API_KEY_1 through GROQ_API_KEY_5 environment variables.
    
    IMPORTANT: Groq rate limits are enforced at the ORGANIZATION level.
    Multi-key operation only helps if keys are from DIFFERENT organizations.
    """
    
    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
        api_key: Optional[str] = None,
        tokens_per_minute: int = 8000,  # Default TPM limit for on-demand tier
        use_multi_key: bool = True,  # Enable multi-key by default if configured
        max_retries: int = 3
    ):
        """
        Initialize Groq provider.
        
        Args:
            model: Model name (default: openai/gpt-oss-120b)
            api_key: Optional single API key (for backward compatibility)
            tokens_per_minute: TPM rate limit for this model/tier
            use_multi_key: Whether to use multi-key scheduling if available
            max_retries: Maximum retry attempts for transient errors
            
        Raises:
            ValueError: If no API key is configured
        """
        self.model = model
        self.tokens_per_minute = tokens_per_minute
        self.max_retries = max_retries
        self.key_pool = None
        self.client = None
        
        # Try multi-key setup first if enabled
        if use_multi_key and not api_key:
            try:
                from app.extraction.groq_scheduler import load_groq_credentials, GroqKeyPool
                credentials = load_groq_credentials()
                if len(credentials) > 1:
                    self.key_pool = GroqKeyPool(credentials, max_retries=max_retries)
                    import logging
                    logging.getLogger(__name__).info(
                        f"Multi-key mode enabled with {len(credentials)} credentials"
                    )
                else:
                    # Only one key, use single-key mode
                    api_key = credentials[0]
                    import logging
                    logging.getLogger(__name__).info("Single key found, using single-key mode")
            except (ValueError, ImportError) as e:
                # Fall back to single-key mode
                import logging
                logging.getLogger(__name__).info(f"Multi-key setup failed: {e}, falling back to single-key")
        
        # Single-key setup
        if not self.key_pool:
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            
            if not self.api_key:
                raise ValueError(
                    "Groq API key required. "
                    "Set GROQ_API_KEY environment variable or pass api_key parameter. "
                    "For multi-key operation, set GROQ_API_KEY_1 through GROQ_API_KEY_5."
                )
            
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Groq package not installed. "
                    "Install with: pip install groq"
                )
    

    def _sanitize_error(self, text):
        """Remove configured credentials and common credential-bearing diagnostics."""
        import re
        secrets = [getattr(self, "api_key", None)]
        if self.key_pool:
            secrets.extend(cred.api_key for cred in self.key_pool.credentials)
        for secret in sorted((value for value in secrets if isinstance(value, str) and value),
                             key=len, reverse=True):
            text = text.replace(secret, "[REDACTED]")
        text = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", text)
        text = re.sub(r"\b(?:gsk_|sk-)[A-Za-z0-9_-]+", "[REDACTED]", text)
        text = re.sub(
            r"""(?ix)(["']?(?:api[_-]?key|access[_-]?token|authorization|password|secret)["']?\s*[:=]\s*)["']?[^\s,;}"']+["']?""",
            r"\1[REDACTED]", text,
        )
        return text[:1000]

    def _classify_error(self, error):
        """Prefer SDK status/body fields; use conservative legacy-message fallbacks."""
        import re
        import httpx
        from groq import APIConnectionError

        status = getattr(error, "status_code", None)
        if not isinstance(status, int):
            response = getattr(error, "response", None)
            status = getattr(response, "status_code", None)
        if not isinstance(status, int):
            status = None
        body = getattr(error, "body", None)
        details = body.get("error", body) if isinstance(body, dict) else {}
        if not isinstance(details, dict):
            details = {}
        code = details.get("code", getattr(error, "code", None))
        code = code if isinstance(code, str) else None
        message = str(error)
        body_message = details.get("message")
        if isinstance(body_message, str) and body_message not in message:
            message += ": " + body_message
        lowered = message.lower()
        if status is None:
            match = re.search(r"\b(4\d\d|5\d\d)\b", lowered)
            if match:
                status = int(match.group(1))
        model_codes = {"model_decommissioned", "model_not_found", "model_not_available",
                       "model_not_supported"}
        if (code or "").lower() in model_codes or "model_decommissioned" in lowered:
            category, retryable = "permanent_model", False
            if code is None:
                code = "model_decommissioned"
        elif status == 401 or code == "invalid_api_key" or (status is None and "unauthorized" in lowered):
            category, retryable = "authentication", False
        elif status == 403:
            category, retryable = "authorization", False
        elif "tokens per day" in lowered or "daily quota" in lowered:
            category, retryable = "permanent_request", False
        elif status == 429:
            category, retryable = "rate_limit", True
        elif status == 408:
            category, retryable = "transient_network", True
        elif status == 409:
            category, retryable = "transient_request", True
        elif status is not None and 400 <= status < 500:
            category = "permanent_model" if status == 404 and "model" in lowered else "permanent_request"
            retryable = False
        elif status is not None and 500 <= status < 600:
            category, retryable = "transient_server", True
        elif isinstance(error, (APIConnectionError, httpx.TransportError, ConnectionError, TimeoutError)):
            category, retryable = "transient_network", True
        elif "authentication" in lowered or "invalid api key" in lowered:
            category, retryable = "authentication", False
        elif "rate_limit" in lowered or "rate limit" in lowered:
            category, retryable = "rate_limit", True
        elif "timeout" in lowered or "connection" in lowered:
            category, retryable = "transient_network", True
        else:
            # Preserve retry behavior for unstructured legacy provider exceptions.
            category, retryable = "unknown", True
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        raw_retry = None
        if headers is not None:
            value = headers.get("retry-after") or headers.get("Retry-After")
            if isinstance(value, str):
                raw_retry = self._sanitize_error(value)
        return GroqProviderError(
            self._sanitize_error(message), category=category, retryable=retryable,
            status_code=status, error_code=self._sanitize_error(code) if code else None,
            retry_after=self._extract_retry_after(error), retry_after_header=raw_retry,
        )


    def _create_client(self, api_key: str):
        """Create Groq client for a specific API key"""
        try:
            from groq import Groq
            return Groq(api_key=api_key)
        except ImportError:
            raise ImportError("Groq package not installed. Install with: pip install groq")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate response using Groq API.
        
        Automatically uses multi-key scheduling if configured, otherwise single-key.
        
        Args:
            prompt: User prompt
            system: Optional system message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If API call fails after retries
            ValueError: If response is empty or malformed
        """
        if self.key_pool:
            return self._generate_multi_key(prompt, system, temperature, max_tokens)
        else:
            return self._generate_single_key(prompt, system, temperature, max_tokens)
    
    def _generate_single_key(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using single-key mode (backward compatible)"""
        if getattr(self, "_credential_failure", None) is not None:
            raise self._credential_failure from None
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
        except Exception as e:
            classified = self._classify_error(e)
            self.last_error_metadata = classified.diagnostics()
            if classified.status_code == 401:
                self.credential_is_valid = False
                self._credential_failure = classified
            raise classified from None
        
        return self._extract_response_content(response)
    
    def _generate_multi_key(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using multi-key scheduling with retry logic"""
        import logging
        import time
        import random
        
        logger = logging.getLogger(__name__)
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        
        for attempt in range(self.max_retries):
            # Get next available credential
            cred = self.key_pool.wait_for_available_credential(timeout=60.0)
            
            if not cred:
                raise RuntimeError(
                    "No Groq credentials available after waiting. "
                    "All credentials may be in cooldown or invalid."
                )
            
            try:
                # Classify client-creation failures through the same sanitized path.
                client = self._create_client(cred.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Success - record and return
                self.key_pool.record_success(cred)
                return self._extract_response_content(response)
                
            except Exception as e:
                classified = self._classify_error(e)
                self.last_error_metadata = classified.diagnostics()
                last_error = classified

                if not classified.retryable:
                    if classified.status_code == 401:
                        self.key_pool.handle_auth_error(cred, str(classified))
                    # Permanent model/request/auth failures end this request; no rotation.
                    raise classified from None

                if classified.category == "rate_limit":
                    import math
                    delay = classified.retry_after
                    cooldown = max(1, math.ceil(delay)) if delay is not None else None
                    self.key_pool.handle_rate_limit(cred, cooldown)
                    logger.warning("Rate limit on %s; scheduler cooldown applied", cred.key_id)
                else:
                    self.key_pool.handle_transient_error(cred, str(classified))
                    logger.warning("Transient Groq failure on %s: %s", cred.key_id, classified.category)
                    if attempt < self.max_retries - 1:
                        time.sleep((2 ** attempt) + random.uniform(0, 1))

        if last_error is not None:
            raise last_error from None
        raise GroqProviderError(
            "No attempts configured", category="permanent_request", retryable=False,
        )

    def _extract_response_content(self, response) -> str:
        """
        Extract and validate response content.
        
        Raises:
            ValueError: If response is truncated, incomplete, or invalid
        """
        choice = response.choices[0]
        content = choice.message.content
        finish_reason = choice.finish_reason
        
        # Store metadata for diagnostics FIRST (before raising errors)
        usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        } if response.usage else None
        
        self.last_response_metadata = {
            "finish_reason": finish_reason,
            "model": response.model,
            "usage": usage_info
        }
        
        # Check for truncation - this means output was cut off mid-response
        if finish_reason == "length":
            # Include token usage in error for diagnostics
            tokens_msg = ""
            if usage_info:
                tokens_msg = f" (input: {usage_info['prompt_tokens']}, output: {usage_info['completion_tokens']}, total: {usage_info['total_tokens']})"
            
            raise ValueError(
                f"Response truncated due to max_tokens limit{tokens_msg}. "
                f"Increase max_tokens or reduce input size."
            )
        elif finish_reason not in ("stop", "end_turn"):
            raise ValueError(
                f"Unexpected finish_reason: {finish_reason}. "
                f"Expected 'stop' or 'end_turn'."
            )
        
        if not content:
            raise ValueError("Groq API returned empty response")
        
        # Additional validation: Check if JSON looks incomplete DUE TO TRUNCATION
        # Only check for truncation patterns - let extractor handle truly malformed JSON
        # This catches cases where finish_reason is 'stop' but JSON was truncated
        content_stripped = content.strip()
        
        # Check for truncation in JSON (with or without markdown fences)
        if (content_stripped.startswith('{') or 
            content_stripped.startswith('[') or 
            content_stripped.startswith('```')):
            # Only check for clear truncation indicators, not all JSON errors
            if self._has_truncation_indicators(content_stripped):
                tokens_msg = ""
                if usage_info:
                    tokens_msg = f" (output tokens: {usage_info['completion_tokens']})"
                
                raise ValueError(
                    f"Response appears to contain incomplete JSON{tokens_msg}. "
                    f"This may indicate truncation. Consider reducing input size."
                )
        
        return content
    
    def _has_truncation_indicators(self, content: str) -> bool:
        """
        Check if JSON content has clear truncation indicators.
        
        This is a CONSERVATIVE check focused on obvious truncation patterns.
        The goal is to catch responses that were clearly cut off mid-generation,
        while letting malformed-but-complete JSON pass through to the extractor
        for better error messages.
        
        Clear truncation signs:
        - Missing closing markdown fence
        - Ends with structural punctuation (comma, colon, open bracket/brace)
        - Has explicit "..." truncation markers
        
        NOT considered truncation (let extractor handle):
        - Unbalanced braces/brackets alone (could be malformed JSON)
        - Missing closing brace/bracket at end (could be malformed)
        
        Args:
            content: JSON string
            
        Returns:
            True if content has clear truncation indicators, False otherwise
        """
        original_content = content.strip()
        
        # Check for incomplete markdown fences FIRST
        if original_content.startswith('```'):
            lines = original_content.split('\n')
            if len(lines) < 3:
                return True  # Too short to be complete
            
            # Count fence markers
            fence_count = sum(1 for line in lines if line.strip().startswith('```'))
            
            # Should have opening and closing fence (at least 2)
            if fence_count < 2:
                return True  # Missing closing fence - clear truncation
            
            # Extract content between first pair of fences for further checks
            start_idx = None
            end_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith('```'):
                    if start_idx is None:
                        start_idx = i + 1
                    elif end_idx is None:
                        end_idx = i
                        break
            
            if start_idx is not None and end_idx is not None:
                content = '\n'.join(lines[start_idx:end_idx]).strip()
            else:
                content = original_content  # Shouldn't happen, but fallback
        else:
            content = original_content
        
        # Check for explicit truncation patterns (strong indicators)
        # These are clear signs the response was cut off
        strong_truncation_patterns = [
            '...',     # Explicit truncation marker
            ', "',     # Cut off after comma, starting new field
            ': "',     # Cut off after colon, starting value
            ': [',     # Cut off after colon, starting array
            ': {',     # Cut off after colon, starting object
        ]
        
        # Valid JSON may contain unmatched braces or escaped quote characters
        # inside strings. Character-count heuristics cannot establish truncation.
        try:
            __import__('json').loads(content)
            return False
        except (ValueError, TypeError):
            pass
        # Check last 50 characters for these patterns
        last_part = content[-50:] if len(content) > 50 else content
        for pattern in strong_truncation_patterns:
            if last_part.endswith(pattern) or last_part.endswith(pattern.rstrip('"')):
                return True
        
        # Check if ends with structural punctuation that suggests truncation
        # (but ONLY if it's at the very end with nothing after)
        endings_suggesting_truncation = [',', ':', '[', '{']
        stripped_end = content.rstrip()
        if stripped_end and stripped_end[-1] in endings_suggesting_truncation:
            # This is a strong sign of truncation - response ended mid-structure
            return True
        
        # Check for unbalanced quotes (indicates truncation mid-string)
        # This is a STRONG indicator because quotes must be paired in valid JSON
        quote_count = content.count('"')
        if quote_count % 2 != 0:
            # Odd number of quotes - likely truncated inside a string
            return True
        
        # Check for unbalanced braces/brackets ONLY if content looks cleanly structured
        # (i.e., ends with valid JSON characters, not mid-word)
        # This distinguishes truncation from malformed JSON
        last_char = content.rstrip()[-1] if content.rstrip() else ''
        
        if last_char in '{}[],"':  # Valid JSON ending characters
            # Content ends cleanly - check for structural problems
            if content.startswith('{'):
                if content.count('{') != content.count('}'):
                    return True
            elif content.startswith('['):
                if content.count('[') != content.count(']'):
                    return True
        
        # If ends with alphanumeric or other characters, it's likely malformed, not truncated
        # Let the extractor handle it
        
        return False
    
    def _is_complete_json(self, content: str) -> bool:
        """
        Check if JSON content appears complete (basic heuristic).
        
        DEPRECATED: Use _has_truncation_indicators instead.
        This is a fast check before attempting full JSON parsing.
        
        Args:
            content: JSON string
            
        Returns:
            True if JSON appears complete, False if likely truncated
        """
        # Delegate to new method, inverting the result
        return not self._has_truncation_indicators(content)

    
    def _extract_retry_after(self, exception) -> Optional[float]:
        """Preserve seconds, fractional seconds, HTTP dates, or millisecond headers."""
        import math
        import re
        from datetime import datetime, timezone
        from email.utils import parsedate_to_datetime

        response = getattr(exception, "response", None)
        headers = getattr(response, "headers", None)
        if headers is not None:
            for name, divisor in (("retry-after-ms", 1000.0), ("retry-after", 1.0)):
                raw = headers.get(name) or headers.get(name.title())
                if not isinstance(raw, (str, int, float)):
                    continue
                try:
                    seconds = float(raw) / divisor
                    if math.isfinite(seconds) and seconds >= 0:
                        return seconds
                except (ValueError, TypeError):
                    if name == "retry-after":
                        try:
                            date = parsedate_to_datetime(raw)
                            if date.tzinfo is None:
                                date = date.replace(tzinfo=timezone.utc)
                            return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
                        except (ValueError, TypeError, OverflowError):
                            pass
        match = re.search(r"retry[_\s-]after[:=\s]+(\d+(?:\.\d+)?)",
                          str(exception), re.IGNORECASE)
        return float(match.group(1)) if match else None

    def get_scheduler_status(self) -> Optional[Dict]:
        """
        Get status of multi-key scheduler if enabled.
        
        Returns:
            Scheduler status dict or None if single-key mode
        """
        if self.key_pool:
            return self.key_pool.get_status()
        return None


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider using google-genai SDK.
    
    Requires GEMINI_API_KEY environment variable.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        tokens_per_minute: int = 15000  # Default TPM limit for free tier
    ):
        """
        Initialize Gemini provider.
        
        Args:
            model: Model name (default: gemini-2.0-flash-exp)
            api_key: Optional API key (defaults to env var)
            tokens_per_minute: TPM rate limit for this model/tier
            
        Raises:
            ValueError: If API key is not provided and not in environment
        """
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.tokens_per_minute = tokens_per_minute
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )
        
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            
            # Initialize client
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate response using Gemini API.
        
        Args:
            prompt: User prompt
            system: Optional system message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If API call fails
            ValueError: If response is empty or malformed
        """
        
        # Build contents list
        contents = []
        
        if system:
            # System instruction is separate from contents in Gemini
            config = self.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",  # Request JSON output
                system_instruction=system
            )
        else:
            config = self.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json"
            )
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
        except Exception as e:
            error_str = str(e)
            
            # Check for specific error types
            # Note: Order matters - check most specific errors first
            if "401" in error_str or "authentication" in error_str.lower():
                raise RuntimeError(f"Gemini authentication error: {error_str}") from e
            elif "404" in error_str and "model" in error_str.lower():
                # Model not found - not a transient error, do not retry
                raise RuntimeError(f"Gemini model not found: {error_str}") from e
            elif "429" in error_str or ("quota" in error_str.lower() and "rate" not in error_str.lower()):
                # Check if it's daily quota or per-minute rate limit
                if "per day" in error_str.lower() or "TPD" in error_str:
                    raise RuntimeError(f"Gemini daily quota exhausted (tokens per day): {error_str}") from e
                else:
                    raise RuntimeError(f"Gemini rate_limit error (TPM): {error_str}") from e
            elif "rate" in error_str.lower() or "too many requests" in error_str.lower():
                # Rate limit error
                raise RuntimeError(f"Gemini rate_limit error (TPM): {error_str}") from e
            elif "400" in error_str or "invalid" in error_str.lower():
                raise RuntimeError(f"Gemini API request error: {error_str}") from e
            else:
                raise RuntimeError(f"Gemini API call failed: {type(e).__name__}: {e}") from e
        
        # Extract response content
        if not response or not response.candidates:
            raise ValueError("Gemini API returned empty response (no candidates)")
        
        candidate = response.candidates[0]
        
        # Check finish reason
        finish_reason = str(candidate.finish_reason) if hasattr(candidate, 'finish_reason') else "UNKNOWN"
        
        # Gemini finish reasons: STOP, MAX_TOKENS, SAFETY, RECITATION, OTHER
        # STOP indicates normal successful completion
        if "MAX_TOKENS" in finish_reason:
            raise ValueError(
                f"Response truncated due to max_tokens limit ({max_tokens}). "
                f"Increase max_tokens or reduce input size."
            )
        elif "SAFETY" in finish_reason:
            raise ValueError(
                f"Response blocked by safety filter (finish_reason: {finish_reason}). "
                f"Content may have triggered content filtering."
            )
        elif "RECITATION" in finish_reason:
            raise ValueError(
                f"Response blocked due to recitation (finish_reason: {finish_reason}). "
                f"Content may be too similar to training data."
            )
        elif finish_reason not in ["STOP", "1", "FinishReason.STOP"]:  # STOP (enum or string) is normal
            # Log unexpected finish reason but don't fail unless it's clearly an error
            if finish_reason != "UNKNOWN" and "STOP" not in finish_reason:
                print(f"[WARNING] Unexpected finish_reason: {finish_reason}")
        
        # Extract text content
        if not candidate.content or not candidate.content.parts:
            raise ValueError("Gemini API returned empty content")
        
        # Combine all text parts
        text_parts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if not text_parts:
            raise ValueError("Gemini API returned no text content in response")
        
        content = "".join(text_parts)
        
        # Store metadata for diagnostics (optional attribute)
        self.last_response_metadata = {
            "finish_reason": finish_reason,
            "model": self.model,
            "usage": {
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else None,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else None,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else None,
            } if hasattr(response, 'usage_metadata') and response.usage_metadata else None
        }
        
        return content


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider for local models.
    
    Uses the Ollama HTTP API to interact with locally-running models.
    Requires Ollama to be installed and running locally.
    """
    
    def __init__(
        self,
        model: str = "granite4:micro",
        base_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        tokens_per_minute: int = 100000,  # Local models have no hard TPM limit
        request_timeout: float = 300.0  # 5 minutes for local inference
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (default: granite4:micro)
            base_url: Ollama server URL (default: http://localhost:11434)
            api_key: Optional API key (not used by default Ollama setup)
            tokens_per_minute: TPM limit (local models typically have no limit)
            request_timeout: Request timeout in seconds (default: 300s for slow local generation)
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Allow override from environment
        self.model = os.getenv("OLLAMA_MODEL", model)
        self.base_url = os.getenv("OLLAMA_BASE_URL", base_url).rstrip("/")
        self.api_key = api_key
        self.tokens_per_minute = tokens_per_minute
        self.request_timeout = request_timeout
        
        # Verify httpx is available
        try:
            import httpx
            self.httpx = httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. "
                "Install with: pip install httpx"
            )
        
        # Verify Ollama is reachable and model exists
        self._verify_setup()
    
    def _verify_setup(self):
        """
        Verify that Ollama server is reachable and the model is available.
        
        Raises:
            RuntimeError: If server is unreachable or model not found
        """
        try:
            # Check server is alive
            response = self.httpx.get(
                f"{self.base_url}/api/tags",
                timeout=10.0
            )
            response.raise_for_status()
            
            # Check model exists
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Model name might have tag suffix
            model_found = any(
                self.model == name or self.model.split(":")[0] == name.split(":")[0]
                for name in model_names
            )
            
            if not model_found:
                available = ", ".join(model_names) if model_names else "none"
                raise RuntimeError(
                    f"Ollama model '{self.model}' not found. "
                    f"Available models: {available}. "
                    f"Pull the model with: ollama pull {self.model}"
                )
                
        except RuntimeError:
            # Re-raise RuntimeError (including model not found)
            raise
        except Exception as e:
            # All other exceptions mean we can't connect
            raise RuntimeError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                f"Ensure Ollama is running. Error: {type(e).__name__}: {e}"
            ) from e
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate response using Ollama API.
        
        Args:
            prompt: User prompt
            system: Optional system message
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If API call fails
            ValueError: If response is empty, malformed, or truncated
        """
        
        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",  # Request JSON output
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens  # Ollama uses num_predict instead of max_tokens
            }
        }
        
        try:
            response = self.httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.request_timeout
            )
            response.raise_for_status()
            
        except self.httpx.TimeoutException as e:
            raise RuntimeError(
                f"Ollama request timeout after {self.request_timeout}s. "
                f"Local model may be generating slowly. Consider increasing request_timeout."
            ) from e
        except self.httpx.ConnectError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                f"Ensure Ollama is running."
            ) from e
        except self.httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_text = e.response.text[:200]
            
            if status_code == 404:
                if "model" in error_text.lower():
                    raise RuntimeError(
                        f"Ollama model '{self.model}' not found. "
                        f"Pull the model with: ollama pull {self.model}"
                    ) from e
                else:
                    raise RuntimeError(f"Ollama API endpoint not found: {error_text}") from e
            else:
                raise RuntimeError(
                    f"Ollama API error ({status_code}): {error_text}"
                ) from e
        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {type(e).__name__}: {e}") from e
        
        # Parse response
        try:
            data = response.json()
        except Exception as e:
            raise ValueError(f"Failed to parse Ollama response as JSON: {e}") from e
        
        # Extract message content
        message = data.get("message")
        if not message:
            raise ValueError("Ollama API returned response without 'message' field")
        
        content = message.get("content", "")
        if not content:
            raise ValueError("Ollama API returned empty content")
        
        # Check for truncation
        done = data.get("done", False)
        done_reason = data.get("done_reason", "")
        
        # Ollama may truncate if context length exceeded
        if not done:
            raise ValueError(
                "Ollama response incomplete (done=false). "
                "Generation may have been interrupted."
            )
        
        # Check if truncated due to token limit
        # Ollama uses "length" or "stop" as done_reason
        if done_reason == "length":
            raise ValueError(
                f"Response truncated due to max_tokens limit ({max_tokens}). "
                f"Increase max_tokens or reduce input size."
            )
        
        # Store metadata for diagnostics
        self.last_response_metadata = {
            "model": data.get("model", self.model),
            "done": done,
            "done_reason": done_reason,
            "total_duration": data.get("total_duration"),
            "load_duration": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
        }
        
        return content


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for testing.
    
    Returns canned responses based on prompt matching.
    """
    
    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        default_response: Optional[str] = None
    ):
        """
        Initialize mock provider.
        
        Args:
            responses: Dict mapping prompt substrings to responses
            default_response: Default response if no match found
        """
        self.responses = responses or {}
        self.default_response = default_response or self._get_empty_response()
        self.call_count = 0
        self.last_prompt = None
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4000
    ) -> str:
        """Return canned response based on prompt matching"""
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Try to match prompt to canned responses
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # Return default response if no match
        return self.default_response
    
    def _get_empty_response(self) -> str:
        """Get empty but valid JSON response"""
        return json.dumps({
            "concepts": [],
            "definitions": [],
            "explanations": [],
            "examples": [],
            "facts": [],
            "formulas": [],
            "procedures": [],
            "relationships": []
        })
    
    def reset(self):
        """Reset call counter and last prompt"""
        self.call_count = 0
        self.last_prompt = None
