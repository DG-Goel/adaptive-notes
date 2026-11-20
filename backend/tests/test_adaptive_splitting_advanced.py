"""
Advanced tests for adaptive splitting and edge cases.

Tests recursive splitting, quota exhaustion, zero-item chunks,
and provenance preservation across multiple split levels.
"""

import pytest
from unittest.mock import Mock, patch
from app.models.source import SourceUnit, SourceDocument
from app.models.knowledge import ExtractionChunk, Concept
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.chunk_splitter import ChunkSplitter


class TestRecursiveSplitting:
    """Test recursive splitting when sub-chunks also fail"""
    
    def test_sub_chunk_triggers_recursive_split(self):
        """When a sub-chunk fails with truncation, it should be recursively split"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        # Create a chunk that will be split twice
        parent_chunk = ExtractionChunk(
            chunk_id="PARENT",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id=f"S{i:03d}",
                document_id="test",
                type="text_block",
                position=i-1,
                page=1,
                text=f"Unit {i}"
            )
            for i in range(1, 5)
        ]
        
        # First split
        level1_chunks = splitter.split_chunk(parent_chunk, units, num_splits=2)
        assert len(level1_chunks) == 2
        assert level1_chunks[0].split_depth == 1
        assert level1_chunks[0].parent_chunk_id == "PARENT"
        
        # Second split (recursive)
        level2_chunks = splitter.split_chunk(level1_chunks[0], units, num_splits=2)
        assert len(level2_chunks) == 2
        assert level2_chunks[0].split_depth == 2
        assert level2_chunks[0].parent_chunk_id == "PARENT_SUB0"
    
    def test_max_depth_prevents_infinite_recursion(self):
        """Splitting stops at max_split_depth"""
        splitter = ChunkSplitter(max_split_depth=1, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test",
            split_depth=1  # Already at max
        )
        
        units = [
            SourceUnit(
                source_id=f"S{i:03d}",
                document_id="test",
                type="text_block",
                position=i-1,
                page=1,
                text=f"Unit {i}"
            )
            for i in range(1, 5)
        ]
        
        # Cannot split further
        assert not splitter.can_split(chunk, units)
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        assert len(sub_chunks) == 0


class TestZeroItemChunks:
    """Test handling of chunks that produce zero items"""
    
    def test_empty_content_chunk(self):
        """Chunk with only whitespace/noise produces zero items correctly"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = """```json
{
  "concepts": [],
  "definitions": [],
  "explanations": [],
  "examples": [],
  "facts": [],
  "formulas": [],
  "procedures": [],
  "relationships": []
}
```"""
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="test",
                    type="paragraph",
                    position=0,
                    page=1,
                    text="1",
                    content_role="furniture"
                ),
                SourceUnit(
                    source_id="S002",
                    document_id="test",
                    type="paragraph",
                    position=1,
                    page=1,
                    text="   ",
                    content_role="noise"
                )
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have 0 items but not be marked as failed
        assert knowledge_doc.total_items == 0
        # Extraction completed successfully (no extraction errors)
        assert knowledge_doc.extraction_metadata["completeness"] == 1.0
    
    def test_meaningful_content_zero_items_flags_warning(self):
        """Chunk with meaningful content but zero items should be investigated"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.return_value = """```json
{
  "concepts": [],
  "definitions": [],
  "explanations": [],
  "examples": [],
  "facts": [],
  "formulas": [],
  "procedures": [],
  "relationships": []
}
```"""
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="test",
                    type="paragraph",
                    position=0,
                    page=1,
                    text="This is a meaningful sentence with content.",
                    content_role="content"
                ),
                SourceUnit(
                    source_id="S002",
                    document_id="test",
                    type="paragraph",
                    position=1,
                    page=1,
                    text="Another meaningful sentence.",
                    content_role="content"
                )
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Zero items extracted successfully (LLM returned valid empty JSON)
        assert knowledge_doc.total_items == 0
        # Current behavior: chunk with zero items is marked as failed
        # (Could be debated: is empty valid JSON a "success"?)
        assert knowledge_doc.extraction_metadata["successful_chunks"] == 0
        assert knowledge_doc.extraction_metadata["completeness"] == 0.0


class TestDailyQuotaHandling:
    """Test handling of daily token quota exhaustion"""
    
    def test_daily_quota_stops_retries(self):
        """When daily quota is exhausted, stop retrying immediately"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.side_effect = RuntimeError(
            "Groq API call failed: RateLimitError: Error code: 429 - "
            "{'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` "
            "in organization `org_123` service tier `on_demand` on tokens per day (TPD): "
            "Limit 200000, Used 199500, Requested 5000. Please try again in 10m0s.'}}"
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=2)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="test",
                    type="text_block",
                    position=0,
                    page=1,
                    text="Test content",
                    content_role="content"
                )
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have exactly 1 attempt (no retries for daily quota)
        attempts = knowledge_doc.extraction_metadata["chunk_attempts"]
        chunk_attempts = [a for a in attempts if a["chunk_id"].startswith("test_CHUNK")]
        assert len(chunk_attempts) == 1
        assert not chunk_attempts[0]["success"]
        assert "TPD" in chunk_attempts[0]["error"] or "tokens per day" in chunk_attempts[0]["error"]
    
    def test_quota_failed_chunks_marked_incomplete(self):
        """Chunks that fail due to quota should be marked as failed"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        provider.generate.side_effect = RuntimeError(
            "Groq API call failed: RateLimitError: tokens per day (TPD) limit exceeded"
        )
        
        extractor = KnowledgeExtractor(provider, verbose=False)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="test",
                    type="text_block",
                    position=0,
                    page=1,
                    text="Test",
                    content_role="content"
                )
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should be marked as incomplete
        assert knowledge_doc.extraction_metadata["completeness"] < 1.0
        assert len(knowledge_doc.extraction_metadata["failed_chunks"]) == 1


class TestProvenanceAcrossSplits:
    """Test that provenance is preserved across multiple split levels"""
    
    def test_provenance_preserved_after_split(self):
        """Source unit IDs preserved in items after splitting"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        
        # First call fails (truncation), triggers split
        # Second call (sub-chunk 1) succeeds
        # Third call (sub-chunk 2) succeeds
        provider.generate.side_effect = [
            ValueError("Response truncated due to max_tokens limit (4000)"),
            """```json
{
  "concepts": [{"concept_name": "Concept A", "aliases": [], "content": "test", "source_unit_ids": ["S001"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```""",
            """```json
{
  "concepts": [{"concept_name": "Concept B", "aliases": [], "content": "test", "source_unit_ids": ["S002"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```"""
        ]
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(source_id="S001", document_id="test", type="text_block", position=0, page=1, text="A" * 1000, content_role="content"),
                SourceUnit(source_id="S002", document_id="test", type="text_block", position=1, page=1, text="B" * 1000, content_role="content")
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have 2 concepts from the split
        assert len(knowledge_doc.concepts) == 2
        
        # Check provenance
        concept_a = [c for c in knowledge_doc.concepts if c.concept_name == "Concept A"][0]
        concept_b = [c for c in knowledge_doc.concepts if c.concept_name == "Concept B"][0]
        
        assert "S001" in concept_a.source_unit_ids
        assert "S002" in concept_b.source_unit_ids


