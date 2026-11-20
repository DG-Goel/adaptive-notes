"""
Content characteristics and analyzed knowledge data models.

Defines the structural characteristics that can be identified in knowledge items
and the data models for representing analyzed knowledge.
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Dict, Any

from pydantic import BaseModel, Field

from app.models.knowledge import KnowledgeItemType


class ContentCharacteristic(str, Enum):
    """
    Structural characteristics of knowledge content.
    
    These describe HOW information is structured, not WHAT representation to use.
    Representation selection happens in a later layer.
    """
    
    # Clear structural patterns
    DEFINITION = "definition"              # Defines what something is
    SEQUENCE = "sequence"                  # Ordered steps or temporal progression
    COMPARISON = "comparison"              # Contrasts or compares multiple items
    CAUSE_EFFECT = "cause_effect"          # Causal relationships
    HIERARCHY = "hierarchy"                # Parent-child or categorical structure
    RELATIONSHIP = "relationship"          # General connections between concepts
    FACTUAL_EXPLANATION = "factual_explanation"  # Describes how/why with facts
    EXAMPLE = "example"                    # Illustrates a concept
    
    # Explicit uncertainty
    UNKNOWN = "unknown"                    # Cannot classify with confidence


class AnalyzedKnowledge(BaseModel):
    """
    A knowledge item with identified structural characteristics.
    
    Wraps the original KnowledgeItem and adds analysis results without
    modifying the original extracted knowledge.
    """
    
    # Original knowledge item (unchanged) - using discriminated union for proper serialization
    knowledge_item: KnowledgeItemType
    
    # Analysis results
    characteristics: List[ContentCharacteristic]
    analysis_confidence: Literal["high", "medium", "low", "insufficient"]
    analysis_reasoning: str
    
    # Quick access to provenance (from wrapped item)
    @property
    def knowledge_id(self) -> str:
        return self.knowledge_item.knowledge_id
    
    @property
    def source_unit_ids(self) -> List[str]:
        return self.knowledge_item.source_unit_ids
    
    @property
    def document_id(self) -> str:
        return self.knowledge_item.document_id


class AnalysisStatistics(BaseModel):
    """Statistics about the content analysis process"""
    
    items_analyzed: int = 0
    characteristics_distribution: Dict[ContentCharacteristic, int] = Field(default_factory=dict)
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    multiple_characteristics_count: int = 0
    unknown_count: int = 0


class AnalyzedKnowledgeDocument(BaseModel):
    """
    Container for analyzed knowledge items.
    
    Maintains link to original KnowledgeDocument and adds analysis results.
    """
    
    # Metadata
    document_id: str
    source_filename: str
    analysis_timestamp: str
    
    # Original extraction info
    extraction_timestamp: str
    source_units_processed: int
    
    # Analyzed items
    analyzed_items: List[AnalyzedKnowledge] = Field(default_factory=list)
    
    # Statistics
    statistics: AnalysisStatistics = Field(default_factory=AnalysisStatistics)
    
    def update_statistics(self):
        """Calculate statistics from analyzed items"""
        self.statistics.items_analyzed = len(self.analyzed_items)
        
        # Count characteristics
        char_counts: Dict[ContentCharacteristic, int] = {}
        conf_counts: Dict[str, int] = {}
        multiple_count = 0
        unknown_count = 0
        
        for item in self.analyzed_items:
            # Count each characteristic
            for char in item.characteristics:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            # Count multiple characteristics
            if len(item.characteristics) > 1:
                multiple_count += 1
            
            # Count unknown
            if ContentCharacteristic.UNKNOWN in item.characteristics:
                unknown_count += 1
            
            # Count confidence levels
            conf_counts[item.analysis_confidence] = conf_counts.get(item.analysis_confidence, 0) + 1
        
        self.statistics.characteristics_distribution = char_counts
        self.statistics.confidence_distribution = conf_counts
        self.statistics.multiple_characteristics_count = multiple_count
        self.statistics.unknown_count = unknown_count
