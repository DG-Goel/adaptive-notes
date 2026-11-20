"""
Adaptive chunk splitting for truncation recovery.

When extraction fails due to output truncation, split the chunk
into smaller sub-chunks and retry extraction on each piece.
"""

from typing import List, Optional
from app.models.knowledge import ExtractionChunk
from app.models.source import SourceUnit


class ChunkSplitter:
    """
    Splits extraction chunks at source unit boundaries.
    
    Strategy:
    - Split at source unit boundaries (preserve provenance)
    - Aim for roughly equal sub-chunk sizes
    - Preserve all metadata (section, pages, etc.)
    - Track split depth to prevent infinite recursion
    """
    
    def __init__(
        self,
        max_split_depth: int = 2,
        min_units_per_chunk: int = 1
    ):
        """
        Initialize splitter.
        
        Args:
            max_split_depth: Maximum splitting depth (0 = no splitting, 1 = split once, etc.)
            min_units_per_chunk: Minimum source units per sub-chunk
        """
        self.max_split_depth = max_split_depth
        self.min_units_per_chunk = min_units_per_chunk
    
    def can_split(self, chunk: ExtractionChunk, source_units: List[SourceUnit]) -> bool:
        """
        Check if a chunk can be split.
        
        Args:
            chunk: Chunk to check
            source_units: Available source units (for lookup)
            
        Returns:
            True if chunk can be split (has enough units and hasn't exceeded depth)
        """
        current_depth = chunk.split_depth if hasattr(chunk, 'split_depth') else 0
        
        if current_depth >= self.max_split_depth:
            return False
        
        if len(chunk.source_units) < 2 * self.min_units_per_chunk:
            # Not enough units to split meaningfully
            return False
        
        return True
    
    def split_chunk(
        self,
        chunk: ExtractionChunk,
        source_units: List[SourceUnit],
        num_splits: int = 2
    ) -> List[ExtractionChunk]:
        """
        Split a chunk into sub-chunks at source unit boundaries.
        
        Args:
            chunk: Chunk to split
            source_units: All source units (for metadata lookup)
            num_splits: Number of sub-chunks to create (default: 2)
            
        Returns:
            List of sub-chunks, or empty list if splitting not possible
        """
        if not self.can_split(chunk, source_units):
            return []
        
        # Build lookup for source units
        unit_map = {unit.source_id: unit for unit in source_units}
        
        # Get units for this chunk
        chunk_units = [unit_map[sid] for sid in chunk.source_units if sid in unit_map]
        
        if len(chunk_units) < 2:
            return []
        
        # Calculate split points
        units_per_split = max(self.min_units_per_chunk, len(chunk_units) // num_splits)
        
        sub_chunks = []
        current_depth = chunk.split_depth if hasattr(chunk, 'split_depth') else 0
        
        for i in range(num_splits):
            start_idx = i * units_per_split
            
            # Last split gets remaining units
            if i == num_splits - 1:
                end_idx = len(chunk_units)
            else:
                end_idx = (i + 1) * units_per_split
            
            if start_idx >= len(chunk_units):
                break
            
            sub_chunk_units = chunk_units[start_idx:end_idx]
            
            if len(sub_chunk_units) < self.min_units_per_chunk:
                # Merge with previous chunk if too small
                if sub_chunks:
                    # Get units from last sub-chunk
                    last_chunk_unit_ids = sub_chunks[-1].source_units
                    last_chunk_units = [unit_map[sid] for sid in last_chunk_unit_ids if sid in unit_map]
                    
                    # Merge
                    merged_units = last_chunk_units + sub_chunk_units
                    
                    # Recreate last chunk with merged units
                    merged_chunk = self._create_sub_chunk(
                        parent_chunk_id=chunk.chunk_id,
                        units=merged_units,
                        sub_index=len(sub_chunks) - 1,
                        split_depth=current_depth + 1
                    )
                    
                    sub_chunks[-1] = merged_chunk
                continue
            
            sub_chunk = self._create_sub_chunk(
                parent_chunk_id=chunk.chunk_id,
                units=sub_chunk_units,
                sub_index=i,
                split_depth=current_depth + 1
            )
            
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _create_sub_chunk(
        self,
        parent_chunk_id: str,
        units: List[SourceUnit],
        sub_index: int,
        split_depth: int
    ) -> ExtractionChunk:
        """
        Create a sub-chunk from source units.
        
        Args:
            parent_chunk_id: Parent chunk identifier
            units: Source units for this sub-chunk
            sub_index: Index within parent's split (0, 1, 2, ...)
            split_depth: Current split depth
            
        Returns:
            ExtractionChunk for the sub-chunk
        """
        # Generate sub-chunk ID
        chunk_id = f"{parent_chunk_id}_SUB{sub_index}"
        
        # Extract common section (most common among units)
        sections = [u.section for u in units if u.section]
        section = sections[0] if sections else None
        
        # Build text content with source markers
        text_parts = []
        
        if section:
            text_parts.append(f"## {section}\n")
        
        for unit in units:
            if not unit.text:
                continue
            text_parts.append(f"[{unit.source_id}] {unit.text}\n")
        
        text_content = "\n".join(text_parts)
        
        # Calculate page range
        pages = [u.page for u in units if u.page is not None]
        page_range = (min(pages), max(pages)) if pages else None
        
        # Estimate token count
        token_count = int(len(text_content) / 4.0)
        
        # Create chunk with split metadata
        chunk = ExtractionChunk(
            chunk_id=chunk_id,
            source_units=[u.source_id for u in units],
            section=section,
            page_range=page_range,
            text_content=text_content,
            token_count=token_count,
            uninterpreted_source_ids=[u.source_id for u in units if not u.text],
            source_states={u.source_id:(u.representation_status or ('text' if u.text else 'awaiting_interpretation')) for u in units},
            literal_source_texts={u.source_id:u.text for u in units if u.type=='code' and u.text}
        )
        
        # Add split metadata
        chunk.split_depth = split_depth
        chunk.parent_chunk_id = parent_chunk_id
        
        return chunk


def merge_extracted_items(items_list: List[List[any]]) -> List[any]:
    """
    Merge knowledge items from multiple sub-chunk extractions.
    
    Deduplicates items that appear similar (same type and overlapping content).
    Preserves all unique items.
    
    Args:
        items_list: List of item lists from each sub-chunk extraction
        
    Returns:
        Merged list of unique items
    """
    if not items_list:
        return []
    
    if len(items_list) == 1:
        return items_list[0]
    
    # Flatten all items
    all_items = []
    for items in items_list:
        all_items.extend(items)
    
    # Deduplicate based on type and content similarity
    unique_items = []
    seen_signatures = set()
    
    for item in all_items:
        # Create signature for deduplication
        # Use type, key field, and first 100 chars of content
        item_type = type(item).__name__
        content = getattr(item, 'content', '')[:100]
        
        # Add type-specific key fields
        if hasattr(item, 'concept_name'):
            key_field = item.concept_name
        elif hasattr(item, 'term'):
            key_field = item.term
        elif hasattr(item, 'topic'):
            key_field = item.topic
        elif hasattr(item, 'fact_text'):
            key_field = item.fact_text[:50]
        elif hasattr(item, 'procedure_name'):
            key_field = item.procedure_name
        elif hasattr(item, 'subject'):
            key_field = f"{item.subject}_{item.object}"
        else:
            key_field = content[:50]
        
        signature = f"{item_type}:{key_field}:{content}"
        
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_items.append(item)
    
    return unique_items
