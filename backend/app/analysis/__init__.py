"""
Content Analysis layer for identifying structural characteristics.

This layer analyzes extracted knowledge to identify structural patterns
such as definitions, sequences, comparisons, cause-effect relationships, etc.

Analysis is rule-based and deterministic - no LLM calls are made.
"""

from app.analysis.characteristics import (
    ContentCharacteristic,
    AnalyzedKnowledge,
    AnalyzedKnowledgeDocument,
    AnalysisStatistics
)
from app.analysis.analyzer import ContentAnalyzer

__all__ = [
    "ContentCharacteristic",
    "AnalyzedKnowledge",
    "AnalyzedKnowledgeDocument",
    "AnalysisStatistics",
    "ContentAnalyzer",
]
