"""
Representation format definitions.

Defines the available output formats for knowledge representation.
"""

from enum import Enum


class RepresentationFormat(str, Enum):
    """
    Visual/textual representation formats for knowledge items.
    
    These are output format specifications - they describe HOW to present
    information, not what the information is. Actual rendering happens in
    a later layer (Note Assembler).
    """
    
    # Default text format
    STANDARD_TEXT = "standard_text"
    
    # Structured formats
    DEFINITION_BOX = "definition_box"
    COMPARISON_TABLE = "comparison_table"
    FLOWCHART = "flowchart"
    TIMELINE = "timeline"
    CAUSE_EFFECT_DIAGRAM = "cause_effect_diagram"
    HIERARCHY_TREE = "hierarchy_tree"
    EXAMPLE_CALLOUT = "example_callout"
    FORMULA_DISPLAY = "formula_display"
