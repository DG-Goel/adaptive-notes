"""
Regression tests for extraction reliability improvements.

Tests JSON parsing, retry logic, truncation handling, and completeness tracking.
All tests use mocked responses to avoid API costs.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider


class TestJSONParsing:
    """Test JSON parsing with various response formats"""
    
    def test_valid_json_response(self):
        """Valid JSON response is parsed successfully"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = json.dumps({
            "concepts": [
                {
                    "concept_name": "Test Concept",
                    "content": "Test content",
                    "aliases": [],
                    "source_unit_ids": ["S0001"]
                }
            ],
            "definitions": [],
            "explanations": [],
            "examples": [],
            "facts": [],
            "formulas": [],
            "procedures": [],
            "relationships": []
        })
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test text",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        result = extractor.extract(doc)
        
        assert result.total_items == 1
        assert len(result.concepts) == 1
        assert result.concepts[0].concept_name == "Test Concept"
    
    def test_markdown_fenced_json(self):
        """Markdown-fenced JSON is extracted and parsed"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = """```json
{
  "concepts": [{"concept_name": "Test", "content": "Test", "aliases": [], "source_unit_ids": ["S0001"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```"""
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        result = extractor.extract(doc)
        
        assert result.total_items == 1
    
    def test_malformed_json_fails_with_diagnostic(self):
        """Malformed JSON raises error and saves diagnostic"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = '{"concepts": [invalid json'
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        result = extractor.extract(doc)
        
        # Should have failed chunk
        assert len(extractor.failed_chunks) == 1
        assert result.total_items == 0
        
        # Check extraction metadata
        assert result.extraction_metadata["completeness"] < 1.0
        assert len(result.extraction_metadata["failed_chunks"]) == 1


class TestTruncationHandling:
    """Test handling of truncated responses"""
    
    @patch('groq.Groq')
    def test_truncated_response_detected(self, mock_groq_class):
        """Truncated response (finish_reason=length) raises error"""
        # Mock the Groq client
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        # Mock response with truncation
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "length"
        mock_response.choices[0].message.content = '{"concepts": []}'
        mock_response.usage = None
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="truncated due to max_tokens"):
            provider.generate("test prompt")
    
    @patch('groq.Groq')
    def test_unexpected_finish_reason_detected(self, mock_groq_class):
        """Unexpected finish_reason raises error"""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "content_filter"
        mock_response.choices[0].message.content = "filtered"
        mock_response.usage = None
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="Unexpected finish_reason"):
            provider.generate("test prompt")


class TestRetryLogic:
    """Test retry logic for transient failures"""
    
    def test_retry_success_after_failure(self):
        """Extraction succeeds on retry after initial failure"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        # First call fails, second succeeds
        provider.generate.side_effect = [
            ValueError("Parse error"),
            json.dumps({
                "concepts": [{"concept_name": "Test", "content": "Test", "aliases": [], "source_unit_ids": ["S0001"]}],
                "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
            })
        ]
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=2)
        result = extractor.extract(doc)
        
        # Should succeed on second attempt
        assert result.total_items == 1
        assert len(extractor.failed_chunks) == 0
        
        # Check attempt tracking
        assert len(extractor.chunk_attempts) == 2
        assert extractor.chunk_attempts[0]["success"] == False
        assert extractor.chunk_attempts[1]["success"] == True
    
    def test_retry_exhaustion(self):
        """Extraction fails after exhausting retries"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.side_effect = ValueError("Parse error")
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=2)
        result = extractor.extract(doc)
        
        # Should fail after all retries
        assert result.total_items == 0
        assert len(extractor.failed_chunks) == 1
        
        # Check attempt tracking (1 initial + 2 retries = 3 total)
        assert len(extractor.chunk_attempts) == 3
        assert all(not attempt["success"] for attempt in extractor.chunk_attempts)


