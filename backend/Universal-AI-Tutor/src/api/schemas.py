"""
API schemas for Universal AI Tutor.

Pydantic models for request/response validation.
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class IngestRequest(BaseModel):
    """Request to ingest documents."""
    
    file_paths: List[str] = Field(
        ...,
        description="Paths to documents to ingest",
        min_length=1
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite existing documents"
    )
    
    @field_validator('file_paths')
    @classmethod
    def validate_paths(cls, v):
        """Validate that file paths are not empty."""
        if not v:
            raise ValueError("At least one file path required")
        return v


class IngestResponse(BaseModel):
    """Response from ingestion."""
    
    status: Literal["success", "partial", "failed"]
    total_files: int
    successful: int
    failed: int
    total_chunks_indexed: int
    processing_time_seconds: float
    errors: List[str] = Field(default_factory=list)


class AskRequest(BaseModel):
    """Request to ask a question."""
    notes_file: Optional[str] = Field(default=None, pattern=r"^video-notes-[a-f0-9]{24}-[a-f0-9]{16}\.md$")
    
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=1,
        max_length=1000
    )
    mode: Literal["strict", "teaching"] = Field(
        default="strict",
        description="Answer mode: strict (notes only) or teaching (notes + explanations)"
    )
    top_k: int = Field(
        default=5,
        description="Number of chunks to retrieve",
        ge=1,
        le=20
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous Q&A pairs for context"
    )
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        """Validate question is not empty."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class Citation(BaseModel):
    """Source citation."""
    
    doc_title: str
    doc_path: str
    section_path: str
    chunk_id: str


class AskResponse(BaseModel):
    """Response to question."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "Based on your notes: Machine learning is...",
                "citations": [
                    {
                        "doc_title": "ML Guide",
                        "doc_path": "/docs/ml.md",
                        "section_path": "Introduction",
                        "chunk_id": "chunk_1"
                    }
                ],
                "mode": "strict",
                "metadata": {
                    "evidence_assessment": {
                        "is_sufficient": True,
                        "confidence_score": 0.92
                    }
                }
            }
        }
    }
    
    answer: str
    citations: List[Citation]
    mode: Literal["strict", "teaching"]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str
    detail: Optional[str] = None
    status_code: int
