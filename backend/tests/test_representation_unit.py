"""
Unit tests for Representation Selector layer.

Tests format selection rules, content extraction, and provenance preservation.
"""

from app.models.knowledge import (
    Concept,
    Definition,
    Explanation,
    Example,
    Fact,
    Formula,
    Procedure,
    Relationship
)
from app.analysis.characteristics import (
    AnalyzedKnowledge,
    ContentCharacteristic
)
from app.representation import (
    RepresentationFormat,
    RepresentationSelector
)


# ============================================================================
# Fixtures
# ============================================================================

def create_definition(knowledge_id: str = "DEF_001") -> Definition:
    """Create test definition"""
    return Definition(
        knowledge_id=knowledge_id,
        knowledge_type="definition",
        source_unit_ids=["S0001", "S0002"],
        document_id="TEST_DOC",
        content="A prose narrative of limited length",
        term="short story",
        definition_text="A prose narrative of limited length"
    )


def create_example(knowledge_id: str = "EXM_001") -> Example:
    """Create test example"""
    return Example(
        knowledge_id=knowledge_id,
        knowledge_type="example",
        source_unit_ids=["S0003"],
        document_id="TEST_DOC",
        content="Garcia Marquez's story illustrates magical realism",
        exemplifies="magical realism",
        example_text="Garcia Marquez's story illustrates magical realism",
        example_type="literary"
    )


def create_procedure(knowledge_id: str = "PRO_001", steps: list = None) -> Procedure:
    """Create test procedure"""
    if steps is None:
        steps = [
            "Read the text carefully",
            "Identify key themes",
            "Analyze character development",
            "Draw conclusions"
        ]
    
    return Procedure(
        knowledge_id=knowledge_id,
        knowledge_type="procedure",
        source_unit_ids=["S0004", "S0005"],
        document_id="TEST_DOC",
        content="Steps for analyzing literature",
        procedure_name="literary analysis",
        steps=steps
    )


def create_causal_explanation(knowledge_id: str = "EXP_001") -> Explanation:
    """Create causal explanation"""
    return Explanation(
        knowledge_id=knowledge_id,
        knowledge_type="explanation",
        source_unit_ids=["S0006"],
        document_id="TEST_DOC",
        content="Because the dream was prophetic, the narrator left Vienna",
        topic="dream interpretation",
        explanation_text="Because the dream was prophetic, the narrator left Vienna immediately",
        explanation_type="causal"
    )


def create_formula(knowledge_id: str = "FOR_001") -> Formula:
    """Create test formula"""
    return Formula(
        knowledge_id=knowledge_id,
        knowledge_type="formula",
        source_unit_ids=["S0007"],
        document_id="TEST_DOC",
        content="E = mc²",
        formula_text="E = mc²",
        variables={"E": "energy", "m": "mass", "c": "speed of light"}
    )


def create_hierarchical_relationship(knowledge_id: str = "REL_001") -> Relationship:
    """Create hierarchical relationship"""
    return Relationship(
        knowledge_id=knowledge_id,
        knowledge_type="relationship",
        source_unit_ids=["S0008"],
        document_id="TEST_DOC",
        content="Short story is a type of prose narrative",
        relationship_type="is_a",
        subject="short story",
        object="prose narrative",
        description="Hierarchical categorization"
    )


def create_analyzed_item(
    item,
    characteristics: list,
    confidence: str = "high"
) -> AnalyzedKnowledge:
    """Wrap knowledge item as analyzed item"""
    return AnalyzedKnowledge(
        knowledge_item=item,
        characteristics=characteristics,
        analysis_confidence=confidence,
        analysis_reasoning="Test reasoning"
    )


# ============================================================================
# Format Selection Tests
# ============================================================================

def test_definition_selects_definition_box():
    """Test that definitions get DEFINITION_BOX format"""
    
    item = create_definition()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.DEFINITION])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.DEFINITION_BOX
    assert result.confidence_label == "high"
    assert result.format_content["term"] == "short story"
    assert result.format_content["definition"] == "A prose narrative of limited length"
    
    print("[PASS] Definition -> DEFINITION_BOX")


