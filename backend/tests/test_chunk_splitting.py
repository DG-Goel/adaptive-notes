"""
Tests for adaptive chunk splitting.

Verifies that truncation triggers splitting, split depth is respected,
provenance is preserved, and deduplication works correctly.
"""

import pytest
from app.models.source import SourceUnit
from app.models.knowledge import ExtractionChunk, Concept, Fact
from app.extraction.chunk_splitter import ChunkSplitter, merge_extracted_items


class TestChunkSplitter:
    """Test ChunkSplitter functionality"""
    
    def test_can_split_with_enough_units(self):
        """Chunk with enough units can be split"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id="S001",
                document_id="test_doc",
                type="text_block",
                position=0,
                page=1,
                text="Unit 1"
            ),
            SourceUnit(
                source_id="S002",
                document_id="test_doc",
                type="text_block",
                position=1,
                page=1,
                text="Unit 2"
            ),
            SourceUnit(
                source_id="S003",
                document_id="test_doc",
                type="text_block",
                position=2,
                page=1,
                text="Unit 3"
            ),
            SourceUnit(
                source_id="S004",
                document_id="test_doc",
                type="text_block",
                position=3,
                page=1,
                text="Unit 4"
            ),
        ]
        
        assert splitter.can_split(chunk, units) is True
    
    def test_cannot_split_at_max_depth(self):
        """Chunk at max split depth cannot be split further"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001_SUB0",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test content",
            split_depth=2  # At max depth
        )
        
        units = [
            SourceUnit(
                source_id="S001",
                document_id="test_doc",
                type="text_block",
                position=0,
                page=1,
                text="Unit 1"
            ),
            SourceUnit(
                source_id="S002",
                document_id="test_doc",
                type="text_block",
                position=1,
                page=1,
                text="Unit 2"
            ),
            SourceUnit(
                source_id="S003",
                document_id="test_doc",
                type="text_block",
                position=2,
                page=1,
                text="Unit 3"
            ),
            SourceUnit(
                source_id="S004",
                document_id="test_doc",
                type="text_block",
                position=3,
                page=1,
                text="Unit 4"
            ),
        ]
        
        assert splitter.can_split(chunk, units) is False
    
    def test_cannot_split_too_few_units(self):
        """Chunk with too few units cannot be split"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=2)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002"],  # Only 2 units, need 4 (2*min)
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id="S001",
                document_id="test_doc",
                type="text_block",
                position=0,
                page=1,
                text="Unit 1"
            ),
            SourceUnit(
                source_id="S002",
                document_id="test_doc",
                type="text_block",
                position=1,
                page=1,
                text="Unit 2"
            ),
        ]
        
        assert splitter.can_split(chunk, units) is False
    
    def test_split_creates_sub_chunks(self):
        """Splitting creates sub-chunks with correct metadata"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004"],
            section="Test Section",
            page_range=(1, 2),
            text_content="test content",
            token_count=100,
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id="S001",
                document_id="test_doc",
                type="text_block",
                position=0,
                page=1,
                text="Unit 1",
                section="Test Section"
            ),
            SourceUnit(
                source_id="S002",
                document_id="test_doc",
                type="text_block",
                position=1,
                page=1,
                text="Unit 2",
                section="Test Section"
            ),
            SourceUnit(
                source_id="S003",
                document_id="test_doc",
                type="text_block",
                position=2,
                page=2,
                text="Unit 3",
                section="Test Section"
            ),
            SourceUnit(
                source_id="S004",
                document_id="test_doc",
                type="text_block",
                position=3,
                page=2,
                text="Unit 4",
                section="Test Section"
            ),
        ]
        
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        
        assert len(sub_chunks) == 2
        
        # Check first sub-chunk
        assert sub_chunks[0].chunk_id == "TEST_001_SUB0"
        assert sub_chunks[0].split_depth == 1
        assert sub_chunks[0].parent_chunk_id == "TEST_001"
        assert len(sub_chunks[0].source_units) == 2
        assert "S001" in sub_chunks[0].source_units
        assert "S002" in sub_chunks[0].source_units
        
        # Check second sub-chunk
        assert sub_chunks[1].chunk_id == "TEST_001_SUB1"
        assert sub_chunks[1].split_depth == 1
        assert sub_chunks[1].parent_chunk_id == "TEST_001"
        assert len(sub_chunks[1].source_units) == 2
        assert "S003" in sub_chunks[1].source_units
        assert "S004" in sub_chunks[1].source_units
    
    def test_split_preserves_provenance(self):
        """Source unit IDs are preserved across splitting"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        original_unit_ids = ["S001", "S002", "S003", "S004", "S005", "S006"]
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=original_unit_ids,
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id=sid,
                document_id="test_doc",
                type="text_block",
                position=i,
                page=1,
                text=f"Unit {sid}"
            )
            for i, sid in enumerate(original_unit_ids)
        ]
        
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        
        # All original units should be in sub-chunks
        all_sub_unit_ids = []
        for sub_chunk in sub_chunks:
            all_sub_unit_ids.extend(sub_chunk.source_units)
        
        assert set(all_sub_unit_ids) == set(original_unit_ids)
    
    def test_split_increments_depth(self):
        """Split depth increments correctly"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        # First level split
        chunk_l0 = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id=f"S{i:03d}",
                document_id="test_doc",
                type="text_block",
                position=i-1,
                page=1,
                text=f"Unit {i}"
            )
            for i in range(1, 5)
        ]
        
        sub_chunks_l1 = splitter.split_chunk(chunk_l0, units, num_splits=2)
        
        assert all(sc.split_depth == 1 for sc in sub_chunks_l1)
        
        # Second level split
        if sub_chunks_l1:
            first_l1 = sub_chunks_l1[0]
            # Add more units to make it splittable
            first_l1.source_units = ["S001", "S002", "S003", "S004"]
            
            units_l2 = [
                SourceUnit(
                    source_id=f"S{i:03d}",
                    document_id="test_doc",
                    type="text_block",
                    position=i-1,
                    page=1,
                    text=f"Unit {i}"
                )
                for i in range(1, 5)
            ]
            
            sub_chunks_l2 = splitter.split_chunk(first_l1, units_l2, num_splits=2)
            
            if sub_chunks_l2:  # May be empty if can't split
                assert all(sc.split_depth == 2 for sc in sub_chunks_l2)


