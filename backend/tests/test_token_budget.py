"""
Tests for token budget management.

Verifies token estimation, budget allocation, rate limit tracking,
and backoff logic to prevent TPM violations.
"""

import time
import pytest
from app.extraction.token_budget import TokenBudgetManager, TokenBudget


class TestTokenEstimation:
    """Test token estimation from text"""
    
    def test_basic_estimation(self):
        """Estimate tokens from simple text"""
        manager = TokenBudgetManager(chars_per_token=4.0)
        
        text = "This is a test"  # 14 chars
        tokens = manager.estimate_input_tokens(text, include_system=False)
        
        # 14 / 4 = 3.5 -> 3 tokens
        assert tokens == 3
    
    def test_includes_system_overhead(self):
        """System overhead is added when requested"""
        manager = TokenBudgetManager(
            chars_per_token=4.0,
            system_overhead_tokens=150
        )
        
        text = "Test"  # 4 chars = 1 token
        tokens_with_system = manager.estimate_input_tokens(text, include_system=True)
        tokens_without = manager.estimate_input_tokens(text, include_system=False)
        
        assert tokens_with_system == 151  # 1 + 150
        assert tokens_without == 1


class TestBudgetCalculation:
    """Test token budget allocation"""
    
    def test_small_input_gets_preferred_budget(self):
        """Small inputs get full preferred output budget"""
        manager = TokenBudgetManager(
            tokens_per_minute=8000,
            chars_per_token=4.0,
            system_overhead_tokens=150,
            safety_margin=0.85
        )
        
        small_text = "Test" * 100  # 400 chars = 100 tokens + 150 overhead = 250 tokens
        budget = manager.calculate_budget(
            input_text=small_text,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        assert budget.is_safe
        assert budget.max_output_tokens == 4000
        assert budget.total_tokens <= 8000 * 0.85
    
    def test_large_input_gets_reduced_budget(self):
        """Large inputs get reduced output budget"""
        manager = TokenBudgetManager(
            tokens_per_minute=8000,
            chars_per_token=4.0,
            system_overhead_tokens=150,
            safety_margin=0.85
        )
        
        # Input: 4000 chars = 1000 tokens + 150 overhead = 1150 tokens
        # Safe TPM: 8000 * 0.85 = 6800
        # Available for output: 6800 - 1150 = 5650
        # Preferred is 4000, so should get 4000
        large_text = "Word " * 800  # 5 chars * 800 = 4000 chars / 4 = 1000 tokens
        budget = manager.calculate_budget(
            input_text=large_text,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        assert budget.is_safe
        assert budget.max_output_tokens == 4000
        assert budget.total_tokens <= 8000 * 0.85
    
    def test_excessive_input_marked_unsafe(self):
        """Inputs exceeding budget are marked unsafe"""
        manager = TokenBudgetManager(
            tokens_per_minute=8000,
            chars_per_token=4.0,
            system_overhead_tokens=150,
            safety_margin=0.85
        )
        
        # Massive input: exceeds safe TPM even with minimum output
        massive_text = "Word " * 10000  # 50000 chars / 4 = 12500 tokens
        budget = manager.calculate_budget(
            input_text=massive_text,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        assert not budget.is_safe
        assert "Input too large" in budget.reason


class TestTPMTracking:
    """Test tokens-per-minute tracking"""
    
    def test_records_request(self):
        """Requests are recorded for TPM tracking"""
        manager = TokenBudgetManager()
        
        manager.record_request(1000)
        usage = manager.get_current_tpm_usage()
        
        assert usage == 1000
    
    def test_rolling_window(self):
        """Old requests expire after 60 seconds"""
        manager = TokenBudgetManager()
        
        # Simulate old request
        manager.recent_requests.append((time.time() - 65, 1000))
        
        # Record new request
        manager.record_request(500)
        
        # Old request should be cleaned up
        usage = manager.get_current_tpm_usage()
        assert usage == 500
    
    def test_accumulates_within_window(self):
        """Multiple requests within window accumulate"""
        manager = TokenBudgetManager()
        
        manager.record_request(1000)
        manager.record_request(2000)
        manager.record_request(1500)
        
        usage = manager.get_current_tpm_usage()
        assert usage == 4500


class TestBackoffRecommendation:
    """Test rate limit backoff logic"""
    
    def test_no_delay_when_under_limit(self):
        """No delay needed when under TPM limit"""
        manager = TokenBudgetManager(tokens_per_minute=8000)
        
        manager.record_request(2000)
        delay = manager.recommend_delay(3000)
        
        assert delay is None  # 2000 + 3000 = 5000 < 8000
    
    def test_recommends_delay_when_exceeding(self):
        """Delay recommended when request would exceed TPM"""
        manager = TokenBudgetManager(tokens_per_minute=8000)
        
        manager.record_request(7000)
        delay = manager.recommend_delay(2000)
        
        assert delay is not None  # 7000 + 2000 = 9000 > 8000
        assert delay > 0
    
    def test_backoff_after_rate_limit_error(self):
        """Backoff triggered after rate limit error"""
        manager = TokenBudgetManager()
        
        manager.record_rate_limit_error()
        should_wait, delay = manager.should_backoff()
        
        assert should_wait
        assert delay > 0
    
    def test_backoff_clears_after_time(self):
        """Backoff flag clears after sufficient time"""
        manager = TokenBudgetManager()
        
        # Simulate old rate limit error
        manager.last_rate_limit_time = time.time() - 35
        
        should_wait, delay = manager.should_backoff()
        assert not should_wait
        assert manager.last_rate_limit_time is None  # Cleared


class TestSafetyMargin:
    """Test safety margin configuration"""
    
    def test_respects_safety_margin(self):
        """Budget stays within safety margin of TPM limit"""
        manager = TokenBudgetManager(
            tokens_per_minute=8000,
            safety_margin=0.80  # Use 80%
        )
        
        text = "Test"
        budget = manager.calculate_budget(
            input_text=text,
            preferred_output_tokens=7000
        )
        
        # Should not exceed 80% of 8000 = 6400
        assert budget.total_tokens <= 6400
        assert budget.tpm_limit == 6400


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_input(self):
        """Handle empty input text"""
        manager = TokenBudgetManager()
        
        budget = manager.calculate_budget(
            input_text="",
            preferred_output_tokens=1000
        )
        
        assert budget.is_safe
        # Should still include system overhead
        assert budget.input_tokens > 0
    
    def test_zero_preferred_tokens(self):
        """Handle zero preferred output tokens"""
        manager = TokenBudgetManager()
        
        budget = manager.calculate_budget(
            input_text="Test",
            min_output_tokens=100,
            preferred_output_tokens=0
        )
        
        # Should use minimum since preferred is 0
        assert budget.max_output_tokens == 100
    
    def test_no_recent_requests(self):
        """Handle empty request history"""
        manager = TokenBudgetManager()
        
        usage = manager.get_current_tpm_usage()
        assert usage == 0
        
        delay = manager.recommend_delay(1000)
        assert delay is None


class TestSystemPromptHandling:
    """Test proper handling of system prompt overhead"""
    
    def test_system_overhead_not_double_counted(self):
        """
        System overhead should be counted once via system_overhead_tokens,
        not by concatenating system prompt to input text.
        
        This test verifies the fix for the issue where passing
        prompt + system_prompt caused double-counting and reduced output budget.
        """
        manager = TokenBudgetManager(
            tokens_per_minute=8000,
            chars_per_token=4.0,
            system_overhead_tokens=150,
            safety_margin=0.85  # 6800 safe tokens
        )
        
        # Create a prompt that uses ~1933 tokens (matching real-world case)
        # This is 7732 characters
        user_prompt = "x" * 7732
        
        # Simulate actual system prompt length (~532 chars = 133 tokens)
        system_prompt = "x" * 532
        
        # WRONG way: concatenating prompts (old bug)
        # Input: (7732 + 532) / 4 + 150 = 2066 + 150 = 2216 tokens
        # Available: 6800 - 2216 = 4584 tokens
        # Gets 4000 preferred
        budget_wrong = manager.calculate_budget(
            input_text=user_prompt + system_prompt,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        # RIGHT way: pass only user prompt (system overhead added internally)
        # Input: 7732 / 4 + 150 = 1933 + 150 = 2083 tokens
        # Available: 6800 - 2083 = 4717 tokens
        # Gets 4000 preferred
        budget_right = manager.calculate_budget(
            input_text=user_prompt,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        # Both can afford 4000 in this case, but verify calculations
        assert budget_right.input_tokens == 2083
        assert budget_wrong.input_tokens == 2216
        
        # Now test with larger input where it matters
        # Create prompt that fills more of budget
        large_prompt = "x" * 11000  # 2750 tokens + 150 = 2900 input
        large_system = "x" * 1600   # 400 tokens
        
        # WRONG: (11000 + 1600) / 4 + 150 = 3150 + 150 = 3300 tokens input
        # Available: 6800 - 3300 = 3500 for output (less than 4000 preferred)
        budget_large_wrong = manager.calculate_budget(
            input_text=large_prompt + large_system,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        # RIGHT: 11000 / 4 + 150 = 2750 + 150 = 2900 tokens input
        # Available: 6800 - 2900 = 3900 for output (less than 4000 preferred)
        budget_large_right = manager.calculate_budget(
            input_text=large_prompt,
            min_output_tokens=500,
            preferred_output_tokens=4000
        )
        
        # Right way gets more output tokens
        assert budget_large_right.max_output_tokens > budget_large_wrong.max_output_tokens
        assert budget_large_right.max_output_tokens == 3900
        assert budget_large_wrong.max_output_tokens == 3500


class TestCompleteChatRequestBudget:
    def test_actual_system_growth_changes_input_and_output_budget(self):
        manager = TokenBudgetManager()
        small = manager.calculate_budget("user" * 1000, system_text="system")
        large = manager.calculate_budget("user" * 1000, system_text="system" * 1000)
        assert large.input_tokens > small.input_tokens
        assert large.max_output_tokens < small.max_output_tokens
        assert large.total_tokens <= large.tpm_limit
        assert small.max_output_tokens <= 4000
        assert large.max_output_tokens <= 4000

    def test_utf8_rounding_and_framing_are_included_without_fixed_system_overhead(self):
        import math
        manager = TokenBudgetManager(system_overhead_tokens=99999)
        expected = math.ceil(len("user".encode()) / 3.5) + math.ceil(len("system".encode()) / 3.5) + 2*32 + 16 + 64
        assert manager.estimate_request_tokens("user", "system") == expected
        assert manager.calculate_budget("user", system_text="system").input_tokens == expected
        assert manager.estimate_request_tokens("emoji", "😀") > manager.estimate_request_tokens("emoji", "a")

    def test_evidence_heavy_output_reservation_is_not_lowered_when_it_fits(self):
        manager = TokenBudgetManager(tokens_per_minute=20000)
        budget = manager.calculate_budget(
            "source text", system_text="grounding instructions",
            min_output_tokens=500, preferred_output_tokens=4000)
        assert budget.is_safe
        assert budget.max_output_tokens == 4000
        assert budget.total_tokens == budget.input_tokens + 4000

    def test_complete_request_that_cannot_fit_minimum_is_explicitly_unsafe(self):
        manager = TokenBudgetManager()
        system, user = "grounding " * 5000, "source " * 1000
        budget = manager.calculate_budget(user, system_text=system)
        assert not budget.is_safe
        assert "Input too large" in budget.reason
        assert budget.max_output_tokens == 500
        assert len(system) == len("grounding " * 5000)
        assert len(user) == len("source " * 1000)

    def test_extractor_budgets_the_same_complete_messages_it_sends(self):
        from unittest.mock import Mock, patch
        from app.extraction.extractor import KnowledgeExtractor
        from app.extraction.llm_provider import MockLLMProvider
        from app.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
        from app.models.knowledge import ExtractionChunk
        provider = MockLLMProvider()
        extractor = KnowledgeExtractor(provider, verbose=False)
        chunk = ExtractionChunk(chunk_id="test", source_units=["S1"], text_content="[S1] Source.")
        with patch.object(extractor.token_budget, "calculate_budget",
                          wraps=extractor.token_budget.calculate_budget) as budget:
            extractor._extract_from_chunk(chunk, "test")
        call = budget.call_args.kwargs
        assert call["system_text"] == EXTRACTION_SYSTEM_PROMPT
        assert call["input_text"] == build_extraction_prompt(
            chunk.text_content,
            chunk.chunk_id,
            allowed_source_ids=chunk.source_units,
        )
        assert call["preferred_output_tokens"] == 4000
        assert call["min_output_tokens"] == 500

    def test_unsafe_complete_request_never_calls_provider_or_truncates_prompt(self):
        from unittest.mock import Mock
        from app.extraction.extractor import KnowledgeExtractor
        from app.extraction.llm_provider import MockLLMProvider
        from app.models.knowledge import ExtractionChunk
        provider = MockLLMProvider()
        provider.generate = Mock()
        extractor = KnowledgeExtractor(provider, verbose=False)
        source = "huge source " * 10000
        chunk = ExtractionChunk(chunk_id="test", source_units=["S1"], text_content=source)
        with pytest.raises(ValueError, match="exceeds token budget"):
            extractor._extract_from_chunk(chunk, "test")
        provider.generate.assert_not_called()
        assert chunk.text_content == source