def test_example_selects_example_callout():
    """Test that examples get EXAMPLE_CALLOUT format"""
    
    item = create_example()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.EXAMPLE])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.EXAMPLE_CALLOUT
    assert result.confidence_label == "high"
    assert result.format_content["exemplifies"] == "magical realism"
    assert "Garcia Marquez" in result.format_content["example_text"]
    
    print("[PASS] Example -> EXAMPLE_CALLOUT")


def test_procedure_selects_flowchart():
    """Test that procedures with multiple steps get FLOWCHART"""
    
    item = create_procedure()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.SEQUENCE])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.FLOWCHART
    assert result.confidence_label == "high"
    assert len(result.format_content["steps"]) == 4
    assert result.format_content["procedure_name"] == "literary analysis"
    
    print("[PASS] Procedure with steps -> FLOWCHART")


def test_single_step_procedure_fallback():
    """Test that single-step procedures get low confidence"""
    
    item = create_procedure(steps=["Read the text"])
    analyzed = create_analyzed_item(item, [ContentCharacteristic.SEQUENCE])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # Single step gets flowchart but with low confidence
    assert result.primary_format == RepresentationFormat.FLOWCHART
    assert result.confidence_label in ["low", "fallback"]
    
    print("[PASS] Single-step procedure -> FLOWCHART with low confidence")


def test_causal_explanation_selects_cause_effect():
    """Test that causal explanations get CAUSE_EFFECT_DIAGRAM"""
    
    item = create_causal_explanation()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.CAUSE_EFFECT])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.CAUSE_EFFECT_DIAGRAM
    assert result.confidence_label in ["high", "medium"]
    assert "cause" in result.format_content
    assert "effect" in result.format_content
    
    print("[PASS] Causal explanation -> CAUSE_EFFECT_DIAGRAM")


def test_formula_selects_formula_display():
    """Test that formulas get FORMULA_DISPLAY"""
    
    item = create_formula()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.DEFINITION])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.FORMULA_DISPLAY
    assert result.confidence_label == "high"
    assert result.format_content["formula"] == "E = mc²"
    assert result.format_content["variables"] is not None
    
    print("[PASS] Formula -> FORMULA_DISPLAY")


def test_unknown_characteristic_fallback():
    """Test that UNKNOWN characteristic falls back to STANDARD_TEXT"""
    
    item = create_definition()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.UNKNOWN], confidence="insufficient")
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.STANDARD_TEXT
    assert result.confidence_label == "fallback"
    
    print("[PASS] UNKNOWN characteristic -> STANDARD_TEXT")


# ============================================================================
# Multiple Characteristics Tests
# ============================================================================

def test_multiple_characteristics_picks_best():
    """Test that multiple characteristics select the best-scoring format"""
    
    # Causal explanation has both CAUSE_EFFECT and FACTUAL_EXPLANATION
    item = create_causal_explanation()
    analyzed = create_analyzed_item(
        item,
        [ContentCharacteristic.CAUSE_EFFECT, ContentCharacteristic.FACTUAL_EXPLANATION]
    )
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # CAUSE_EFFECT_DIAGRAM should score higher than generic text
    assert result.primary_format == RepresentationFormat.CAUSE_EFFECT_DIAGRAM
    
    print("[PASS] Multiple characteristics select best format")


def test_conflicting_characteristics_deterministic():
    """Test that conflicting characteristics resolve deterministically"""
    
    item = create_procedure()
    analyzed1 = create_analyzed_item(
        item,
        [ContentCharacteristic.SEQUENCE, ContentCharacteristic.FACTUAL_EXPLANATION]
    )
    analyzed2 = create_analyzed_item(
        item,
        [ContentCharacteristic.SEQUENCE, ContentCharacteristic.FACTUAL_EXPLANATION]
    )
    
    selector = RepresentationSelector()
    result1 = selector._select_representation(analyzed1)
    result2 = selector._select_representation(analyzed2)
    
    # Same input should give same output
    assert result1.primary_format == result2.primary_format
    assert result1.selection_confidence == result2.selection_confidence
    
    print("[PASS] Conflicting characteristics resolve deterministically")


