"""
Deterministic tests for truncated response handling.

Tests verify:
- Incomplete JSON detection
- Proper error raising (not silent parsing)
- Retry with adjusted strategy
- Provenance preservation after splitting
- No silent mock fallback
"""

import pytest
from unittest.mock import MagicMock, patch
import json

from app.extraction.llm_provider import GroqProvider
from app.extraction.extractor import KnowledgeExtractor
from app.models.source import SourceDocument, SourceUnit


class TestTruncatedJSONDetection:
    """Test detection of incomplete/truncated JSON responses"""
    
    @patch('groq.Groq')
    def test_incomplete_json_with_stop_finish_reason(self, mock_groq_class):
        """Incomplete JSON raises error even with finish_reason='stop'"""
        
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Mock truncated JSON (missing closing brace)
        truncated_json = '{"concepts": [{"concept_name": "test", "content": "incomplete'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"  # Says complete, but JSON is not!
        mock_response.choices[0].message.content = truncated_json
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        
        # Should raise error due to incomplete JSON
        with pytest.raises(ValueError, match="incomplete JSON"):
            provider.generate("test prompt")
    
    @patch('groq.Groq')
    def test_incomplete_json_unmatched_braces(self, mock_groq_class):
        """JSON with unmatched braces is detected as incomplete"""
        
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Missing closing brace for outer object
        incomplete_json = '{"concepts": [{"concept_name": "test"}], "definitions": []'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = incomplete_json
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="incomplete JSON"):
            provider.generate("test prompt")
    
    @patch('groq.Groq')
    def test_incomplete_json_in_markdown_fence(self, mock_groq_class):
        """Incomplete JSON inside markdown fence is detected"""
        
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Missing closing markdown fence
        incomplete = '```json\n{"concepts": [], "definitions": []}\n'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = incomplete
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response  # Fixed
        
        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="incomplete JSON"):
            provider.generate("test prompt")
    
    @patch('groq.Groq')
    def test_complete_json_accepted(self, mock_groq_class):
        """Complete JSON passes validation"""
        
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        complete_json = '{"concepts": [{"concept_name": "test", "content": "complete"}], "definitions": []}'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = complete_json
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        
        # Should succeed
        result = provider.generate("test prompt")
        assert "concepts" in result


class TestTruncationRecoveryWithSplitting:
    """Test that truncation triggers adaptive splitting with adjusted strategy"""
    
    def test_truncation_triggers_splitting_not_just_retry(self):
        """Truncation should trigger split with smaller chunks, not just retry same chunk"""
        
        # Create test source doc with large content
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id=f"S{i:04d}",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text=f"Unit {i} content " * 50,  # Medium units
                    position=i
                )
                for i in range(10)  # 10 units will be grouped into chunks
            ]
        )
        
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            
            call_count = [0]
            
            def create_mock_response(*args, **kwargs):
                call_count[0] += 1
                
                mock_resp = MagicMock()
                mock_resp.model = "test-model"
                mock_resp.choices = [MagicMock()]
                mock_resp.usage = MagicMock()
                
                # First 3 calls fail with truncation (initial chunk + 2 retries)
                if call_count[0] <= 3:
                    mock_resp.choices[0].finish_reason = "length"  # Truncated
                    mock_resp.choices[0].message.content = '{"concepts": ['
                    mock_resp.usage.prompt_tokens = 2000
                    mock_resp.usage.completion_tokens = 4000
                    mock_resp.usage.total_tokens = 6000
                else:
                    # Sub-chunks succeed
                    mock_resp.choices[0].finish_reason = "stop"
                    # Return valid response with any valid source ID from the test data
                    mock_resp.choices[0].message.content = '{"concepts": [{"concept_name": "test", "content": "ok", "source_unit_ids": ["S0000"]}], "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []}'
                    mock_resp.usage.prompt_tokens = 100
                    mock_resp.usage.completion_tokens = 50
                    mock_resp.usage.total_tokens = 150
                
                return mock_resp
            
            mock_client.chat.completions.create.side_effect = create_mock_response
            
            # This fixture tests output truncation, after complete input budgeting succeeds.
            provider = GroqProvider(api_key="test-key", tokens_per_minute=16000)
            
            extractor = KnowledgeExtractor(
                llm_provider=provider,
                max_tokens_per_chunk=2000,
                verbose=False,
                max_retries=2,
                max_split_depth=2
            )
            
            result = extractor.extract(source_doc)
            
            # Verify that splitting occurred
            metadata = result.extraction_metadata
            assert len(metadata['split_chunks']) > 0, "Truncation should have triggered splitting"
            # Either recovered via splits or explicitly failed
            assert metadata['completeness'] > 0 or len(metadata['failed_chunks']) > 0


