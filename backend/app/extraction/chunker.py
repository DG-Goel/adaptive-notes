"""
Content chunking for knowledge extraction.

Groups source units into manageable chunks that fit within
LLM context windows while preserving section and page context.
"""

from typing import List, Optional, Tuple

from app.models.source import SourceUnit
from app.models.knowledge import ExtractionChunk


class ContentChunker:
    """
    Chunks source units for extraction.
    
    Strategy:
    1. Group by section headings
    2. Limit chunk size to max_tokens
    3. Preserve page ranges and context
    """
    
    def __init__(
        self,
        max_tokens_per_chunk: int = 2000,
        chars_per_token: float = 4.0  # Rough approximation
    ):
        """
        Initialize chunker.
        
        Args:
            max_tokens_per_chunk: Target maximum tokens per chunk
            chars_per_token: Character to token ratio estimate
        """
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.chars_per_token = chars_per_token
        self.max_chars_per_chunk = int(max_tokens_per_chunk * chars_per_token)
    
    def chunk(
        self,
        source_units: List[SourceUnit],
        document_id: str
    ) -> List[ExtractionChunk]:
        """
        Chunk source units into extraction chunks.
        
        Args:
            source_units: List of validated source units
            document_id: Document identifier
            
        Returns:
            List of extraction chunks
        """
        
        # Layout roles are hints; only explicitly reviewed exclusions remove units.
        content_units = [
            unit for unit in source_units
            if not unit.educational_assessment.excluded
        ]
        
        if not content_units:
            return []
        
        chunks = []
        current_chunk_units = []
        current_section = None
        current_chars = 0
        chunk_counter = 0
        
        for unit in content_units:
            
            # Check if we need to start a new chunk
            should_start_new = False
            
            # Start new chunk if section changes (and we have units)
            if unit.section != current_section and current_chunk_units:
                should_start_new = True
            
            # Start new chunk if adding this unit would exceed max size
            unit_text = unit.text or ""
            unit_chars = len(unit_text)
            
            if current_chars + unit_chars > self.max_chars_per_chunk and current_chunk_units:
                should_start_new = True
            
            # Create chunk if needed
            if should_start_new:
                chunk = self._create_chunk(
                    chunk_id=f"{document_id}_CHUNK_{chunk_counter:03d}",
                    units=current_chunk_units,
                    section=current_section
                )
                chunks.append(chunk)
                
                chunk_counter += 1
                current_chunk_units = []
                current_chars = 0
            
            # Add unit to current chunk
            current_chunk_units.append(unit)
            current_section = unit.section
            current_chars += unit_chars
        
        # Create final chunk if we have remaining units
        if current_chunk_units:
            chunk = self._create_chunk(
                chunk_id=f"{document_id}_CHUNK_{chunk_counter:03d}",
                units=current_chunk_units,
                section=current_section
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(
        self,
        chunk_id: str,
        units: List[SourceUnit],
        section: Optional[str]
    ) -> ExtractionChunk:
        """
        Create an extraction chunk from units.
        
        IMPORTANT: Non-text content handling
        - All units (text and non-text) are tracked in source_units list
        - Only units with text content are included in text_content string
        - Non-text elements are explicitly tracked as non-quotable evidence
        - The LLM CANNOT see or extract from non-text elements
        - Source IDs are preserved for validation only, NOT semantic extraction
        
        Args:
            chunk_id: Unique chunk identifier
            units: List of source units (may include pictures, formulas, etc.)
            section: Section heading (if any)
            
        Returns:
            ExtractionChunk with:
            - source_units: ALL unit IDs (text and non-text)
            - text_content: Only text from units with non-null text field
        """
        
        # Build text content with source markers
        # Non-quotable units stay in coverage/state metadata, without fake text.
        text_parts = []
        
        if section:
            text_parts.append(f"## {section}\n")
        
        for unit in units:
            if not unit.text:
                # Picture, formula, or other non-text element
                # Source ID is tracked in source_units list but NOT sent to LLM
                # No quotation or invented description; state remains explicit.
                continue
            
            # Add source marker for traceability
            text_parts.append(f"[{unit.source_id}] {unit.text}\n")
        
        text_content = "\n".join(text_parts)
        
        # Calculate page range
        pages = [u.page for u in units if u.page is not None]
        page_range = (min(pages), max(pages)) if pages else None
        
        # Estimate token count
        token_count = int(len(text_content) / self.chars_per_token)
        
        return ExtractionChunk(
            chunk_id=chunk_id,
            source_units=[u.source_id for u in units],  # ALL units (text + non-text)
            section=section,
            page_range=page_range,
            text_content=text_content,  # Only text units
            token_count=token_count,
            review_source_ids=[u.source_id for u in units if u.educational_assessment.status in {'uncertain','incomplete_educational','noisy_educational'}],
            uninterpreted_source_ids=[u.source_id for u in units if not u.text],
            source_states={u.source_id:(u.representation_status or ('text' if u.text else 'awaiting_interpretation')) for u in units},
            literal_source_texts={u.source_id:u.text for u in units if u.type=='code' and u.text}
        )
