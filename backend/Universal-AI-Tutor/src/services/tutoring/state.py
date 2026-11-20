"""
Tutoring workflow state definition.

Defines the TypedDict for LangGraph workflow state.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class TutoringState(TypedDict, total=False):
    """
    State for the tutoring workflow.
    
    Represents the state passed between nodes in the LangGraph workflow.
    """
    
    # Input
    question: str
    top_k: int
    notes_file: Optional[str]
    """User's question"""
    
    mode: Literal["strict", "teaching"]
    """Answer generation mode"""
    
    conversation_history: List[Dict[str, str]]
    """Previous Q&A pairs for context"""
    
    # Retrieval
    retrieved_chunks: List[Dict[str, Any]]
    """Retrieved context chunks"""
    
    retrieval_results: List[Any]
    """Full retrieval results with metadata"""
    
    # Evidence assessment
    evidence_sufficient: bool
    """Whether evidence is sufficient to answer"""
    
    evidence_assessment: Optional[Dict[str, Any]]
    """Detailed evidence assessment metrics"""
    
    retry_count: int
    """Number of retrieval retries"""
    
    # Generation
    answer: str
    """Generated answer"""
    
    citations: List[Dict[str, str]]
    """Source citations"""
    
    # Metadata
    metadata: Dict[str, Any]
    """Additional metadata (verification, timing, etc.)"""
    
    admit_unknown: bool
    """Flag to indicate insufficient information"""