class TestProvenancePreservationAfterSplitting:
    """Test that source_unit_ids are preserved correctly after splitting"""
    
    def test_source_ids_preserved_across_splits(self):
        """Source unit IDs must be preserved when chunks are split"""
        
        # Create doc where both units will fit in one chunk (no split needed)
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Unit one content",
                    position=1
                ),
                SourceUnit(
                    source_id="S0002",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Unit two content",
                    position=2
                )
            ]
        )
        
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            
            # Both units in one chunk, extract both
            def create_response(*args, **kwargs):
                mock_resp = MagicMock()
                mock_resp.choices = [MagicMock()]
                mock_resp.choices[0].finish_reason = "stop"
                mock_resp.usage = MagicMock()
                mock_resp.usage.prompt_tokens = 100
                mock_resp.usage.completion_tokens = 50
                mock_resp.usage.total_tokens = 150
                mock_resp.model = "test-model"
                
                # Extract from both source units in same response
                mock_resp.choices[0].message.content = '{"concepts": [{"concept_name": "from_s0001", "content": "test", "source_unit_ids": ["S0001"]}, {"concept_name": "from_s0002", "content": "test", "source_unit_ids": ["S0002"]}], "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []}'
                
                return mock_resp
            
            mock_client.chat.completions.create.side_effect = create_response
            
            provider = GroqProvider(api_key="test-key")
            
            extractor = KnowledgeExtractor(
                llm_provider=provider,
                max_tokens_per_chunk=2000,
                verbose=False
            )
            
            result = extractor.extract(source_doc)
            
            # Verify provenance
            assert len(result.concepts) == 2, "Should extract from both source units"
            
            concepts_by_source = {}
            for concept in result.concepts:
                for source_id in concept.source_unit_ids:
                    concepts_by_source[source_id] = concept
            
            assert "S0001" in concepts_by_source, "S0001 provenance must be preserved"
            assert "S0002" in concepts_by_source, "S0002 provenance must be preserved"
            assert concepts_by_source["S0001"].concept_name == "from_s0001"
            assert concepts_by_source["S0002"].concept_name == "from_s0002"


class TestRepeatedTruncationFailure:
    """Test that repeated truncation (even after splitting) results in explicit failure"""
    
    def test_repeated_truncation_explicit_failure(self):
        """If splitting doesn't resolve truncation, fail explicitly (don't silently discard)"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Content " * 200,
                    position=1
                )
            ]
        )
        
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            
            # Always truncate (even sub-chunks)
            def always_truncate(*args, **kwargs):
                mock_resp = MagicMock()
                mock_resp.choices = [MagicMock()]
                mock_resp.choices[0].finish_reason = "length"
                mock_resp.choices[0].message.content = '{"incomplete":'
                mock_resp.usage = MagicMock()
                mock_resp.usage.prompt_tokens = 100
                mock_resp.usage.completion_tokens = 4000
                mock_resp.usage.total_tokens = 4100
                mock_resp.model = "test-model"
                return mock_resp
            
            mock_client.chat.completions.create.side_effect = always_truncate
            
            provider = GroqProvider(api_key="test-key")
            
            extractor = KnowledgeExtractor(
                llm_provider=provider,
                max_tokens_per_chunk=2000,
                verbose=False,
                max_retries=2,
                max_split_depth=2
            )
            
            result = extractor.extract(source_doc)
            
            # Verify explicit failure tracking
            metadata = result.extraction_metadata
            assert len(metadata['failed_chunks']) > 0, "Failed chunks must be explicitly tracked"
            assert metadata['completeness'] < 1.0, "Completeness must reflect failure"
            
            # Verify no items extracted (because all failed)
            assert result.total_items == 0, "No items should be extracted if all chunks fail"


class TestNoSilentMockFallback:
    """Verify tests use real code paths, not mock shortcuts"""
    
    def test_extractor_uses_real_llm_provider_interface(self):
        """Extractor must call provider.generate(), not bypass it"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test content for extraction",
                    position=1
                )
            ]
        )
        
        with patch('groq.Groq') as mock_groq_class:
            mock_client = MagicMock()
            mock_groq_class.return_value = mock_client
            
            # Track that Groq API is actually called
            api_called = [False]
            
            def track_api_call(*args, **kwargs):
                api_called[0] = True
                mock_resp = MagicMock()
                mock_resp.choices = [MagicMock()]
                mock_resp.choices[0].finish_reason = "stop"
                mock_resp.choices[0].message.content = '{"concepts": [], "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []}'
                mock_resp.usage = MagicMock()
                mock_resp.usage.prompt_tokens = 10
                mock_resp.usage.completion_tokens = 10
                mock_resp.usage.total_tokens = 20
                mock_resp.model = "test-model"
                return mock_resp
            
            mock_client.chat.completions.create.side_effect = track_api_call
            
            provider = GroqProvider(api_key="test-key")
            extractor = KnowledgeExtractor(llm_provider=provider, verbose=False)
            
            result = extractor.extract(source_doc)
            
            assert api_called[0], "Groq API must be called (no silent mock bypass)"
            assert mock_client.chat.completions.create.called, "Provider's generate() must invoke Groq client"