class TestCompletenessTracking:
    """Test extraction completeness tracking"""
    
    def test_partial_extraction_marked_incomplete(self):
        """Partial extraction is marked as incomplete"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        # First chunk succeeds, second fails (with retries exhausted)
        provider.generate.side_effect = [
            json.dumps({
                "concepts": [{"concept_name": "Test1", "content": "Test1", "aliases": [], "source_unit_ids": ["S0001"]}],
                "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
            }),
            ValueError("Parse error"),  # attempt 1
        ]
        
        # Create document with TWO explicitly chunked source units (different sections)
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=2,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test1 " * 500,  # First chunk
                    position=1,
                    page=1,
                    section="Section 1"
                ),
                SourceUnit(
                    source_id="S0002",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test2 " * 500,  # Force new chunk with different section
                    position=2,
                    page=2,
                    section="Section 2"  # Different section triggers new chunk
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        result = extractor.extract(doc)
        
        # Should have 2 chunks due to different sections
        metadata = result.extraction_metadata
        assert metadata["total_chunks"] == 2, f"Expected 2 chunks, got {metadata['total_chunks']}"
        
        # Should have partial extraction (1 success, 1 failure)
        assert result.total_items == 1
        assert len(extractor.failed_chunks) == 1
        
        # Check metadata
        assert metadata["successful_chunks"] == 1
        assert metadata["completeness"] == 0.5
    
    def test_complete_extraction_marked_complete(self):
        """Complete extraction has 100% completeness"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = json.dumps({
            "concepts": [{"concept_name": "Test", "content": "Test", "aliases": [], "source_unit_ids": ["S0001"]}],
            "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
        })
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        result = extractor.extract(doc)
        
        # Should be complete
        assert len(extractor.failed_chunks) == 0
        assert result.extraction_metadata["completeness"] == 1.0
        assert result.extraction_metadata["successful_chunks"] == result.extraction_metadata["total_chunks"]


class TestProvenancePreservation:
    """Test that provenance is preserved through extraction"""
    
    def test_valid_source_ids_preserved(self):
        """Valid source IDs are preserved"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = json.dumps({
            "concepts": [{"concept_name": "Test", "content": "Test", "aliases": [], "source_unit_ids": ["S0001"]}],
            "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
        })
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        result = extractor.extract(doc)
        
        assert result.concepts[0].source_unit_ids == ["S0001"]
        assert extractor.invalid_refs_count == 0
    
    def test_invalid_source_ids_filtered(self):
        """Invalid source IDs are filtered out"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = json.dumps({
            "concepts": [{"concept_name": "Test", "content": "Test", "aliases": [], "source_unit_ids": ["S0001", "S9999"]}],
            "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
        })
        
        doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Test",
                    position=1,
                    page=1
                )
            ]
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        result = extractor.extract(doc)
        
        # Should filter out invalid ID
        assert result.concepts[0].source_unit_ids == ["S0001"]
        assert extractor.invalid_refs_count == 1


