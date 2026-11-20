"""
Unit tests for Content Analysis layer.

Tests rule-based classification of knowledge items into structural characteristics.
"""

from app.models.knowledge import (
    Concept,
    Definition,
    Explanation,
    Example,
    Fact,
    Formula,
    Procedure,
    Relationship,
    KnowledgeDocument
)
from app.analysis import (
    ContentCharacteristic,
    ContentAnalyzer,
    AnalyzedKnowledge
)


# ============================================================================
# Fixtures
# ============================================================================

def create_test_definition() -> Definition:
    """Create test definition"""
    return Definition(
        knowledge_id="DEF_001",
        knowledge_type="definition",
        source_unit_ids=["S0001"],
        document_id="TEST",
        content="A prose narrative of limited length",
        term="short story",
        definition_text="A prose narrative of limited length"
    )


def create_test_example() -> Example:
    """Create test example"""
    return Example(
        knowledge_id="EXM_001",
        knowledge_type="example",
        source_unit_ids=["S0002"],
        document_id="TEST",
        content="Garcia Marquez's story illustrates magical realism",
        exemplifies="magical realism",
        example_text="Garcia Marquez's story illustrates magical realism"
    )


def create_test_procedure() -> Procedure:
    """Create test procedure"""
    return Procedure(
        knowledge_id="PRC_001",
        knowledge_type="procedure",
        source_unit_ids=["S0003"],
        document_id="TEST",
        content="Steps to analyze a story",
        procedure_name="story analysis",
        steps=["Read the story", "Identify themes", "Analyze characters"]
    )


def create_test_relationship(rel_type: str) -> Relationship:
    """Create test relationship"""
    return Relationship(
        knowledge_id="REL_001",
        knowledge_type="relationship",
        source_unit_ids=["S0004"],
        document_id="TEST",
        content=f"{rel_type} relationship",
        relationship_type=rel_type,
        subject="A",
        object="B"
    )


def create_test_explanation(exp_type: str = None, text: str = "This explains something") -> Explanation:
    """Create test explanation"""
    return Explanation(
        knowledge_id="EXP_001",
        knowledge_type="explanation",
        source_unit_ids=["S0005"],
        document_id="TEST",
        content=text,
        topic="test topic",
        explanation_text=text,
        explanation_type=exp_type
    )


def create_test_concept(aliases: list = None, content: str = "A concept") -> Concept:
    """Create test concept"""
    return Concept(
        knowledge_id="CON_001",
        knowledge_type="concept",
        source_unit_ids=["S0006"],
        document_id="TEST",
        content=content,
        concept_name="test concept",
        aliases=aliases or []
    )


def create_test_fact(fact_type: str = None) -> Fact:
    """Create test fact"""
    return Fact(
        knowledge_id="FCT_001",
        knowledge_type="fact",
        source_unit_ids=["S0007"],
        document_id="TEST",
        content="A factual statement",
        fact_text="A factual statement",
        fact_type=fact_type
    )


# ============================================================================
# Test: Type-Based Classification (High Confidence)
# ============================================================================

def test_definition_gets_DEFINITION():
    """Test that definitions are classified as DEFINITION"""
    item = create_test_definition()
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.DEFINITION in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"
    assert "definition" in analyzed.analysis_reasoning.lower()


def test_example_gets_EXAMPLE():
    """Test that examples are classified as EXAMPLE"""
    item = create_test_example()
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.EXAMPLE in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_procedure_gets_SEQUENCE():
    """Test that procedures are classified as SEQUENCE"""
    item = create_test_procedure()
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.SEQUENCE in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_procedure_gets_multiple_characteristics():
    """Test that multi-step procedures get both SEQUENCE and FACTUAL_EXPLANATION"""
    item = create_test_procedure()
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.SEQUENCE in analyzed.characteristics
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert len(analyzed.characteristics) == 2