class TestMergeExtractedItems:
    """Test merge_extracted_items deduplication"""
    
    def test_merge_empty_lists(self):
        """Merging empty lists returns empty list"""
        result = merge_extracted_items([])
        assert result == []
    
    def test_merge_single_list(self):
        """Merging single list returns that list"""
        items = [
            Concept(
                knowledge_id="C001",
                document_id="test",
                concept_name="Test Concept",
                content="Test content",
                source_unit_ids=["S001"]
            )
        ]
        
        result = merge_extracted_items([items])
        assert len(result) == 1
        assert result[0].knowledge_id == "C001"
    
    def test_merge_removes_duplicates(self):
        """Duplicate items are removed during merge"""
        concept1 = Concept(
            knowledge_id="C001",
            document_id="test",
            concept_name="Test Concept",
            content="This is a test concept with some content",
            source_unit_ids=["S001"]
        )
        
        concept2 = Concept(
            knowledge_id="C002",
            document_id="test",
            concept_name="Test Concept",  # Same name
            content="This is a test concept with some content",  # Same content
            source_unit_ids=["S002"]
        )
        
        result = merge_extracted_items([[concept1], [concept2]])
        
        # Should only have one concept (duplicate removed)
        assert len(result) == 1
        assert result[0].concept_name == "Test Concept"
    
    def test_merge_preserves_unique_items(self):
        """Unique items are all preserved"""
        concept1 = Concept(
            knowledge_id="C001",
            document_id="test",
            concept_name="Concept A",
            content="Content A",
            source_unit_ids=["S001"]
        )
        
        concept2 = Concept(
            knowledge_id="C002",
            document_id="test",
            concept_name="Concept B",  # Different name
            content="Content B",  # Different content
            source_unit_ids=["S002"]
        )
        
        fact = Fact(
            knowledge_id="F001",
            document_id="test",
            fact_text="This is a fact",
            content="This is a fact",
            source_unit_ids=["S003"]
        )
        
        result = merge_extracted_items([[concept1, concept2], [fact]])
        
        assert len(result) == 3
        
        # Check all types present
        types = [type(item).__name__ for item in result]
        assert "Concept" in types
        assert "Fact" in types
    
    def test_merge_handles_multiple_sub_chunks(self):
        """Merge correctly handles 3+ sub-chunk results"""
        items_1 = [
            Concept(
                knowledge_id="C001",
                document_id="test",
                concept_name="Concept 1",
                content="Content 1",
                source_unit_ids=["S001"]
            )
        ]
        
        items_2 = [
            Concept(
                knowledge_id="C002",
                document_id="test",
                concept_name="Concept 2",
                content="Content 2",
                source_unit_ids=["S002"]
            )
        ]
        
        items_3 = [
            Fact(
                knowledge_id="F001",
                document_id="test",
                fact_text="Fact 1",
                content="Fact 1",
                source_unit_ids=["S003"]
            )
        ]
        
        result = merge_extracted_items([items_1, items_2, items_3])
        
        assert len(result) == 3
        assert len([r for r in result if isinstance(r, Concept)]) == 2
        assert len([r for r in result if isinstance(r, Fact)]) == 1