class TestGroqProviderResponseFormat:
    """Test Groq provider with JSON response format"""
    
    @patch('groq.Groq')
    def test_response_format_parameter_used(self, mock_groq_class):
        """Verify response_format parameter is passed to API"""
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = '{"test": "response"}'
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model = "test-model"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = GroqProvider(api_key="test-key")
        result = provider.generate("test prompt")
        
        # Verify response_format was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "response_format" in call_kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}
        
        assert result == '{"test": "response"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestExplicitProviderRetryContract:
    """Actual root/child loops must honor metadata, including partial child results."""

    @staticmethod
    def source():
        from app.models.source import SourceDocument, SourceUnit
        return SourceDocument(
            document_id="TEST", filename="test.txt", page_count=1,
            source_units=[
                SourceUnit(source_id=f"S00{index}", document_id="TEST",
                           type="paragraph", content_role="content",
                           text="A useful source passage.", position=index)
                for index in (1, 2)
            ],
        )

    @staticmethod
    def permanent():
        from app.extraction.llm_provider import GroqProviderError
        # Even misleading truncation wording must not trigger splitting.
        return GroqProviderError(
            "model_decommissioned; max_tokens limit; truncated",
            category="permanent_model", retryable=False, status_code=400,
            error_code="model_decommissioned",
        )

    @staticmethod
    def transient():
        from app.extraction.llm_provider import GroqProviderError
        return GroqProviderError(
            "authentication marker in a transient diagnostic",
            category="transient_server", retryable=True, status_code=503,
        )

    @staticmethod
    def item():
        from app.models.knowledge import Fact
        return Fact(knowledge_id="FCT_0001", document_id="TEST",
                    source_unit_ids=["S001"], content="A useful fact.",
                    fact_text="A useful fact.")

    @staticmethod
    def extractor():
        from app.extraction.extractor import KnowledgeExtractor
        from app.extraction.llm_provider import MockLLMProvider
        return KnowledgeExtractor(MockLLMProvider(), max_retries=2, verbose=False)

    def test_permanent_root_attempted_once_without_splitting(self):
        extractor = self.extractor()
        with patch.object(extractor, "_extract_from_chunk", side_effect=self.permanent()) as attempt, \
                patch.object(extractor, "_try_split_and_extract") as split:
            result = extractor.extract(self.source())
        assert attempt.call_count == 1
        split.assert_not_called()
        assert result.total_items == 0
        assert len(extractor.chunk_attempts) == 1
        assert extractor.chunk_attempts[0]["success"] is False
        assert len(extractor.failed_chunks) == 1

    def test_permanent_child_attempted_once_and_successful_sibling_retained(self):
        extractor, source = self.extractor(), self.source()
        root = extractor.chunker.chunk(source.source_units, source.document_id)[0]
        retained = self.item()
        with patch.object(extractor, "_extract_from_chunk",
                          side_effect=[[retained], self.permanent()]) as attempt, \
                patch.object(extractor.splitter, "split_chunk", wraps=extractor.splitter.split_chunk) as split:
            result = extractor._try_split_and_extract(root, source)
        assert result == [retained]
        assert attempt.call_count == 2  # One call for each child, no retry of child 2.
        assert split.call_count == 1  # No recursive split of a permanent failure.
        assert len(extractor.chunk_attempts) == 2
        assert len(extractor.failed_chunks) == 1
        assert extractor.chunk_attempts[1]["success"] is False

    def test_explicit_transient_root_keeps_existing_retry_policy(self):
        extractor = self.extractor()
        with patch.object(extractor, "_extract_from_chunk",
                          side_effect=[self.transient(), [self.item()]]) as attempt:
            result = extractor.extract(self.source())
        assert attempt.call_count == 2
        assert result.total_items == 1
        assert [entry["success"] for entry in extractor.chunk_attempts] == [False, True]

    def test_explicit_transient_child_keeps_existing_retry_policy(self):
        extractor, source = self.extractor(), self.source()
        root = extractor.chunker.chunk(source.source_units, source.document_id)[0]
        retained = self.item()
        with patch.object(extractor, "_extract_from_chunk",
                          side_effect=[self.transient(), [retained], [retained]]) as attempt:
            result = extractor._try_split_and_extract(root, source)
        assert attempt.call_count == 3
        assert result
        assert not extractor.failed_chunks
        assert [entry["success"] for entry in extractor.chunk_attempts] == [False, True, True]

    def test_legacy_authentication_exception_still_stops_root_retries(self):
        extractor = self.extractor()
        with patch.object(extractor, "_extract_from_chunk",
                          side_effect=RuntimeError("401 authentication failure")) as attempt:
            extractor.extract(self.source())
        assert attempt.call_count == 1

    @pytest.mark.parametrize("status,code", [(400, "model_decommissioned"), (401, "invalid_api_key")])
    def test_mocked_groq_permanent_error_is_not_retried_by_outer_extractor(self, status, code):
        import httpx
        from groq import APIStatusError
        from app.extraction.llm_provider import GroqProvider
        response = httpx.Response(
            status, request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
        )
        error = APIStatusError(
            "Unavailable model", response=response,
            body={"error": {"code": code, "message": "Unavailable model"}},
        )
        with patch("groq.Groq") as constructor:
            client = constructor.return_value
            client.chat.completions.create.side_effect = error
            provider = GroqProvider(api_key="unit-test-key", use_multi_key=False)
            extractor = self.extractor()
            extractor.llm = provider
            result = extractor.extract(self.source())
        client.chat.completions.create.assert_called_once()
        assert len(extractor.chunk_attempts) == 1
        assert result.total_items == 0


    def test_permanent_later_root_preserves_earlier_root_results(self):
        extractor, source = self.extractor(), self.source()
        source.source_units[0].section = "First"
        source.source_units[1].section = "Second"
        with patch.object(extractor, "_extract_from_chunk",
                          side_effect=[[self.item()], self.permanent()]) as attempt:
            result = extractor.extract(source)
        assert attempt.call_count == 2
        assert result.total_items == 1
        assert result.facts[0].fact_text == "A useful fact."
        assert len(extractor.failed_chunks) == 1