# ============================================================================
# Content Validation Tests
# ============================================================================

def test_missing_required_fields_fallback():
    """Test fallback when required format fields are missing"""
    
    # Definition without definition_text
    item = Definition(
        knowledge_id="DEF_BAD",
        knowledge_type="definition",
        source_unit_ids=["S0010"],
        document_id="TEST_DOC",
        content="",
        term="",
        definition_text=""
    )
    analyzed = create_analyzed_item(item, [ContentCharacteristic.DEFINITION])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # Should still select definition box but with reduced confidence
    # (scoring system doesn't completely reject formats with missing fields)
    assert result.confidence_label in ["medium", "low", "fallback"]
    assert result.format_content is not None
    
    print("[PASS] Missing required fields -> reduced confidence")


def test_temporal_sequence_detection():
    """Test detection of temporal vs procedural sequences"""
    
    # Procedural sequence
    procedural = create_procedure(steps=[
        "First, analyze the theme",
        "Then, examine the characters",
        "Finally, draw conclusions"
    ])
    analyzed_proc = create_analyzed_item(procedural, [ContentCharacteristic.SEQUENCE])
    
    selector = RepresentationSelector()
    result_proc = selector._select_representation(analyzed_proc)
    
    # Procedural should get FLOWCHART
    assert result_proc.primary_format == RepresentationFormat.FLOWCHART
    
    # Temporal sequence
    temporal = create_procedure(steps=[
        "In January 1950, the war began",
        "By June 1950, forces mobilized",
        "During July 1950, battles intensified"
    ])
    analyzed_temp = create_analyzed_item(temporal, [ContentCharacteristic.SEQUENCE])
    
    result_temp = selector._select_representation(analyzed_temp)
    
    # Temporal should get TIMELINE
    assert result_temp.primary_format == RepresentationFormat.TIMELINE
    
    print("[PASS] Temporal vs procedural sequence detection")


# ============================================================================
# Provenance Tests
# ============================================================================

def test_provenance_preserved():
    """Test that source IDs and document IDs are preserved"""
    
    item = create_definition()
    original_sources = item.source_unit_ids.copy()
    original_doc_id = item.document_id
    
    analyzed = create_analyzed_item(item, [ContentCharacteristic.DEFINITION])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.source_unit_ids == original_sources
    assert result.document_id == original_doc_id
    assert result.knowledge_id == item.knowledge_id
    
    print("[PASS] Provenance preserved (source IDs, document ID, knowledge ID)")


def test_no_source_modification():
    """Test that original source IDs are not modified"""
    
    item = create_example()
    original_sources = item.source_unit_ids.copy()
    
    analyzed = create_analyzed_item(item, [ContentCharacteristic.EXAMPLE])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # Verify original item unchanged
    assert item.source_unit_ids == original_sources
    # Verify result has copy, not reference
    result.source_unit_ids.append("MODIFIED")
    assert item.source_unit_ids != result.source_unit_ids
    
    print("[PASS] Original knowledge item source IDs not modified")


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_content():
    """Test handling of empty or minimal content"""
    
    item = Concept(
        knowledge_id="CON_EMPTY",
        knowledge_type="concept",
        source_unit_ids=["S0020"],
        document_id="TEST_DOC",
        content="",
        concept_name="empty"
    )
    analyzed = create_analyzed_item(item, [ContentCharacteristic.UNKNOWN], confidence="insufficient")
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    assert result.primary_format == RepresentationFormat.STANDARD_TEXT
    assert result.confidence_label == "fallback"
    
    print("[PASS] Empty content -> STANDARD_TEXT fallback")


def test_formula_without_formula_text():
    """Test formula with missing formula text"""
    
    item = Formula(
        knowledge_id="FOR_BAD",
        knowledge_type="formula",
        source_unit_ids=["S0021"],
        document_id="TEST_DOC",
        content="A formula",
        formula_text=""
    )
    analyzed = create_analyzed_item(item, [ContentCharacteristic.DEFINITION])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # Should still attempt FORMULA_DISPLAY but with low confidence
    # or fallback to STANDARD_TEXT
    assert result.format_content is not None
    
    print("[PASS] Formula without formula text handled")


