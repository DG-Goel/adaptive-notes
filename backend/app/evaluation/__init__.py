"""
Evaluation module for assessing faithfulness and coverage.

This module provides:
1. Structural evaluation: coverage, provenance integrity, representation validity
2. Semantic verification: factual correctness of extracted claims against source text

Use FaithfulnessEvaluator for structural checks.
Use DeterministicSemanticVerifier for semantic faithfulness verification.
"""

from app.evaluation.models import (
    EvaluationResult,
    CoverageMetrics,
    ProvenanceError,
    RepresentationError,
    ContentWarning,
    ItemFinding,
    EvaluationStatus
)
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import (
    DeterministicSemanticVerifier,
    SemanticVerificationReport,
    ClaimVerification,
    SemanticVerificationStatus,
    NumericVerification,
    EntityVerification
)

__all__ = [
    # Structural evaluation
    "EvaluationResult",
    "CoverageMetrics",
    "ProvenanceError",
    "RepresentationError",
    "ContentWarning",
    "ItemFinding",
    "EvaluationStatus",
    "FaithfulnessEvaluator",
    
    # Semantic verification
    "DeterministicSemanticVerifier",
    "SemanticVerificationReport",
    "ClaimVerification",
    "SemanticVerificationStatus",
    "NumericVerification",
    "EntityVerification",
]
