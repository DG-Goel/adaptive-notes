"""
Data models for representation selection.

Defines the output structure of the Representation Selector layer.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.representation.formats import RepresentationFormat


class SelectedRepresentation(BaseModel):
    section: Optional[str] = None
    source_position: Optional[int] = None
    educational_context: Dict[str, Any] = Field(default_factory=dict)
    """
    A knowledge item with selected representation format(s).
    
    Contains the format choice, confidence, reasoning, and format-specific
    content extracted from the original knowledge item.
    """
    
    # Identification (preserved from original)
    knowledge_id: str
    document_id: str
    knowledge_type: str  # From original KnowledgeItem
    
    # Source traceability (preserved exactly)
    source_unit_ids: List[str]
    
    # Format selection
    primary_format: RepresentationFormat
    secondary_format: Optional[RepresentationFormat] = None
    
    # Selection metadata
    selection_confidence: float  # 0.0-1.0
    confidence_label: Literal["high", "medium", "low", "fallback"]
    selection_reasoning: str
    
    # Format-specific content
    # Structure depends on selected format (see DESIGN.md for schemas)
    format_content: Dict[str, Any]
    
    # Optional secondary content (if secondary_format is set)
    secondary_content: Optional[Dict[str, Any]] = None


class RepresentationStatistics(BaseModel):
    """Statistics about representation selection"""
    
    items_processed: int = 0
    format_distribution: Dict[RepresentationFormat, int] = Field(default_factory=dict)
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    items_with_secondary: int = 0
    fallback_count: int = 0


class RepresentationDocument(BaseModel):
    """
    Container for representations selected from analyzed knowledge.
    
    Maintains links to previous layers and adds representation decisions.
    """
    
    # Metadata
    document_id: str
    source_filename: str
    representation_timestamp: str
    
    # Previous layer info
    analysis_timestamp: str
    extraction_timestamp: str
    source_units_processed: int
    
    # Representations
    representations: List[SelectedRepresentation] = Field(default_factory=list)
    
    # Statistics
    statistics: RepresentationStatistics = Field(default_factory=RepresentationStatistics)
    
    def update_statistics(self):
        """Calculate statistics from representations"""
        self.statistics.items_processed = len(self.representations)
        
        # Count formats
        format_counts: Dict[RepresentationFormat, int] = {}
        conf_counts: Dict[str, int] = {}
        secondary_count = 0
        fallback_count = 0
        
        for rep in self.representations:
            # Count primary format
            format_counts[rep.primary_format] = format_counts.get(rep.primary_format, 0) + 1
            
            # Count secondary formats
            if rep.secondary_format:
                secondary_count += 1
                format_counts[rep.secondary_format] = format_counts.get(rep.secondary_format, 0) + 1
            
            # Count confidence levels
            conf_counts[rep.confidence_label] = conf_counts.get(rep.confidence_label, 0) + 1
            
            # Count fallbacks
            if rep.confidence_label == "fallback":
                fallback_count += 1
        
        self.statistics.format_distribution = format_counts
        self.statistics.confidence_distribution = conf_counts
        self.statistics.items_with_secondary = secondary_count
        self.statistics.fallback_count = fallback_count
