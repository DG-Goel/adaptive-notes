"""
Knowledge Model for educational content extraction.

Represents structured knowledge extracted from source documents
while maintaining complete traceability to source units.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Literal

from pydantic import BaseModel, Field, ConfigDict, model_serializer
from app.models.educational_review import EducationalReview


class KnowledgeItem(BaseModel):
    educational_review: Optional[EducationalReview] = None

    @model_serializer(mode='wrap')
    def preserve_legacy_shape(self,handler):
        data=handler(self)
        if self.educational_review is None:data.pop('educational_review',None)
        return data
    """
    Base class for all extracted knowledge.
    
    Every knowledge item maintains links to the source units
    that support it, enabling verification and citation.
    """
    model_config = ConfigDict(extra='forbid')
    
    knowledge_id: str
    knowledge_type: str  # concept, definition, explanation, example, fact, formula, procedure, relationship
    
    # Source traceability (required)
    source_unit_ids: List[str]  # Links back to SourceUnit.source_id
    document_id: str
    
    # Content (what we extracted)
    content: str  # Primary content
    
    # Context
    section: Optional[str] = None
    page_range: Optional[Tuple[int, int]] = None  # (start_page, end_page)
    
    # Metadata
    confidence: Optional[str] = None  # high, medium, low, unknown
    extraction_metadata: Optional[Dict[str, Any]] = None


class Concept(KnowledgeItem):
    """
    A named concept or term being introduced or discussed.
    
    Example: "short story", "protagonist", "plot"
    """
    knowledge_type: Literal["concept"] = "concept"
    concept_name: str
    aliases: List[str] = Field(default_factory=list)


class Definition(KnowledgeItem):
    """
    A formal definition of a concept.
    
    Example: "A short story is a prose narrative of limited length..."
    """
    knowledge_type: Literal["definition"] = "definition"
    term: str
    definition_text: str
    context: Optional[str] = None  # e.g., "in mathematics", "in biology"


class Explanation(KnowledgeItem):
    """
    An explanation of how or why something works.
    
    Example: Explaining why dreams might be prophetic in literature
    """
    knowledge_type: Literal["explanation"] = "explanation"
    topic: str
    explanation_text: str
    explanation_type: Optional[str] = None  # causal, procedural, functional, interpretive


class Example(KnowledgeItem):
    """
    A concrete example or illustration.
    
    Example: The story "I Sell My Dreams" illustrating magical realism
    """
    knowledge_type: Literal["example"] = "example"
    exemplifies: str  # What concept/principle it demonstrates
    example_text: str
    example_type: Optional[str] = None  # case_study, numerical, analogy, literary


class Fact(KnowledgeItem):
    """
    A factual statement.
    
    Example: "Pablo Neruda was a Chilean poet"
    """
    knowledge_type: Literal["fact"] = "fact"
    fact_text: str
    fact_type: Optional[str] = None  # historical, statistical, empirical, biographical


class Formula(KnowledgeItem):
    """
    A mathematical or scientific formula.
    
    Example: E = mc²
    """
    knowledge_type: Literal["formula"] = "formula"
    formula_text: str  # The formula itself
    variables: Optional[Dict[str, str]] = None  # {symbol: description}
    conditions: Optional[str] = None
    derivation: Optional[str] = None


class Procedure(KnowledgeItem):
    """
    A step-by-step procedure or algorithm.
    
    Example: Steps to analyze a short story
    """
    knowledge_type: Literal["procedure"] = "procedure"
    procedure_name: str
    steps: List[str]
    prerequisites: Optional[List[str]] = None
    outcomes: Optional[str] = None


class Relationship(KnowledgeItem):
    """
    A relationship between concepts.
    
    Example: "short story" IS_A "prose narrative"
    """
    knowledge_type: Literal["relationship"] = "relationship"
    relationship_type: str  # is_a, part_of, causes, requires, contrasts_with, exemplifies
    subject: str
    object: str
    description: Optional[str] = None


class KnowledgeDocument(BaseModel):
    """
    Container for all knowledge extracted from a source document.
    
    Organizes extracted knowledge by type and maintains statistics
    about the extraction process.
    """
    document_id: str
    source_filename: str
    extraction_timestamp: str
    
    # Extracted knowledge by type
    concepts: List[Concept] = Field(default_factory=list)
    definitions: List[Definition] = Field(default_factory=list)
    explanations: List[Explanation] = Field(default_factory=list)
    examples: List[Example] = Field(default_factory=list)
    facts: List[Fact] = Field(default_factory=list)
    formulas: List[Formula] = Field(default_factory=list)
    procedures: List[Procedure] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    
    # Statistics
    total_items: int = 0
    source_units_processed: int = 0
    
    # Extraction diagnostics (added for reliability tracking)
    extraction_metadata: Optional[Dict[str, Any]] = None
    
    def get_all_items(self) -> List[KnowledgeItem]:
        """Get all knowledge items as a flat list"""
        return (
            self.concepts +
            self.definitions +
            self.explanations +
            self.examples +
            self.facts +
            self.formulas +
            self.procedures +
            self.relationships
        )
    
    def update_statistics(self):
        """Update total_items count"""
        self.total_items = len(self.get_all_items())


class ExtractionChunk(BaseModel):
    source_states: Dict[str, str] = Field(default_factory=dict)
    literal_source_texts: Dict[str, str] = Field(default_factory=dict)
    ingestion_binding: Optional[str] = None
    context_source_ids: List[str] = Field(default_factory=list)
    context_text: str = ''
    context_limitations: List[str] = Field(default_factory=list)
    review_source_ids: List[str] = Field(default_factory=list)
    uninterpreted_source_ids: List[str] = Field(default_factory=list)
    """
    A manageable piece of content for extraction.
    
    Groups source units by section/page to create chunks
    that fit within LLM context windows.
    
    Supports adaptive splitting for truncation recovery.
    """
    chunk_id: str
    source_units: List[str]  # SourceUnit IDs in this chunk
    section: Optional[str] = None
    page_range: Optional[Tuple[int, int]] = None
    text_content: str  # Concatenated text for LLM
    
    # Metadata
    token_count: Optional[int] = None
    
    # Splitting metadata (for adaptive splitting)
    split_depth: int = 0  # 0 = original chunk, 1 = first split, etc.
    parent_chunk_id: Optional[str] = None  # ID of parent chunk if this is a sub-chunk
    # Exact character ranges in canonical source units for output-budget splitting.
    source_spans: Optional[Dict[str, Tuple[int, int]]] = None


# Discriminated union for proper serialization of knowledge item subtypes
from typing import Annotated
from pydantic import Field as PydanticField

KnowledgeItemType = Annotated[
    Union[Concept, Definition, Explanation, Example, Fact, Formula, Procedure, Relationship],
    PydanticField(discriminator='knowledge_type')
]
