"""
Transcript ingestion adapter for converting lecture transcripts into Source Unit Model.

Handles plain text transcripts by:
1. Detecting topic boundaries (paragraph breaks, topic shifts)
2. Assigning stable segment IDs based on position
3. Preserving timestamps if present (e.g., [00:12:34] format)
4. Creating SourceUnits compatible with existing extraction pipeline

Does not use arbitrary character slicing - respects natural text boundaries.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.source import SourceDocument, SourceUnit


class TimestampSegment:
    """Represents a segment with optional timestamp."""
    
    def __init__(
        self,
        text: str,
        start_timestamp: Optional[str] = None,
        segment_index: int = 0,
        char_offset: int = 0
    ):
        self.text = text.strip()
        self.start_timestamp = start_timestamp
        self.segment_index = segment_index
        self.char_offset = char_offset


class TranscriptParser:
    """
    Parses plain text transcripts into SourceUnits.
    
    Segments transcripts at natural boundaries (paragraphs, timestamps)
    rather than arbitrary character positions.
    """
    
    # Timestamp patterns (e.g., [00:12:34], (01:23:45), 00:12:34)
    TIMESTAMP_PATTERNS = [
        re.compile(r'\[(\d{1,2}:\d{2}:\d{2})\]'),  # [HH:MM:SS]
        re.compile(r'\((\d{1,2}:\d{2}:\d{2})\)'),  # (HH:MM:SS)
        re.compile(r'^(\d{1,2}:\d{2}:\d{2})\s'),   # HH:MM:SS at start of line
    ]
    
    # Topic markers (e.g., "Chapter 1:", "Section 2:", "Topic:")
    TOPIC_MARKERS = [
        re.compile(r'^(Chapter\s+\d+[:\.])', re.IGNORECASE),
        re.compile(r'^(Section\s+\d+[:\.])', re.IGNORECASE),
        re.compile(r'^(Part\s+\d+[:\.])', re.IGNORECASE),
        re.compile(r'^(Topic[:\.])', re.IGNORECASE),
    ]
    
    def __init__(
        self,
        min_segment_words: int = 50,
        max_segment_words: int = 500,
        detect_timestamps: bool = True
    ):
        """
        Initialize transcript parser.
        
        Args:
            min_segment_words: Minimum words per segment (for merging small segments)
            max_segment_words: Maximum words per segment (for splitting large paragraphs)
            detect_timestamps: Whether to detect and preserve timestamps
        """
        self.min_segment_words = min_segment_words
        self.max_segment_words = max_segment_words
        self.detect_timestamps = detect_timestamps
    
    def parse(self, filepath: Path) -> SourceDocument:
        """
        Parse transcript file into SourceDocument.
        
        Args:
            filepath: Path to transcript text file
            
        Returns:
            SourceDocument with SourceUnits representing transcript segments
        """
        
        # Read transcript
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate document ID
        document_id = self._generate_document_id(filepath)
        
        # Segment transcript
        segments = self._segment_transcript(content)
        
        # Create source units
        source_units = []
        for i, segment in enumerate(segments):
            unit = self._create_source_unit(
                segment=segment,
                document_id=document_id,
                position=i + 1
            )
            source_units.append(unit)
        
        # Create source document
        doc = SourceDocument(
            document_id=document_id,
            filename=filepath.name,
            page_count=1,  # Transcripts don't have pages
            source_units=source_units
        )
        
        return doc
    
    def _generate_document_id(self, filepath: Path) -> str:
        """Generate stable document ID from filename."""
        # Use filename without extension, sanitized
        base = filepath.stem
        # Remove special characters, keep alphanumeric and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', base)
        return sanitized.upper()
    
    def _segment_transcript(self, content: str) -> List[TimestampSegment]:
        """
        Segment transcript at natural boundaries.
        
        Boundaries:
        1. Timestamps (if present)
        2. Double line breaks (paragraph boundaries) - if present
        3. Topic markers (Chapter, Section, etc.)
        4. Sentence boundaries (for continuous text)
        5. Size limits (merge too-small, split too-large)
        
        Args:
            content: Raw transcript text
            
        Returns:
            List of TimestampSegment objects
        """
        
        # Check if we have paragraph breaks
        paragraphs = re.split(r'\n\s*\n', content)
        has_paragraphs = len(paragraphs) > 1
        
        timestamped = self.detect_timestamps and any(
            pattern.search(line.strip()) for line in content.splitlines()
            for pattern in self.TIMESTAMP_PATTERNS)
        if timestamped:
            # Timestamped lines must not take the continuous-text path, which
            # discards segment timing. Continuation lines remain with their segment.
            paragraphs = re.split(r'\n(?=\s*(?:\[|\()?\d{1,2}:\d{2}:\d{2})', content)
        if not has_paragraphs and not timestamped:
            # No paragraph breaks - treat as continuous text
            # Split by sentences and group into segments
            return self._segment_continuous_text(content)
        
        # Has paragraph breaks - use original logic
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        segments = []
        char_offset = 0
        
        for para_idx, para in enumerate(paragraphs):
            # Check for timestamp at start
            timestamp = None
            para_text = para
            
            if self.detect_timestamps:
                for pattern in self.TIMESTAMP_PATTERNS:
                    match = pattern.search(para)
                    if match:
                        timestamp = match.group(1)
                        # Remove timestamp from text
                        para_text = pattern.sub('', para).strip()
                        break
            
            # Check for topic markers
            is_topic_header = any(
                pattern.match(para_text) for pattern in self.TOPIC_MARKERS
            )
            
            # Split long paragraphs by sentences if too large
            if self._count_words(para_text) > self.max_segment_words:
                sub_segments = self._split_long_paragraph(para_text)
                for sub_idx, sub_text in enumerate(sub_segments):
                    seg = TimestampSegment(
                        text=sub_text,
                        start_timestamp=timestamp if sub_idx == 0 else None,
                        segment_index=len(segments),
                        char_offset=char_offset
                    )
                    segments.append(seg)
                    char_offset += len(sub_text)
            else:
                seg = TimestampSegment(
                    text=para_text,
                    start_timestamp=timestamp,
                    segment_index=len(segments),
                    char_offset=char_offset
                )
                segments.append(seg)
                char_offset += len(para_text)
        
        # Second pass: merge segments that are too small
        segments = self._merge_small_segments(segments)
        
        # Reindex after merging
        for i, seg in enumerate(segments):
            seg.segment_index = i
        
        return segments
    
    def _segment_continuous_text(self, content: str) -> List[TimestampSegment]:
        """
        Segment continuous text (no paragraph breaks) into meaningful chunks.
        
        Uses sentence boundaries if available, otherwise splits by word count
        at natural pauses (spaces).
        
        Args:
            content: Continuous text
            
        Returns:
            List of segments
        """
        
        # Try splitting by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # If we get reasonable number of sentences, use them
        word_count = self._count_words(content)
        avg_words_per_sentence = word_count / len(sentences) if sentences else word_count
        
        # If average sentence length is reasonable (< 200 words), use sentence-based splitting
        if len(sentences) > 10 and avg_words_per_sentence < 200:
            return self._segment_by_sentences(sentences)
        
        # Otherwise, this is poorly punctuated text - split by word count
        return self._segment_by_word_count(content)
    
    def _segment_by_sentences(self, sentences: List[str]) -> List[TimestampSegment]:
        """Group sentences into segments of appropriate size."""
        
        segments = []
        current_segment = []
        current_word_count = 0
        char_offset = 0
        
        for sentence in sentences:
            sentence_words = self._count_words(sentence)
            
            # If adding this sentence would exceed max, flush current segment
            if current_word_count + sentence_words > self.max_segment_words and current_segment:
                segment_text = ' '.join(current_segment)
                seg = TimestampSegment(
                    text=segment_text,
                    start_timestamp=None,
                    segment_index=len(segments),
                    char_offset=char_offset
                )
                segments.append(seg)
                char_offset += len(segment_text)
                
                # Start new segment
                current_segment = [sentence]
                current_word_count = sentence_words
            else:
                current_segment.append(sentence)
                current_word_count += sentence_words
        
        # Flush remaining sentences
        if current_segment:
            segment_text = ' '.join(current_segment)
            seg = TimestampSegment(
                text=segment_text,
                start_timestamp=None,
                segment_index=len(segments),
                char_offset=char_offset
            )
            segments.append(seg)
        
        return segments
    
    def _segment_by_word_count(self, content: str) -> List[TimestampSegment]:
        """
        Split poorly-punctuated text by word count at natural pauses.
        
        Args:
            content: Continuous text without proper sentence boundaries
            
        Returns:
            List of segments
        """
        
        words = content.split()
        segments = []
        char_offset = 0
        
        i = 0
        while i < len(words):
            # Take max_segment_words words (or remaining if less)
            segment_words = words[i:i + self.max_segment_words]
            segment_text = ' '.join(segment_words)
            
            seg = TimestampSegment(
                text=segment_text,
                start_timestamp=None,
                segment_index=len(segments),
                char_offset=char_offset
            )
            segments.append(seg)
            char_offset += len(segment_text)
            
            i += self.max_segment_words
        
        return segments
    
    def _split_long_paragraph(self, text: str) -> List[str]:
        """
        Split long paragraph into smaller segments at sentence boundaries.
        
        Args:
            text: Paragraph text
            
        Returns:
            List of sub-segments
        """
        
        # Split by sentence endings (., !, ?)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        segments = []
        current_segment = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = self._count_words(sentence)
            
            if current_word_count + sentence_words > self.max_segment_words and current_segment:
                # Flush current segment
                segments.append(' '.join(current_segment))
                current_segment = [sentence]
                current_word_count = sentence_words
            else:
                current_segment.append(sentence)
                current_word_count += sentence_words
        
        # Flush remaining
        if current_segment:
            segments.append(' '.join(current_segment))
        
        return segments
    
    def _merge_small_segments(self, segments: List[TimestampSegment]) -> List[TimestampSegment]:
        """
        Merge segments that are too small with adjacent segments.
        
        Args:
            segments: List of segments
            
        Returns:
            List of merged segments
        """
        
        if not segments:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            current = segments[i]
            current_words = self._count_words(current.text)
            
            # If current segment is too small and not the last one, try to merge with next
            if current_words < self.min_segment_words and i < len(segments) - 1:
                next_seg = segments[i + 1]
                
                # Merge current with next
                merged_text = current.text + ' ' + next_seg.text
                merged_seg = TimestampSegment(
                    text=merged_text,
                    start_timestamp=current.start_timestamp,  # Keep first timestamp
                    segment_index=current.segment_index,
                    char_offset=current.char_offset
                )
                merged.append(merged_seg)
                i += 2  # Skip next since we merged it
            else:
                merged.append(current)
                i += 1
        
        return merged
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def _create_source_unit(
        self,
        segment: TimestampSegment,
        document_id: str,
        position: int
    ) -> SourceUnit:
        """
        Create SourceUnit from TimestampSegment.
        
        Args:
            segment: Parsed segment
            document_id: Document identifier
            position: Position in document
            
        Returns:
            SourceUnit compatible with extraction pipeline
        """
        
        # Generate stable source ID
        source_id = f"T{position:04d}"  # T0001, T0002, etc.
        
        # Determine content role
        # Topic markers and headers are structural, rest is content
        text = segment.text
        content_role = "content"
        
        # Check if this looks like a structural element (very short, ends with colon, etc.)
        if len(text) < 100 and (text.endswith(':') or text.isupper()):
            content_role = "structural"
        
        # Determine type
        unit_type = "paragraph"
        if content_role == "structural":
            unit_type = "heading"
        
        # Build section name from timestamp if available
        section = None
        if segment.start_timestamp:
            section = f"Timestamp {segment.start_timestamp}"
        
        # Create source unit
        unit = SourceUnit(
            source_id=source_id,
            document_id=document_id,
            page=None,  # Transcripts don't have pages
            section=section,
            type=unit_type,
            content_role=content_role,
            text=text,
            position=position,
            parent_id=None,
            bbox=None,  # No bounding boxes for transcripts
            docling_ref=f"transcript_segment_{segment.segment_index}",
            provenance={"segment_index":segment.segment_index,
                        **({"timestamp":segment.start_timestamp} if segment.start_timestamp else {})}
        )
        
        return unit


def parse_transcript(filepath: Path, **kwargs) -> SourceDocument:
    """
    Convenience function to parse transcript file.
    
    Args:
        filepath: Path to transcript file
        **kwargs: Additional arguments for TranscriptParser
        
    Returns:
        SourceDocument
    """
    parser = TranscriptParser(**kwargs)
    return parser.parse(filepath)
