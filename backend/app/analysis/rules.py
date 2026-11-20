"""
Classification rules for content analysis.

Implements rule-based logic to identify structural characteristics
from extracted knowledge items.
"""

import re
from typing import List, Tuple

from app.models.knowledge import (
    KnowledgeItem,
    Concept,
    Definition,
    Explanation,
    Example,
    Fact,
    Formula,
    Procedure,
    Relationship
)
from app.analysis.characteristics import ContentCharacteristic


class ClassificationRules:
    """
    Rule-based classifier for knowledge items.
    
    Uses type-based and content-based rules to identify structural
    characteristics without any LLM calls.
    """
    
    # Keywords for content-based detection
    CAUSE_EFFECT_KEYWORDS = [
        "because", "therefore", "thus", "consequently", "as a result",
        "causes", "caused", "leads to", "results in", "due to"
    ]
    
    SEQUENCE_KEYWORDS = [
        "first", "second", "third", "then", "next", "finally", "after",
        "before", "subsequently", "following", "step"
    ]
    
    COMPARISON_KEYWORDS = [
        "compared to", "versus", "vs", "while", "whereas", "unlike",
        "in contrast", "on the other hand", "however", "but"
    ]
    
    @classmethod
    def classify(cls, item: KnowledgeItem) -> Tuple[List[ContentCharacteristic], str, str]:
        """
        Classify a knowledge item.
        
        Returns:
            (characteristics, confidence, reasoning)
        """
        
        # Try type-based classification first (high confidence)
        chars, conf, reason = cls._classify_by_type(item)
        
        if chars:
            return chars, conf, reason
        
        # Fall back to content-based classification (medium confidence)
        chars, conf, reason = cls._classify_by_content(item)
        
        if chars:
            return chars, conf, reason
        
        # Unable to classify
        return [ContentCharacteristic.UNKNOWN], "insufficient", "No clear structural markers detected"
    
    @classmethod
    def _classify_by_type(cls, item: KnowledgeItem) -> Tuple[List[ContentCharacteristic], str, str]:
        """Classify based on knowledge type (high confidence)"""
        
        if isinstance(item, Definition):
            return [ContentCharacteristic.DEFINITION], "high", "Explicit definition structure"
        
        if isinstance(item, Example):
            return [ContentCharacteristic.EXAMPLE], "high", "Explicit example structure"
        
        if isinstance(item, Procedure):
            # Procedures are sequences that also explain how to do something
            if len(item.steps) > 1:
                return (
                    [ContentCharacteristic.SEQUENCE, ContentCharacteristic.FACTUAL_EXPLANATION],
                    "high",
                    "Ordered steps forming a sequence with explanatory content"
                )
            else:
                return [ContentCharacteristic.SEQUENCE], "medium", "Single-step procedure"
        
        if isinstance(item, Relationship):
            return cls._classify_relationship(item)
        
        if isinstance(item, Explanation):
            return cls._classify_explanation(item)
        
        if isinstance(item, Fact):
            # Facts are typically factual explanations
            # But check for specific types
            if item.fact_type == "statistical":
                return (
                    [ContentCharacteristic.FACTUAL_EXPLANATION, ContentCharacteristic.COMPARISON],
                    "medium",
                    "Statistical fact may involve comparison"
                )
            return [ContentCharacteristic.FACTUAL_EXPLANATION], "medium", "Factual statement"
        
        if isinstance(item, Concept):
            return cls._classify_concept(item)
        
        if isinstance(item, Formula):
            return [ContentCharacteristic.DEFINITION], "high", "Formula defines a mathematical relationship"
        
        return [], "", ""
    
    @classmethod
    def _classify_relationship(cls, item: Relationship) -> Tuple[List[ContentCharacteristic], str, str]:
        """Classify relationship based on relationship_type"""
        
        rel_type = item.relationship_type.lower()
        
        if rel_type in ["is_a", "part_of", "subclass_of", "instance_of"]:
            return [ContentCharacteristic.HIERARCHY], "high", f"Hierarchical relationship: {rel_type}"
        
        if rel_type in ["causes", "causes_effect", "leads_to"]:
            return [ContentCharacteristic.CAUSE_EFFECT], "high", f"Causal relationship: {rel_type}"
        
        if rel_type in ["contrasts_with", "differs_from", "opposite_of"]:
            return [ContentCharacteristic.COMPARISON], "high", f"Comparative relationship: {rel_type}"
        
        if rel_type in ["exemplifies", "illustrates"]:
            return [ContentCharacteristic.EXAMPLE], "high", f"Example relationship: {rel_type}"
        
        # Generic relationship
        return [ContentCharacteristic.RELATIONSHIP], "medium", f"General relationship: {rel_type}"
    
    @classmethod
    def _classify_explanation(cls, item: Explanation) -> Tuple[List[ContentCharacteristic], str, str]:
        """Classify explanation based on explanation_type and content"""
        
        exp_type = item.explanation_type
        
        if exp_type == "causal":
            return (
                [ContentCharacteristic.CAUSE_EFFECT, ContentCharacteristic.FACTUAL_EXPLANATION],
                "high",
                "Causal explanation type"
            )
        
        if exp_type == "procedural":
            return (
                [ContentCharacteristic.SEQUENCE, ContentCharacteristic.FACTUAL_EXPLANATION],
                "high",
                "Procedural explanation type"
            )
        
        if exp_type in ["functional", "interpretive"]:
            return (
                [ContentCharacteristic.FACTUAL_EXPLANATION],
                "high",
                f"{exp_type.capitalize()} explanation"
            )
        
        # No explicit type, check content
        return cls._check_content_keywords(item.explanation_text, "explanation")
    
    @classmethod
    def _classify_concept(cls, item: Concept) -> Tuple[List[ContentCharacteristic], str, str]:
        """Classify concept based on available information"""
        
        # Concepts with aliases are implicit definitions
        if item.aliases:
            return (
                [ContentCharacteristic.DEFINITION],
                "medium",
                "Concept with aliases implies definition"
            )
        
        # Check content length
        if len(item.content) < 10:
            return (
                [ContentCharacteristic.UNKNOWN],
                "insufficient",
                "Minimal content, no clear structure"
            )
        
        # Check for structural keywords in content
        chars, conf, reason = cls._check_content_keywords(item.content, "concept")
        if chars and ContentCharacteristic.UNKNOWN not in chars:
            return chars, conf, reason
        
        # Unable to classify with confidence
        return (
            [ContentCharacteristic.UNKNOWN],
            "insufficient",
            "Concept without aliases or clear structural markers"
        )
    
    @classmethod
    def _check_content_keywords(cls, text: str, item_type: str) -> Tuple[List[ContentCharacteristic], str, str]:
        """Check content for structural keywords"""
        
        text_lower = text.lower()
        found_chars = []
        reasons = []
        
        # Check for cause-effect
        if any(keyword in text_lower for keyword in cls.CAUSE_EFFECT_KEYWORDS):
            found_chars.append(ContentCharacteristic.CAUSE_EFFECT)
            reasons.append("cause-effect keywords")
        
        # Check for sequence
        if any(keyword in text_lower for keyword in cls.SEQUENCE_KEYWORDS):
            found_chars.append(ContentCharacteristic.SEQUENCE)
            reasons.append("sequence keywords")
        
        # Check for comparison
        if any(keyword in text_lower for keyword in cls.COMPARISON_KEYWORDS):
            found_chars.append(ContentCharacteristic.COMPARISON)
            reasons.append("comparison keywords")
        
        # If we found structural markers
        if found_chars:
            # Also add factual explanation if it's describing something
            if item_type in ["explanation", "fact"]:
                found_chars.append(ContentCharacteristic.FACTUAL_EXPLANATION)
            
            reason = f"Content contains {', '.join(reasons)}"
            return found_chars, "medium", reason
        
        # Default for explanations/facts without clear markers
        if item_type in ["explanation", "fact"]:
            return [ContentCharacteristic.FACTUAL_EXPLANATION], "medium", "Default for explanatory content"
        
        return [], "", ""
