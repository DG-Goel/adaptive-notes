"""
Data models for faithfulness and coverage evaluation.

Defines structured output for evaluation results, findings, and recommendations.
"""

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


class CoverageMetrics(BaseModel):
    """
    Coverage statistics for the pipeline.
    
    Tracks how many items make it through each stage with explicit denominators.
    
    IMPORTANT: Extraction coverage (extracted/source_units) is a STRUCTURAL proxy,
    not a definitive measure of semantic completeness. One source unit may contain
    zero, one, or multiple knowledge items depending on content density and
    extraction criteria. Use this metric to detect gross extraction failures,
    not to judge semantic completeness.
    """
    
    # Source layer
    total_source_units: int
    source_units_with_text: int
    
    # Extraction layer
    total_knowledge_items_extracted: int
    knowledge_items_by_type: Dict[str, int] = Field(default_factory=dict)
    
    # Analysis layer
    total_items_analyzed: int
    items_analyzed_by_confidence: Dict[str, int] = Field(default_factory=dict)
    
    # Assembly layer
    total_items_assembled: int
    items_assembled_by_format: Dict[str, int] = Field(default_factory=dict)
    
    # Rendering layer
    total_items_rendered: int
    items_rendered_by_format: Dict[str, int] = Field(default_factory=dict)
    items_rendered_by_status: Dict[str, int] = Field(default_factory=dict)
    
    # Coverage ratios (explicit)
    extraction_coverage_ratio: float  # extracted / source_units_with_text (structural proxy only)
    analysis_coverage_ratio: float  # analyzed / extracted
    assembly_coverage_ratio: float  # assembled / analyzed (or extracted if no analysis)
    rendering_coverage_ratio: float  # rendered / assembled
    end_to_end_coverage_ratio: float  # rendered / extracted
    
    # Missing items
    knowledge_ids_not_analyzed: List[str] = Field(default_factory=list)
    knowledge_ids_not_assembled: List[str] = Field(default_factory=list)
    knowledge_ids_not_rendered: List[str] = Field(default_factory=list)


class ProvenanceError(BaseModel):
    """Error in provenance tracking or reference integrity."""
    
    error_type: Literal[
        "unknown_knowledge_id",
        "unknown_source_unit_id",
        "missing_source_units",
        "inconsistent_mapping",
        "duplicate_knowledge_id",
        "missing_analyzed_item",
        "unexpected_analyzed_id",
        "document_id_mismatch"
    ]
    knowledge_id: str
    source_unit_ids: List[str] = Field(default_factory=list)
    message: str
    location: Optional[str] = None  # e.g., "assembly", "rendering"


class RepresentationError(BaseModel):
    """Error in representation format or structure."""
    
    error_type: Literal[
        "missing_required_field",
        "malformed_payload",
        "invalid_mermaid_structure",
        "empty_collection",
        "type_mismatch"
    ]
    knowledge_id: str
    representation_format: str
    missing_fields: List[str] = Field(default_factory=list)
    message: str


class ContentWarning(BaseModel):
    """Warning about content integrity issues."""
    
    warning_type: Literal[
        "missing_rendered_item",
        "duplicated_knowledge_id",
        "suspicious_content_change",
        "empty_content",
        "truncated_content"
    ]
    knowledge_id: str
    message: str
    details: Optional[Dict[str, str]] = None


class ItemFinding(BaseModel):
    """Detailed finding for a specific knowledge item."""
    
    knowledge_id: str
    knowledge_type: str
    source_unit_ids: List[str]
    
    # Status through pipeline
    extracted: bool = True
    analyzed: bool = False
    represented: bool = False
    assembled: bool = False
    rendered: bool = False
    
    # Issues
    provenance_errors: List[str] = Field(default_factory=list)
    representation_errors: List[str] = Field(default_factory=list)
    content_warnings: List[str] = Field(default_factory=list)
    
    # Format information
    representation_format: Optional[str] = None
    rendering_status: Optional[str] = None


class EvaluationStatus(BaseModel):
    """Overall evaluation status."""
    
    status: Literal["pass", "warning", "fail", "incomplete"]
    
    # Summary counts
    total_errors: int = 0
    total_warnings: int = 0
    
    # Error breakdown
    provenance_errors: int = 0
    representation_errors: int = 0
    content_warnings: int = 0
    
    # Pass criteria
    coverage_acceptable: bool = True
    provenance_valid: bool = True
    representations_valid: bool = True
    pipeline_complete: bool = True  # All stages have data
    
    summary_message: str = ""


class EvaluationResult(BaseModel):
    """
    Complete evaluation result.
    
    Contains all findings, metrics, and recommendations.
    """
    
    # Metadata
    evaluation_timestamp: str
    document_id: str
    source_filename: str
    
    # Overall status
    status: EvaluationStatus
    
    # Coverage metrics
    coverage: CoverageMetrics
    
    # Findings (structured)
    provenance_errors: List[ProvenanceError] = Field(default_factory=list)
    representation_errors: List[RepresentationError] = Field(default_factory=list)
    content_warnings: List[ContentWarning] = Field(default_factory=list)
    
    # Per-item findings
    item_findings: List[ItemFinding] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    
    # Semantic faithfulness verification
    semantic_faithfulness_verified: bool = False
    semantic_faithfulness_note: str = (
        "Semantic faithfulness (factual correctness of extracted claims) "
        "was NOT verified in this evaluation. Only structural validity and "
        "provenance integrity were checked. Use SemanticVerifier for "
        "semantic faithfulness verification."
    )
    
    # Optional: Semantic verification report (if performed)
    semantic_verification_report: Optional[dict] = None  # SemanticVerificationReport as dict