def test_relationship_hierarchy_gets_HIERARCHY():
    """Test that is_a relationships get HIERARCHY"""
    item = create_test_relationship("is_a")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.HIERARCHY in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_relationship_causes_gets_CAUSE_EFFECT():
    """Test that causes relationships get CAUSE_EFFECT"""
    item = create_test_relationship("causes")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.CAUSE_EFFECT in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_relationship_contrasts_gets_COMPARISON():
    """Test that contrasts_with relationships get COMPARISON"""
    item = create_test_relationship("contrasts_with")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.COMPARISON in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


# ============================================================================
# Test: Content-Based Classification (Medium Confidence)
# ============================================================================

def test_causal_explanation_gets_CAUSE_EFFECT():
    """Test that causal explanations get CAUSE_EFFECT"""
    item = create_test_explanation(exp_type="causal")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.CAUSE_EFFECT in analyzed.characteristics
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_procedural_explanation_gets_SEQUENCE():
    """Test that procedural explanations get SEQUENCE"""
    item = create_test_explanation(exp_type="procedural")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.SEQUENCE in analyzed.characteristics
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics


def test_functional_explanation_gets_FACTUAL_EXPLANATION():
    """Test that functional explanations get FACTUAL_EXPLANATION"""
    item = create_test_explanation(exp_type="functional")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert analyzed.analysis_confidence == "high"


def test_explanation_with_cause_keywords():
    """Test that explanations with cause keywords get CAUSE_EFFECT"""
    item = create_test_explanation(text="The dream caused him to leave because of the warning")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.CAUSE_EFFECT in analyzed.characteristics
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics


def test_explanation_with_sequence_keywords():
    """Test that explanations with sequence keywords get SEQUENCE"""
    item = create_test_explanation(text="First, analyze the text. Then, identify themes. Finally, write conclusions")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.SEQUENCE in analyzed.characteristics


def test_explanation_with_comparison_keywords():
    """Test that explanations with comparison keywords get COMPARISON"""
    item = create_test_explanation(text="Unlike prose, poetry uses verse. In contrast, drama uses dialogue")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.COMPARISON in analyzed.characteristics


def test_concept_with_aliases_gets_DEFINITION():
    """Test that concepts with aliases are treated as implicit definitions"""
    item = create_test_concept(aliases=["synonym1", "synonym2"])
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.DEFINITION in analyzed.characteristics
    assert analyzed.analysis_confidence == "medium"


def test_fact_gets_FACTUAL_EXPLANATION():
    """Test that facts get FACTUAL_EXPLANATION"""
    item = create_test_fact()
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert analyzed.analysis_confidence == "medium"


def test_statistical_fact_gets_COMPARISON():
    """Test that statistical facts may get COMPARISON"""
    item = create_test_fact(fact_type="statistical")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert ContentCharacteristic.COMPARISON in analyzed.characteristics


# ============================================================================
# Test: Ambiguous Cases and Insufficient Evidence
# ============================================================================

def test_concept_without_aliases_gets_UNKNOWN():
    """Test that minimal concepts without aliases get UNKNOWN"""
    item = create_test_concept(aliases=[], content="X")  # Very short
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.UNKNOWN in analyzed.characteristics
    assert analyzed.analysis_confidence == "insufficient"


def test_concept_with_short_content_insufficient():
    """Test that concepts with short content are marked insufficient"""
    item = create_test_concept(content="Brief")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert analyzed.analysis_confidence == "insufficient"


def test_explanation_without_type_or_keywords():
    """Test that plain explanations default to FACTUAL_EXPLANATION"""
    item = create_test_explanation(exp_type=None, text="This describes something")
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert ContentCharacteristic.FACTUAL_EXPLANATION in analyzed.characteristics
    assert analyzed.analysis_confidence == "medium"


# ============================================================================
# Test: Provenance Preservation
# ============================================================================