class TestDeduplicationAcrossSplits:
    """Test that deduplication works correctly across split merging"""
    
    def test_identical_items_deduplicated(self):
        """Identical items from different sub-chunks are merged"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        
        # Both sub-chunks return the same concept
        provider.generate.side_effect = [
            ValueError("Response truncated due to max_tokens limit"),
            """```json
{
  "concepts": [{"concept_name": "Same Concept", "aliases": [], "content": "identical content", "source_unit_ids": ["S001"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```""",
            """```json
{
  "concepts": [{"concept_name": "Same Concept", "aliases": [], "content": "identical content", "source_unit_ids": ["S002"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```"""
        ]
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(source_id="S001", document_id="test", type="text_block", position=0, page=1, text="A" * 1000, content_role="content"),
                SourceUnit(source_id="S002", document_id="test", type="text_block", position=1, page=1, text="B" * 1000, content_role="content")
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have only 1 concept (deduplicated)
        assert len(knowledge_doc.concepts) == 1
        assert knowledge_doc.concepts[0].concept_name == "Same Concept"
    
    def test_distinct_items_preserved(self):
        """Different items from sub-chunks are both preserved"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        
        provider.generate.side_effect = [
            ValueError("Response truncated due to max_tokens limit"),
            """```json
{
  "concepts": [{"concept_name": "Concept A", "aliases": [], "content": "content a", "source_unit_ids": ["S001"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```""",
            """```json
{
  "concepts": [{"concept_name": "Concept B", "aliases": [], "content": "content b", "source_unit_ids": ["S002"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```"""
        ]
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(source_id="S001", document_id="test", type="text_block", position=0, page=1, text="A" * 1000, content_role="content"),
                SourceUnit(source_id="S002", document_id="test", type="text_block", position=1, page=1, text="B" * 1000, content_role="content")
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have 2 distinct concepts
        assert len(knowledge_doc.concepts) == 2
        names = {c.concept_name for c in knowledge_doc.concepts}
        assert names == {"Concept A", "Concept B"}


class TestFailedChildPropagation:
    """Test that failed child chunks properly mark parent as incomplete"""
    
    def test_partial_split_success_marked_incomplete(self):
        """When some sub-chunks fail, parent is marked incomplete"""
        provider = Mock()
        provider.tokens_per_minute = 8000
        
        # Parent fails, splits into 2 sub-chunks
        # Sub-chunk 1 succeeds, sub-chunk 2 fails
        provider.generate.side_effect = [
            ValueError("Response truncated due to max_tokens limit"),
            """```json
{
  "concepts": [{"concept_name": "Success", "aliases": [], "content": "test", "source_unit_ids": ["S001"]}],
  "definitions": [], "explanations": [], "examples": [], "facts": [], "formulas": [], "procedures": [], "relationships": []
}
```""",
            ValueError("Permanent error")
        ]
        
        extractor = KnowledgeExtractor(provider, verbose=False, max_retries=0)
        
        source_doc = SourceDocument(
            document_id="test",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(source_id="S001", document_id="test", type="text_block", position=0, page=1, text="A" * 1000, content_role="content"),
                SourceUnit(source_id="S002", document_id="test", type="text_block", position=1, page=1, text="B" * 1000, content_role="content")
            ]
        )
        
        knowledge_doc = extractor.extract(source_doc)
        
        # Should have 1 concept from successful sub-chunk
        assert len(knowledge_doc.concepts) == 1
        
        # But failed sub-chunk should be in failed list
        failed_chunks = knowledge_doc.extraction_metadata["failed_chunks"]
        assert any("SUB" in chunk_id for chunk_id in failed_chunks)
