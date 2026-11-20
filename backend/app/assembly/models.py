"""
Data models for note assembly.

Defines the output structure of the Note Assembler layer.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.representation.formats import RepresentationFormat


class AssembledItem(BaseModel):
    educational_context: Dict[str, Any] = Field(default_factory=dict)
    """
    A knowledge item ready for rendering.
    
    Preserves representation selection and adds assembly metadata.
    """
    
    # Identification (preserved)
    knowledge_id: str
    document_id: str
    knowledge_type: str
    
    # Representation format (preserved)
    primary_format: RepresentationFormat
    format_content: Dict[str, Any]
    secondary_format: Optional[RepresentationFormat] = None
    secondary_content: Optional[Dict[str, Any]] = None
    
    # Selection metadata (preserved)
    selection_confidence: float
    confidence_label: str
    selection_reasoning: str
    
    # Provenance (preserved)
    source_unit_ids: List[str]
    
    # Assembly metadata (new)
    position_in_section: int
    ordering_rationale: str  # How this item was ordered


class AssembledSection(BaseModel):
    """
    A section containing organized knowledge items.
    """
    
    section_id: str  # "section_0", "section_1", etc.
    section_name: str  # Original section name or "Main Content"
    section_type: str  # "named_section", "default_section"
    items: List[AssembledItem] = Field(default_factory=list)
    
    @property
    def item_count(self) -> int:
        return len(self.items)


class AssemblyMetadata(BaseModel):
    """Metadata about the assembly process"""
    
    assembly_timestamp: str
    ordering_strategy: str  # "section-based", "source-order", "id-based", "mixed"
    total_sections: int
    total_items: int
    items_with_section: int
    items_without_section: int
    duplicate_ids_found: int = 0


class AssemblyStatistics(BaseModel):
    """Statistics about assembled notes"""
    
    total_sections: int = 0
    total_items: int = 0
    items_by_format: Dict[RepresentationFormat, int] = Field(default_factory=dict)
    items_by_confidence: Dict[str, int] = Field(default_factory=dict)
    average_items_per_section: float = 0.0


class AssembledNotesDocument(BaseModel):
    """
    Complete assembled notes ready for rendering.
    
    Contains organized sections with ordered items.
    """
    
    # Metadata
    document_id: str
    source_filename: str
    assembly_timestamp: str
    
    # Previous layer timestamps
    representation_timestamp: str
    analysis_timestamp: str
    extraction_timestamp: str
    source_units_processed: int
    
    # Organized content
    sections: List[AssembledSection] = Field(default_factory=list)
    
    # Assembly metadata
    metadata: AssemblyMetadata
    
    # Statistics
    statistics: AssemblyStatistics = Field(default_factory=AssemblyStatistics)
    
    def update_statistics(self):
        """Calculate statistics from assembled sections"""
        total_items = sum(section.item_count for section in self.sections)
        
        # Count by format
        format_counts: Dict[RepresentationFormat, int] = {}
        conf_counts: Dict[str, int] = {}
        
        for section in self.sections:
            for item in section.items:
                # Count primary format
                format_counts[item.primary_format] = format_counts.get(item.primary_format, 0) + 1
                
                # Count confidence
                conf_counts[item.confidence_label] = conf_counts.get(item.confidence_label, 0) + 1
        
        # Calculate statistics
        self.statistics.total_sections = len(self.sections)
        self.statistics.total_items = total_items
        self.statistics.items_by_format = format_counts
        self.statistics.items_by_confidence = conf_counts
        self.statistics.average_items_per_section = (
            total_items / len(self.sections) if len(self.sections) > 0 else 0.0
        )