def test_source_ids_preserved():
    """Test that source_unit_ids are preserved in analyzed knowledge"""
    item = create_test_definition()
    item.source_unit_ids = ["S0001", "S0002", "S0003"]
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert analyzed.source_unit_ids == ["S0001", "S0002", "S0003"]
    assert analyzed.knowledge_item.source_unit_ids == item.source_unit_ids


def test_document_id_preserved():
    """Test that document_id is preserved"""
    item = create_test_definition()
    item.document_id = "DOC_123"
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    assert analyzed.document_id == "DOC_123"


def test_original_item_unchanged():
    """Test that original knowledge item is not modified"""
    item = create_test_definition()
    original_content = item.content
    original_term = item.term
    analyzer = ContentAnalyzer(verbose=False)
    
    analyzed = analyzer._analyze_item(item)
    
    # Original item preserved
    assert analyzed.knowledge_item.content == original_content
    assert analyzed.knowledge_item.term == original_term
    
    # Wraps the original, doesn't copy
    assert analyzed.knowledge_item is item


# ============================================================================
# Test: Full Document Analysis
# ============================================================================

def test_analyze_full_document():
    """Test analyzing a complete knowledge document"""
    from datetime import datetime
    
    # Create knowledge document with consistent IDs
    concept = create_test_concept(aliases=["alias1"])
    concept.document_id = "TEST_DOC"
    
    definition = create_test_definition()
    definition.document_id = "TEST_DOC"
    
    explanation = create_test_explanation(exp_type="causal")
    explanation.document_id = "TEST_DOC"
    
    example = create_test_example()
    example.document_id = "TEST_DOC"
    
    fact = create_test_fact()
    fact.document_id = "TEST_DOC"
    
    procedure = create_test_procedure()
    procedure.document_id = "TEST_DOC"
    
    relationship = create_test_relationship("is_a")
    relationship.document_id = "TEST_DOC"
    
    knowledge_doc = KnowledgeDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        concepts=[concept],
        definitions=[definition],
        explanations=[explanation],
        examples=[example],
        facts=[fact],
        procedures=[procedure],
        relationships=[relationship],
        source_units_processed=10
    )
    knowledge_doc.update_statistics()
    
    analyzer = ContentAnalyzer(verbose=False)
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    # Check all items analyzed
    assert len(analyzed_doc.analyzed_items) == 7
    
    # Check provenance preserved
    for analyzed_item in analyzed_doc.analyzed_items:
        assert analyzed_item.document_id == "TEST_DOC"
        assert len(analyzed_item.source_unit_ids) > 0
    
    # Check statistics updated
    assert analyzed_doc.statistics.items_analyzed == 7
    assert analyzed_doc.statistics.items_analyzed == len(analyzed_doc.analyzed_items)


def test_statistics_calculated_correctly():
    """Test that statistics are calculated correctly"""
    from datetime import datetime
    
    knowledge_doc = KnowledgeDocument(
        document_id="TEST",
        source_filename="test.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        definitions=[create_test_definition(), create_test_definition()],
        examples=[create_test_example()],
        concepts=[create_test_concept(content="X")],  # Will be UNKNOWN
        source_units_processed=5
    )
    knowledge_doc.update_statistics()
    
    analyzer = ContentAnalyzer(verbose=False)
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    stats = analyzed_doc.statistics
    
    # Should have 2 DEFINITION, 1 EXAMPLE, 1 UNKNOWN
    assert stats.characteristics_distribution[ContentCharacteristic.DEFINITION] == 2
    assert stats.characteristics_distribution[ContentCharacteristic.EXAMPLE] == 1
    assert stats.characteristics_distribution.get(ContentCharacteristic.UNKNOWN, 0) >= 1
    assert stats.unknown_count >= 1


# ============================================================================
# Test: Edge Cases
# ============================================================================

def test_empty_knowledge_document():
    """Test analyzing an empty knowledge document"""
    from datetime import datetime
    
    knowledge_doc = KnowledgeDocument(
        document_id="EMPTY",
        source_filename="empty.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        source_units_processed=0
    )
    
    analyzer = ContentAnalyzer(verbose=False)
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    assert len(analyzed_doc.analyzed_items) == 0
    assert analyzed_doc.statistics.items_analyzed == 0