class TestRootOutcomeAccounting:
    @staticmethod
    def run_case(*, split=False, recursive=False, partial=False, retry=False):
        from app.extraction.extractor import KnowledgeExtractor
        from app.extraction.llm_provider import MockLLMProvider
        from app.models.source import SourceUnit
        helper = TestExplicitProviderRetryContract
        source = helper.source()
        source.source_units = [
            SourceUnit(source_id=f"S00{i}", document_id="TEST", position=i,
                       type="paragraph", content_role="content", text=f"Useful fact {i}.")
            for i in range(1, 5)
        ]
        extractor = KnowledgeExtractor(MockLLMProvider(), verbose=False, max_retries=int(retry))
        root_calls = []
        def extract(chunk, document_id):
            if chunk.split_depth == 0:
                root_calls.append(chunk.chunk_id)
                if split or (retry and len(root_calls) == 1):
                    raise ValueError("truncated")
            if recursive and chunk.split_depth == 1:
                raise ValueError("truncated")
            if partial and "S004" in chunk.source_units:
                raise helper.permanent()
            sid = chunk.source_units[0]
            return [helper.item().model_copy(update={
                "knowledge_id": "FCT_" + sid[1:].zfill(4),
                "source_unit_ids": [sid], "content": sid, "fact_text": sid,
            })]
        with patch.object(extractor, "_extract_from_chunk", side_effect=extract):
            result = extractor.extract(source)
        return extractor, result

    @pytest.mark.parametrize("options,outcome", [
        ({}, "SUCCESS"), ({"retry": True}, "SUCCESS"),
        ({"split": True}, "RECOVERED"),
        ({"split": True, "recursive": True}, "RECOVERED"),
        ({"split": True, "partial": True}, "FAILED"),
        ({"split": True, "recursive": True, "partial": True}, "FAILED"),
    ])
    def test_authoritative_root_outcomes(self, options, outcome):
        extractor, result = self.run_case(**options)
        metadata = result.extraction_metadata
        assert metadata["scheduled_roots"] == 1
        assert len(metadata["root_outcomes"]) == 1
        assert metadata["root_outcomes"][0]["outcome"] == outcome
        assert sum(metadata[key] for key in (
            "successful_roots", "recovered_roots", "failed_roots", "skipped_roots")) == 1
        assert metadata["retry_attempts"] == (1 if options.get("retry") else 0)
        for metric in ("resolution_ratio", "extraction_completion_ratio"):
            assert 0 <= metadata[metric] <= 1
            assert metadata[metric] == (0 if outcome == "FAILED" else 1)
        if outcome == "FAILED":
            assert result.total_items > 0
            assert metadata["partial_results"]
            assert metadata["failed_roots"] == len(metadata["failed_root_ids"]) == 1
        if outcome == "RECOVERED":
            assert metadata["failed_chunks"] == []
            assert metadata["child_outcomes"]
            assert metadata["recovered_roots"] == 1
        if options.get("recursive"):
            assert len(metadata["child_outcomes"]) == 6

    def test_empty_response_is_failed_not_skipped(self):
        helper = TestExplicitProviderRetryContract
        extractor = helper.extractor()
        with patch.object(extractor, "_extract_from_chunk", return_value=[]):
            result = extractor.extract(helper.source())
        metadata = result.extraction_metadata
        assert metadata["failed_roots"] == 1
        assert metadata["skipped_roots"] == 0
        assert metadata["extraction_completion_ratio"] == 0
        assert not metadata["extraction_successful"]

    @pytest.mark.parametrize("empty_document", [False, True])
    def test_skips_and_zero_denominators(self, empty_document):
        helper = TestExplicitProviderRetryContract
        source, extractor = helper.source(), helper.extractor()
        if empty_document:
            source.source_units = []
        else:
            for unit in source.source_units:
                unit.text = "   "
        with patch.object(extractor, "_extract_from_chunk") as attempt:
            result = extractor.extract(source)
        attempt.assert_not_called()
        metadata = result.extraction_metadata
        assert metadata["extraction_completion_ratio"] is None
        assert not metadata["extraction_successful"]
        assert metadata["resolution_ratio"] == (None if empty_document else 1)
        assert metadata["skipped_roots"] == (0 if empty_document else 1)

    def test_reuse_does_not_mix_or_mutate_prior_diagnostics(self):
        helper = TestExplicitProviderRetryContract
        extractor, source = helper.extractor(), helper.source()
        with patch.object(extractor, "_extract_from_chunk", side_effect=helper.permanent()):
            first = extractor.extract(source)
        snapshot = first.model_dump()
        with patch.object(extractor, "_extract_from_chunk", return_value=[helper.item()]):
            second = extractor.extract(source)
        assert first.model_dump() == snapshot
        assert second.extraction_metadata["failed_roots"] == 0
        assert second.extraction_metadata["total_attempts"] == 1
        assert second.extraction_metadata["child_outcomes"] == []
        assert second.extraction_metadata["successful_roots"] == 1

    def test_mixed_success_and_skipped_root(self):
        helper = TestExplicitProviderRetryContract
        source, extractor = helper.source(), helper.extractor()
        source.source_units[0].section = "First"
        source.source_units[1].section = "Empty"
        source.source_units[1].text = "   "
        with patch.object(extractor, "_extract_from_chunk", return_value=[helper.item()]) as attempt:
            result = extractor.extract(source)
        metadata = result.extraction_metadata
        attempt.assert_called_once()
        assert metadata["scheduled_roots"] == 2
        assert metadata["successful_roots"] == metadata["skipped_roots"] == 1
        assert metadata["failed_roots"] == metadata["recovered_roots"] == 0
        assert metadata["resolution_ratio"] == metadata["extraction_completion_ratio"] == 1
        assert metadata["source_coverage"]["cited_units"] == ["S001"]
        assert metadata["source_coverage"]["uncited_units"] == ["S002"]

    def test_permanent_failure_has_one_failed_root(self):
        helper = TestExplicitProviderRetryContract
        extractor = helper.extractor()
        with patch.object(extractor, "_extract_from_chunk", side_effect=helper.permanent()) as attempt:
            result = extractor.extract(helper.source())
        metadata = result.extraction_metadata
        attempt.assert_called_once()
        assert metadata["scheduled_roots"] == metadata["failed_roots"] == 1
        assert metadata["total_attempts"] == 1
        assert metadata["retry_attempts"] == 0
        assert metadata["resolution_ratio"] == metadata["extraction_completion_ratio"] == 0

    def test_nontext_visual_is_not_silently_skipped(self):
        helper = TestExplicitProviderRetryContract
        source, extractor = helper.source(), helper.extractor()
        source.source_units = [source.source_units[0]]
        source.source_units[0].type = "picture"
        source.source_units[0].text = None
        with patch.object(extractor, "_extract_from_chunk", return_value=[]):
            result = extractor.extract(source)
        assert result.extraction_metadata["failed_roots"] == 1
        assert result.extraction_metadata["skipped_roots"] == 0
