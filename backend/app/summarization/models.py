"""
Data models for summarization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkSummary(BaseModel):
    """
    Summary of a single text chunk.
    """
    chunk_id: str
    source_unit_ids: List[str]  # IDs of source units in this chunk
    original_text: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    technical_terms: List[str] = Field(default_factory=list)
    confidence: Optional[str] = None  # "high", "medium", "low", "uncertain"
    token_count: Optional[int] = None  # Approximate tokens in original text
    processing_time_ms: Optional[int] = None
    

class SummarizationResult(BaseModel):
    """
    Result of summarizing a document.
    """
    document_id: str
    filename: str
    chunk_summaries: List[ChunkSummary]
    total_chunks: int
    successful_chunks: int
    failed_chunks: List[str] = Field(default_factory=list)
    total_processing_time_ms: int
    model_name: str
    model_loaded: bool = False
    
    @property
    def completeness(self) -> float:
        """Fraction of chunks successfully summarized."""
        return self.successful_chunks / self.total_chunks if self.total_chunks > 0 else 0.0