def test_multiple_relationships_same_document():
    """Test document with multiple relationship types"""
    from datetime import datetime
    
    knowledge_doc = KnowledgeDocument(
        document_id="TEST",
        source_filename="test.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        relationships=[
            create_test_relationship("is_a"),
            create_test_relationship("causes"),
            create_test_relationship("contrasts_with"),
        ],
        source_units_processed=3
    )
    knowledge_doc.update_statistics()
    
    analyzer = ContentAnalyzer(verbose=False)
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    # Check all relationships classified
    assert len(analyzed_doc.analyzed_items) == 3
    
    # Check different characteristics assigned
    all_chars = set()
    for item in analyzed_doc.analyzed_items:
        all_chars.update(item.characteristics)
    
    assert ContentCharacteristic.HIERARCHY in all_chars
    assert ContentCharacteristic.CAUSE_EFFECT in all_chars
    assert ContentCharacteristic.COMPARISON in all_chars


# ============================================================================
# Test: Regression - No Items Lost
# ============================================================================

def test_all_items_analyzed_no_loss():
    """Regression test: ensure no items are lost during analysis"""
    from datetime import datetime
    
    knowledge_doc = KnowledgeDocument(
        document_id="REGRESSION",
        source_filename="regression.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        concepts=[create_test_concept() for _ in range(3)],
        definitions=[create_test_definition() for _ in range(2)],
        explanations=[create_test_explanation() for _ in range(4)],
        examples=[create_test_example() for _ in range(1)],
        facts=[create_test_fact() for _ in range(2)],
        source_units_processed=12
    )
    knowledge_doc.update_statistics()
    
    original_count = knowledge_doc.total_items
    
    analyzer = ContentAnalyzer(verbose=False)
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    # No items lost
    assert len(analyzed_doc.analyzed_items) == original_count
    assert analyzed_doc.statistics.items_analyzed == original_count


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    print("Running content analysis unit tests...")
    print("=" * 80)
    
    # Collect all test functions
    test_functions = [
        # Type-based classification
        test_definition_gets_DEFINITION,
        test_example_gets_EXAMPLE,
        test_procedure_gets_SEQUENCE,
        test_procedure_gets_multiple_characteristics,
        test_relationship_hierarchy_gets_HIERARCHY,
        test_relationship_causes_gets_CAUSE_EFFECT,
        test_relationship_contrasts_gets_COMPARISON,
        
        # Content-based classification
        test_causal_explanation_gets_CAUSE_EFFECT,
        test_procedural_explanation_gets_SEQUENCE,
        test_functional_explanation_gets_FACTUAL_EXPLANATION,
        test_explanation_with_cause_keywords,
        test_explanation_with_sequence_keywords,
        test_explanation_with_comparison_keywords,
        test_concept_with_aliases_gets_DEFINITION,
        test_fact_gets_FACTUAL_EXPLANATION,
        test_statistical_fact_gets_COMPARISON,
        
        # Ambiguous cases
        test_concept_without_aliases_gets_UNKNOWN,
        test_concept_with_short_content_insufficient,
        test_explanation_without_type_or_keywords,
        
        # Provenance preservation
        test_source_ids_preserved,
        test_document_id_preserved,
        test_original_item_unchanged,
        
        # Full document
        test_analyze_full_document,
        test_statistics_calculated_correctly,
        
        # Edge cases
        test_empty_knowledge_document,
        test_multiple_relationships_same_document,
        
        # Regression
        test_all_items_analyzed_no_loss,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"[PASS] {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {str(e) or '(assertion failed)'}")
            failed += 1
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n[SUCCESS] All content analysis tests passed!")
    else:
        print(f"\n[FAILURE] {failed} test(s) failed")
        exit(1)
