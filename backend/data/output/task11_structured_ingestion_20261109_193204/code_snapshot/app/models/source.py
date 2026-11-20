from typing import List, Optional, Literal

from pydantic import BaseModel, Field
from app.ingestion.educational_policy import EducationalAssessment


class BoundingBox(BaseModel):
    left: float
    top: float
    right: float
    bottom: float


class SourceUnit(BaseModel):
    source_id: str
    document_id: str

    page: Optional[int] = None
    section: Optional[str] = None

    type: str

    # How this unit should be treated by downstream systems.
    # Examples:
    # content, structural, furniture, noise, unknown
    content_role: str = "unknown"

    text: Optional[str] = None

    position: int
    parent_id: Optional[str] = None

    bbox: Optional[BoundingBox] = None
    
    # Reference to the original Docling item (e.g., "#/texts/0", "#/pictures/3")
    docling_ref: Optional[str] = None
    educational_assessment: EducationalAssessment = Field(default_factory=EducationalAssessment)
    # Populate only from available parser evidence, never inferred coordinates.
    provenance: dict = Field(default_factory=dict)
    interpretation_limitations: List[str] = Field(default_factory=list)
    representation_status: Optional[Literal['text', 'structured', 'awaiting_interpretation',
        'failed', 'incomplete', 'empty', 'structural']] = None


class SourceDocument(BaseModel):
    document_id: str
    filename: str
    page_count: int

    source_units: List[SourceUnit] = Field(default_factory=list)
    ingestion: dict = Field(default_factory=dict)