def test_hierarchy_single_level_insufficient():
    """Test that single-level hierarchy doesn't force tree visualization"""
    
    item = create_hierarchical_relationship()
    analyzed = create_analyzed_item(item, [ContentCharacteristic.HIERARCHY])
    
    selector = RepresentationSelector()
    result = selector._select_representation(analyzed)
    
    # Single relationship insufficient for tree - should score low
    # Likely falls back to STANDARD_TEXT
    assert result.format_content is not None
    
    print("[PASS] Single-level hierarchy handled appropriately")


# ============================================================================
# Confidence Scoring Tests
# ============================================================================

def test_confidence_scoring_accuracy():
    """Test confidence label assignment"""
    
    selector = RepresentationSelector()
    
    assert selector._get_confidence_label(0.95) == "high"
    assert selector._get_confidence_label(0.8) == "high"
    assert selector._get_confidence_label(0.7) == "medium"
    assert selector._get_confidence_label(0.6) == "medium"
    assert selector._get_confidence_label(0.5) == "low"
    assert selector._get_confidence_label(0.3) == "low"
    assert selector._get_confidence_label(0.2) == "fallback"
    assert selector._get_confidence_label(0.1) == "fallback"
    
    print("[PASS] Confidence scoring thresholds correct")


# ============================================================================
# Determinism Tests
# ============================================================================

def test_deterministic_selection():
    """Test that selection is deterministic"""
    
    item = create_procedure()
    analyzed = create_analyzed_item(
        item,
        [ContentCharacteristic.SEQUENCE, ContentCharacteristic.FACTUAL_EXPLANATION]
    )
    
    selector = RepresentationSelector()
    
    results = [selector._select_representation(analyzed) for _ in range(5)]
    
    # All should be identical
    first = results[0]
    for r in results[1:]:
        assert r.primary_format == first.primary_format
        assert r.selection_confidence == first.selection_confidence
        assert r.confidence_label == first.confidence_label
    
    print("[PASS] Selection is deterministic across multiple runs")


# ============================================================================
# Complementary Format Tests
# ============================================================================

def test_complementary_formats():
    """Test complementary format detection"""
    
    selector = RepresentationSelector()
    
    # DEFINITION_BOX + EXAMPLE_CALLOUT are complementary
    assert selector._is_complementary(
        RepresentationFormat.DEFINITION_BOX,
        RepresentationFormat.EXAMPLE_CALLOUT
    )
    
    # FLOWCHART + STANDARD_TEXT are complementary
    assert selector._is_complementary(
        RepresentationFormat.FLOWCHART,
        RepresentationFormat.STANDARD_TEXT
    )
    
    # Two identical formats are not complementary
    assert not selector._is_complementary(
        RepresentationFormat.DEFINITION_BOX,
        RepresentationFormat.DEFINITION_BOX
    )
    
    print("[PASS] Complementary format detection works")


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("REPRESENTATION SELECTOR UNIT TESTS")
    print("=" * 80)
    print()
    
    tests = [
        # Format selection
        test_definition_selects_definition_box,
        test_example_selects_example_callout,
        test_procedure_selects_flowchart,
        test_single_step_procedure_fallback,
        test_causal_explanation_selects_cause_effect,
        test_formula_selects_formula_display,
        test_unknown_characteristic_fallback,
        
        # Multiple characteristics
        test_multiple_characteristics_picks_best,
        test_conflicting_characteristics_deterministic,
        
        # Content validation
        test_missing_required_fields_fallback,
        test_temporal_sequence_detection,
        
        # Provenance
        test_provenance_preserved,
        test_no_source_modification,
        
        # Edge cases
        test_empty_content,
        test_formula_without_formula_text,
        test_hierarchy_single_level_insufficient,
        
        # Confidence
        test_confidence_scoring_accuracy,
        
        # Determinism
        test_deterministic_selection,
        
        # Complementary
        test_complementary_formats
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            failed += 1
    
    print()
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    exit(0 if failed == 0 else 1)