class TestSplitIntegration:
    """Integration tests for splitting scenarios"""
    
    def test_split_with_odd_number_of_units(self):
        """Splitting works with odd number of units"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004", "S005"],  # 5 units
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id=f"S{i:03d}",
                document_id="test_doc",
                type="text_block",
                position=i-1,
                page=1,
                text=f"Unit {i}"
            )
            for i in range(1, 6)
        ]
        
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        
        assert len(sub_chunks) == 2
        
        # First chunk gets 2, second gets 3 (remaining)
        assert len(sub_chunks[0].source_units) == 2
        assert len(sub_chunks[1].source_units) == 3
    
    def test_recursive_splitting_respects_depth(self):
        """Splitting cannot exceed max_split_depth"""
        splitter = ChunkSplitter(max_split_depth=1, min_units_per_chunk=1)
        
        # Original chunk (depth 0)
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id=f"S{i:03d}",
                document_id="test_doc",
                type="text_block",
                position=i-1,
                page_num=1,
                text=f"Unit {i}"
            )
            for i in range(1, 5)
        ]
        
        # First split succeeds (0 -> 1)
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        assert len(sub_chunks) == 2
        assert sub_chunks[0].split_depth == 1
        
        # Second split fails (already at max depth)
        sub_sub_chunks = splitter.split_chunk(sub_chunks[0], units, num_splits=2)
        assert len(sub_sub_chunks) == 0  # Cannot split further
    
    def test_split_with_non_text_units(self):
        """Splitting handles units without text (pictures, etc.)"""
        splitter = ChunkSplitter(max_split_depth=2, min_units_per_chunk=1)
        
        chunk = ExtractionChunk(
            chunk_id="TEST_001",
            source_units=["S001", "S002", "S003", "S004"],
            text_content="test content",
            split_depth=0
        )
        
        units = [
            SourceUnit(
                source_id="S001",
                document_id="test_doc",
                type="text_block",
                position=0,
                page=1,
                text="Unit 1"
            ),
            SourceUnit(
                source_id="S002",
                document_id="test_doc",
                type="picture",
                position=1,
                page=1,
                text=None,
                content_role="picture"
            ),
            SourceUnit(
                source_id="S003",
                document_id="test_doc",
                type="text_block",
                position=2,
                page=1,
                text="Unit 3"
            ),
            SourceUnit(
                source_id="S004",
                document_id="test_doc",
                type="text_block",
                position=3,
                page=1,
                text="Unit 4"
            ),
        ]
        
        sub_chunks = splitter.split_chunk(chunk, units, num_splits=2)
        
        assert len(sub_chunks) == 2
        
        # Check that non-text units are included in source_units
        all_ids = []
        for sc in sub_chunks:
            all_ids.extend(sc.source_units)
        
        assert "S002" in all_ids  # Picture unit preserved
