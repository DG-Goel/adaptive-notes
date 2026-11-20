"""
Data models for rendering.

Defines output structures for the Renderer v1 layer.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.representation.formats import RepresentationFormat


class RenderedItem(BaseModel):
    """
    Metadata about a rendered knowledge item.
    
    Maps rendered content back to source provenance.
    """
    
    knowledge_id: str
    source_unit_ids: List[str]
    format_used: RepresentationFormat  # Alias for format_rendered
    
    # Location in markdown
    start_line: int  # 1-indexed line number
    end_line: int    # 1-indexed line number
    
    # Rendering status
    status: Literal["complete", "partial", "fallback"]
    used_fallback: bool = False  # True if fallback was used
    fallback_reason: Optional[str] = None


class RenderWarning(BaseModel):
    """Warning generated during rendering"""
    
    item_id: str  # knowledge_id
    warning_type: Literal["missing_field", "malformed_payload", "unsupported_format", "empty_content"]
    message: str


class RenderManifest(BaseModel):
    """
    Complete manifest of rendering process.
    
    Tracks provenance and rendering status for all items.
    """
    
    # Metadata
    document_id: str
    source_filename: str
    render_timestamp: str
    
    # Previous layer timestamps
    assembly_timestamp: str
    representation_timestamp: str
    analysis_timestamp: str
    extraction_timestamp: str
    
    # Markdown output
    markdown_length: int  # Character count
    total_lines: int
    
    # Items rendered
    items: List[RenderedItem] = Field(default_factory=list)
    
    # Warnings
    warnings: List[RenderWarning] = Field(default_factory=list)
    
    # Statistics
    total_items: int = 0
    items_complete: int = 0
    items_partial: int = 0
    items_fallback: int = 0


class RenderedDocument(BaseModel):
    """
    Complete rendered output.
    
    Contains both markdown and manifest.
    """
    
    content: str  # The rendered markdown content
    manifest: RenderManifest
