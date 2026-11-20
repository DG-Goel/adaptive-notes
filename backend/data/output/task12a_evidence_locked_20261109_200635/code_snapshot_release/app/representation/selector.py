"""
Representation selector - core selection logic.

Implements rule-based mapping from content characteristics to representation formats.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.knowledge import (
    KnowledgeItem,
    Definition,
    Example,
    Explanation,
    Fact,
    Formula,
    Procedure,
    Relationship,
    Concept
)
from app.analysis.characteristics import (
    AnalyzedKnowledge,
    AnalyzedKnowledgeDocument,
    ContentCharacteristic
)
from app.representation.formats import RepresentationFormat
from app.representation.models import (
    SelectedRepresentation,
    RepresentationDocument
)


class RepresentationSelector:
    """
    Selects appropriate representation formats for analyzed knowledge items.
    
    Uses deterministic rule-based selection with transparent scoring.
    No LLM calls - fully local and reproducible.
    """
    
    # Temporal keywords for timeline detection
    TEMPORAL_KEYWORDS = [
        "year", "month", "week", "day", "date", "time",
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "before", "after", "during", "when", "while"
    ]
    
    def __init__(self, verbose: bool = False):
        """
        Initialize representation selector.
        
        Args:
            verbose: Print selection progress
        """
        self.verbose = verbose
    
    def select(self, analyzed_doc: AnalyzedKnowledgeDocument) -> RepresentationDocument:
        """
        Select representations for all analyzed items.
        
        Args:
            analyzed_doc: Document with analyzed knowledge items
            
        Returns:
            RepresentationDocument with format selections
        """
        
        if self.verbose:
            print("\n" + "=" * 80)
            print("REPRESENTATION SELECTION")
            print("=" * 80)
            print(f"Document: {analyzed_doc.source_filename}")
            print(f"Items to process: {len(analyzed_doc.analyzed_items)}")
            print()
        
        # Create representation document
        rep_doc = RepresentationDocument(
            document_id=analyzed_doc.document_id,
            source_filename=analyzed_doc.source_filename,
            representation_timestamp=datetime.now().isoformat(),
            analysis_timestamp=analyzed_doc.analysis_timestamp,
            extraction_timestamp=analyzed_doc.extraction_timestamp,
            source_units_processed=analyzed_doc.source_units_processed
        )
        
        # Select representation for each item
        for i, analyzed_item in enumerate(analyzed_doc.analyzed_items, 1):
            if self.verbose:
                print(f"Processing {i}/{len(analyzed_doc.analyzed_items)}: {analyzed_item.knowledge_id}")
            
            representation = self._select_representation(analyzed_item)
            rep_doc.representations.append(representation)
            
            if self.verbose:
                print(f"  Primary: {representation.primary_format.value}")
                if representation.secondary_format:
                    print(f"  Secondary: {representation.secondary_format.value}")
                print(f"  Confidence: {representation.confidence_label} ({representation.selection_confidence:.2f})")
                print()
        
        # Update statistics
        rep_doc.update_statistics()
        
        if self.verbose:
            print("=" * 80)
            print("SELECTION COMPLETE")
            print("=" * 80)
            self._print_statistics(rep_doc)
        
        return rep_doc
    
    def _select_representation(self, analyzed_item: AnalyzedKnowledge) -> SelectedRepresentation:
        """
        Select representation format(s) for a single analyzed item.
        
        Args:
            analyzed_item: Analyzed knowledge item
            
        Returns:
            SelectedRepresentation with format choice
        """
        
        item = analyzed_item.knowledge_item
        characteristics = analyzed_item.characteristics
        
        # Score all candidate formats
        candidates = self._score_formats(item, characteristics)
        
        # Sort by score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select primary format (highest score)
        primary_format, primary_score, primary_reasoning = candidates[0]
        
        # Extract format-specific content
        primary_content = self._extract_format_content(item, primary_format)
        if not self._faithful_structure(item,primary_format,primary_content):
            primary_format=RepresentationFormat.STANDARD_TEXT
            primary_content=self._extract_standard_text_content(item)
            primary_score=0.0
            primary_reasoning='Source does not supply the structure required by this format'
        
        # Determine confidence label
        confidence_label = self._get_confidence_label(primary_score)
        
        # Check for secondary format
        secondary_format = None
        secondary_content = None
        
        if len(candidates) > 1:
            second_format, second_score, second_reasoning = candidates[1]
            
            # Only add secondary if it's ≥70% of primary and provides complementary value
            if (second_score >= primary_score * 0.7 and 
                second_format != primary_format and
                self._is_complementary(primary_format, second_format)):
                
                secondary_format = second_format
                secondary_content = self._extract_format_content(item, second_format)
                if not self._faithful_structure(item,second_format,secondary_content):
                    secondary_format=None;secondary_content=None
                primary_reasoning += f" | Secondary: {second_reasoning}"
        
        selected=SelectedRepresentation(
            section=item.section,
            knowledge_id=item.knowledge_id,
            document_id=item.document_id,
            knowledge_type=item.knowledge_type,
            source_unit_ids=item.source_unit_ids.copy(),
            primary_format=primary_format,
            secondary_format=secondary_format,
            selection_confidence=primary_score,
            confidence_label=confidence_label,
            selection_reasoning=primary_reasoning,
            format_content=primary_content,
            secondary_content=secondary_content
        )
        if isinstance(item,Formula) and not (item.educational_review and item.educational_review.formula_status=='COMPLETE'):
            selected.educational_context={'student_view':True,'notices':['Formula completeness requires source review; do not assume a complete equation.']}
        policy=(item.extraction_metadata or {}).get('source_grounding',{}).get('generation_policy')
        if policy and item.educational_review is None:
            from app.extraction.no_invention import project_policy
            project_policy(item,selected,policy)
        return selected

    @staticmethod
    def _faithful_structure(item,fmt,payload):
        if fmt==RepresentationFormat.COMPARISON_TABLE:
            return False  # No typed comparison dimensions/values exist in KnowledgeItem.
        if fmt==RepresentationFormat.HIERARCHY_TREE:
            return isinstance(item,Relationship) and item.relationship_type in ('is_a','part_of')
        if fmt==RepresentationFormat.CAUSE_EFFECT_DIAGRAM:
            return ((isinstance(item,Relationship) and item.relationship_type in ('causes','causal','cause_effect','leads_to'))
                    or (isinstance(item,Explanation) and bool(payload.get('cause')) and bool(payload.get('effect'))))
        if fmt==RepresentationFormat.FLOWCHART:
            return isinstance(item,Procedure) and bool(item.steps)
        if fmt==RepresentationFormat.TIMELINE:
            return bool(payload.get('events')) and all(e.get('time') in e.get('event','') for e in payload['events'])
        if fmt==RepresentationFormat.DEFINITION_BOX:
            return isinstance(item,(Definition,Concept,Formula))
        if fmt==RepresentationFormat.EXAMPLE_CALLOUT:
            return isinstance(item,Example)
        return True
    
    def _score_formats(
        self, 
        item: KnowledgeItem, 
        characteristics: List[ContentCharacteristic]
    ) -> List[Tuple[RepresentationFormat, float, str]]:
        """
        Score all candidate formats for this item.
        
        Returns:
            List of (format, score, reasoning) tuples
        """
        
        candidates = []
        
        # Try each format based on characteristics and content
        
        # DEFINITION_BOX
        if ContentCharacteristic.DEFINITION in characteristics:
            score, reason = self._score_definition_box(item)
            if score > 0:
                candidates.append((RepresentationFormat.DEFINITION_BOX, score, reason))
        
        # EXAMPLE_CALLOUT
        if ContentCharacteristic.EXAMPLE in characteristics:
            score, reason = self._score_example_callout(item)
            if score > 0:
                candidates.append((RepresentationFormat.EXAMPLE_CALLOUT, score, reason))
        
        # CAUSE_EFFECT_DIAGRAM
        if ContentCharacteristic.CAUSE_EFFECT in characteristics:
            score, reason = self._score_cause_effect_diagram(item)
            if score > 0:
                candidates.append((RepresentationFormat.CAUSE_EFFECT_DIAGRAM, score, reason))
        
        # HIERARCHY_TREE
        if ContentCharacteristic.HIERARCHY in characteristics:
            score, reason = self._score_hierarchy_tree(item)
            if score > 0:
                candidates.append((RepresentationFormat.HIERARCHY_TREE, score, reason))
        
        # COMPARISON_TABLE
        if ContentCharacteristic.COMPARISON in characteristics:
            score, reason = self._score_comparison_table(item)
            if score > 0:
                candidates.append((RepresentationFormat.COMPARISON_TABLE, score, reason))
        
        # SEQUENCE handling (FLOWCHART vs TIMELINE)
        if ContentCharacteristic.SEQUENCE in characteristics:
            # Check if it's temporal (TIMELINE) or procedural (FLOWCHART)
            if self._is_temporal_sequence(item):
                score, reason = self._score_timeline(item)
                if score > 0:
                    candidates.append((RepresentationFormat.TIMELINE, score, reason))
            else:
                score, reason = self._score_flowchart(item)
                if score > 0:
                    candidates.append((RepresentationFormat.FLOWCHART, score, reason))
        
        # FORMULA_DISPLAY
        if isinstance(item, Formula):
            score, reason = self._score_formula_display(item)
            if score > 0:
                candidates.append((RepresentationFormat.FORMULA_DISPLAY, score, reason))
        
        # Always add STANDARD_TEXT as fallback
        candidates.append((RepresentationFormat.STANDARD_TEXT, 0.2, "Fallback format"))
        
        return candidates
    
    def _score_definition_box(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score DEFINITION_BOX format"""
        
        if isinstance(item, Definition):
            if item.term and item.definition_text:
                return 0.95, "Definition with term and text"
            return 0.7, "Definition missing some fields"
        
        if isinstance(item, Concept):
            if item.aliases and len(item.content) > 10:
                return 0.8, "Concept with aliases serves as definition"
            return 0.5, "Concept with minimal definition content"
        
        if isinstance(item, Formula):
            return 0.7, "Formula defines a mathematical relationship"
        
        return 0.0, ""
    
    def _score_example_callout(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score EXAMPLE_CALLOUT format"""
        
        if isinstance(item, Example):
            if item.exemplifies and item.example_text:
                return 0.95, "Example with clear exemplification"
            return 0.7, "Example with incomplete fields"
        
        return 0.0, ""
    
    def _score_cause_effect_diagram(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score CAUSE_EFFECT_DIAGRAM format"""
        
        # For relationships, check if it's causal
        if isinstance(item, Relationship):
            if item.relationship_type in ["causes", "leads_to"]:
                return 0.85, "Causal relationship"
            return 0.0, ""
        
        # Need to be able to extract explicit cause and effect
        if isinstance(item, Explanation) and item.explanation_type == "causal":
            # Check if we can parse cause and effect
            if self._can_extract_cause_effect(item.explanation_text):
                return 0.9, "Causal explanation with extractable cause/effect"
            # If we cannot extract, prefer fallback to text
            return 0.0, ""
        
        # Check content for explicit cause-effect language
        content = self._get_item_text(item)
        if self._can_extract_cause_effect(content):
            return 0.5, "Content with extractable cause-effect structure"
        
        return 0.0, ""
    
    def _score_hierarchy_tree(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score HIERARCHY_TREE format"""
        
        if isinstance(item, Relationship):
            if item.relationship_type in ["is_a", "part_of", "subclass_of", "instance_of"]:
                # Need to verify we have multi-level structure
                # For now, single relationship is insufficient for tree visualization
                return 0.4, "Hierarchical relationship (single level insufficient for tree)"
        
        # Would need multiple related items to build a tree
        # Single items don't have enough structure
        return 0.0, ""
    
    def _score_comparison_table(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score COMPARISON_TABLE format"""
        
        if isinstance(item, Relationship):
            if item.relationship_type in ["contrasts_with", "differs_from"]:
                # Single relationship doesn't provide comparison dimensions
                return 0.3, "Comparison relationship (dimensions not explicit)"
        
        # Would need explicit comparison dimensions in content
        # Most single items don't contain structured comparison data
        return 0.0, ""
    
    def _score_flowchart(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score FLOWCHART format"""
        
        if isinstance(item, Procedure):
            if len(item.steps) >= 2:
                return 0.9, f"Procedure with {len(item.steps)} steps"
            return 0.5, "Single-step procedure (insufficient for flowchart)"
        
        if isinstance(item, Explanation) and item.explanation_type == "procedural":
            # Check if explanation contains step-like structure
            if self._has_step_structure(item.explanation_text):
                return 0.7, "Procedural explanation with step structure"
            return 0.4, "Procedural explanation without clear steps"
        
        return 0.0, ""
    
    def _score_timeline(self, item: KnowledgeItem) -> Tuple[float, str]:
        """Score TIMELINE format"""
        
        if isinstance(item, Procedure):
            # Only if explicitly temporal
            if len(item.steps) >= 2 and self._has_temporal_markers(item.steps):
                return 0.85, "Temporal sequence with multiple events"
            return 0.0, ""
        
        # Check for temporal sequence in content
        content = self._get_item_text(item)
        if self._has_temporal_markers([content]):
            return 0.6, "Content suggests chronological sequence"
        
        return 0.0, ""
    
    def _score_formula_display(self, item: Formula) -> Tuple[float, str]:
        """Score FORMULA_DISPLAY format"""
        
        if item.formula_text and len(item.formula_text.strip()) > 0:
            return 0.95, "Formula with valid formula text"
        
        return 0.3, "Formula without usable formula text"
    
    def _is_temporal_sequence(self, item: KnowledgeItem) -> bool:
        """Check if sequence has temporal (chronological) nature"""
        
        if isinstance(item, Procedure):
            # Check steps for temporal keywords
            return self._has_temporal_markers(item.steps)
        
        content = self._get_item_text(item)
        return self._has_temporal_markers([content])
    
    def _has_temporal_markers(self, texts: List[str]) -> bool:
        """Check if texts contain temporal keywords"""
        combined = " ".join(texts).lower()
        return any(keyword in combined for keyword in self.TEMPORAL_KEYWORDS)
    
    def _has_step_structure(self, text: str) -> bool:
        """Check if text contains step-like structure"""
        text_lower = text.lower()
        
        # Check for numbered/ordered steps
        if re.search(r'\b(step \d|first|second|third|then|next)\b', text_lower):
            return True
        
        # Check for bullet/list structure indicators
        if re.search(r'(\n\s*[-*•]\s|\n\s*\d+\.)', text):
            return True
        
        return False
    
    def _can_extract_cause_effect(self, text: str) -> bool:
        """Check if we can extract explicit cause and effect from text"""
        text_lower = text.lower()
        
        # Look for explicit cause-effect connectors
        cause_effect_patterns = [
            r'because\s+.+?,\s+',  # "because X, Y" - comma indicates effect follows
            r'since\s+.+?,\s+',     # "since X, Y"
            r'therefore\s+',         # "therefore Y"
            r'.+?\s+causes\s+.+',
            r'.+?\s+results in\s+.+',
            r'.+?\s+leads to\s+.+'
        ]
        
        return any(re.search(pattern, text_lower) for pattern in cause_effect_patterns)
    
    def _get_item_text(self, item: KnowledgeItem) -> str:
        """Get primary text content from any knowledge item type"""
        
        if isinstance(item, Definition):
            return item.definition_text
        elif isinstance(item, Example):
            return item.example_text
        elif isinstance(item, Explanation):
            return item.explanation_text
        elif isinstance(item, Fact):
            return item.fact_text
        elif isinstance(item, Formula):
            return item.formula_text
        elif isinstance(item, Procedure):
            return " ".join(item.steps)
        elif isinstance(item, Relationship):
            return item.description or f"{item.subject} {item.relationship_type} {item.object}"
        elif isinstance(item, Concept):
            return item.content
        else:
            return item.content
    
    def _is_complementary(self, fmt1: RepresentationFormat, fmt2: RepresentationFormat) -> bool:
        """Check if two formats provide complementary views"""
        
        # DEFINITION_BOX + EXAMPLE_CALLOUT are complementary
        if {fmt1, fmt2} == {RepresentationFormat.DEFINITION_BOX, RepresentationFormat.EXAMPLE_CALLOUT}:
            return True
        
        # FLOWCHART + STANDARD_TEXT are complementary
        if {fmt1, fmt2} == {RepresentationFormat.FLOWCHART, RepresentationFormat.STANDARD_TEXT}:
            return True
        
        # CAUSE_EFFECT_DIAGRAM + STANDARD_TEXT are complementary
        if {fmt1, fmt2} == {RepresentationFormat.CAUSE_EFFECT_DIAGRAM, RepresentationFormat.STANDARD_TEXT}:
            return True
        
        # Most structured formats + STANDARD_TEXT are complementary
        if RepresentationFormat.STANDARD_TEXT in {fmt1, fmt2}:
            return True
        
        return False
    
    def _get_confidence_label(self, score: float) -> str:
        """Convert score to confidence label"""
        
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.3:
            return "low"
        else:
            return "fallback"
    
    def _extract_format_content(
        self, 
        item: KnowledgeItem, 
        fmt: RepresentationFormat
    ) -> Dict[str, Any]:
        """
        Extract format-specific content from knowledge item.
        
        Args:
            item: Knowledge item
            fmt: Target format
            
        Returns:
            Dictionary with format-specific fields
        """
        
        if fmt == RepresentationFormat.DEFINITION_BOX:
            return self._extract_definition_box_content(item)
        elif fmt == RepresentationFormat.EXAMPLE_CALLOUT:
            return self._extract_example_callout_content(item)
        elif fmt == RepresentationFormat.FLOWCHART:
            return self._extract_flowchart_content(item)
        elif fmt == RepresentationFormat.TIMELINE:
            return self._extract_timeline_content(item)
        elif fmt == RepresentationFormat.CAUSE_EFFECT_DIAGRAM:
            return self._extract_cause_effect_content(item)
        elif fmt == RepresentationFormat.HIERARCHY_TREE:
            return self._extract_hierarchy_content(item)
        elif fmt == RepresentationFormat.COMPARISON_TABLE:
            return self._extract_comparison_content(item)
        elif fmt == RepresentationFormat.FORMULA_DISPLAY:
            return self._extract_formula_content(item)
        else:  # STANDARD_TEXT
            return self._extract_standard_text_content(item)
    
    def _extract_definition_box_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for DEFINITION_BOX"""
        
        if isinstance(item, Definition):
            return {
                "term": item.term,
                "definition": item.definition_text,
                "context": item.context
            }
        elif isinstance(item, Concept):
            return {
                "term": item.concept_name,
                "definition": item.content,
                "context": None
            }
        elif isinstance(item, Formula):
            return {
                "term": "Formula",
                "definition": item.formula_text,
                "context": None
            }
        else:
            return {
                "term": "Unknown",
                "definition": item.content,
                "context": None
            }
    
    def _extract_example_callout_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for EXAMPLE_CALLOUT"""
        
        if isinstance(item, Example):
            return {
                "exemplifies": item.exemplifies,
                "example_text": item.example_text,
                "example_type": item.example_type
            }
        else:
            return {
                "exemplifies": "Unknown",
                "example_text": item.content,
                "example_type": None
            }
    
    def _extract_flowchart_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for FLOWCHART"""
        
        if isinstance(item, Procedure):
            return {
                "steps": item.steps,
                "procedure_name": item.procedure_name
            }
        else:
            # Try to extract steps from content
            text = self._get_item_text(item)
            steps = [s.strip() for s in text.split('\n') if s.strip()]
            return {
                "steps": steps if len(steps) > 1 else [text],
                "procedure_name": None
            }
    
    def _extract_timeline_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for TIMELINE"""
        
        if isinstance(item, Procedure):
            events=[]
            for step in item.steps:
                match=re.search(r'\b(?:\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',step)
                if match:events.append({'time':match.group(),'event':step})
            if len(events)!=len(item.steps):return {}
            return {
                "events": events,
                "title": item.procedure_name
            }
        else:
            # Basic timeline with single event
            text=self._get_item_text(item)
            match=re.search(r'\b\d{4}\b',text)
            return {'events':[{'time':match.group(),'event':text}],'title':None} if match else {}
    
    def _extract_cause_effect_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for CAUSE_EFFECT_DIAGRAM"""
        
        text = self._get_item_text(item)
        
        # Try to parse cause and effect
        cause, effect = self._parse_cause_effect(text)
        
        if isinstance(item, Relationship):
            return {
                "cause": item.subject,
                "effect": item.object,
                "mechanism": item.description
            }
        else:
            # Only use if we successfully extracted cause/effect
            # Otherwise this format shouldn't have been selected
            return {
                "cause": cause if cause else text,
                "effect": effect if effect else "",
                "mechanism": text
            }
    
    def _parse_cause_effect(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Attempt to parse cause and effect from text"""
        
        text_lower = text.lower()
        
        # Try "because X, Y" pattern
        match = re.search(r'because\s+(.+?),\s+(.+)', text_lower, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Try "X causes Y" pattern
        match = re.search(r'(.+?)\s+causes?\s+(.+)', text_lower, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Try "X leads to Y" pattern
        match = re.search(r'(.+?)\s+leads? to\s+(.+)', text_lower, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        return None, None
    
    def _extract_hierarchy_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for HIERARCHY_TREE"""
        
        if isinstance(item, Relationship):
            return {
                "root": item.object,
                "children": [{"name": item.subject, "children": []}]
            }
        else:
            return {
                "root": "Root",
                "children": [{"name": item.content[:50], "children": []}]
            }
    
    def _extract_comparison_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for COMPARISON_TABLE"""
        
        if isinstance(item, Relationship):
            return {
                "items": [item.subject, item.object],
                "dimensions": ["Property"],
                "values": {
                    item.subject: {"Property": "Subject"},
                    item.object: {"Property": "Object"}
                }
            }
        else:
            # Minimal comparison structure
            return {
                "items": ["Item"],
                "dimensions": ["Dimension"],
                "values": {"Item": {"Dimension": self._get_item_text(item)[:100]}}
            }
    
    def _extract_formula_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for FORMULA_DISPLAY"""
        
        if isinstance(item, Formula):
            return {
                "formula": item.formula_text,
                "variables": item.variables,
                "conditions": item.conditions
            }
        else:
            return {
                "formula": item.content,
                "variables": None,
                "conditions": None
            }
    
    def _extract_standard_text_content(self, item: KnowledgeItem) -> Dict[str, Any]:
        """Extract content for STANDARD_TEXT"""
        
        return {
            "content": self._get_item_text(item)
        }
    
    def _print_statistics(self, doc: RepresentationDocument):
        """Print representation statistics"""
        
        stats = doc.statistics
        
        print(f"Items processed: {stats.items_processed}")
        print()
        print("Format distribution:")
        for fmt, count in sorted(stats.format_distribution.items(), key=lambda x: -x[1]):
            print(f"  {fmt.value:25s} {count:3d}")
        
        print()
        print("Confidence distribution:")
        for conf, count in sorted(stats.confidence_distribution.items()):
            print(f"  {conf:15s} {count:3d}")
        
        print()
        print(f"Items with secondary format: {stats.items_with_secondary}")
        print(f"Fallback to standard text: {stats.fallback_count}")
