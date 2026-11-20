"""
Serialization/Deserialization tests for knowledge models.

Tests JSON round-trip for all knowledge item types and analyzed knowledge.
"""

import json
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
from app.analysis.characteristics import (
    AnalyzedKnowledge,
    AnalyzedKnowledgeDocument,
    ContentCharacteristic
)


def test_concept_round_trip():
    """Test Concept can survive JSON round-trip"""
    
    original = Concept(
        knowledge_id="CON_001",
        knowledge_type="concept",
        source_unit_ids=["S001", "S002"],
        document_id="TEST_DOC",
        content="A prose narrative of limited length",
        concept_name="short story",
        aliases=["tale", "narrative"]
    )
    
    # Serialize
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify all fields present in JSON
    assert json_dict["knowledge_type"] == "concept"
    assert json_dict["concept_name"] == "short story"
    assert json_dict["aliases"] == ["tale", "narrative"]
    assert json_dict["source_unit_ids"] == ["S001", "S002"]
    
    # Deserialize
    restored = Concept.model_validate_json(json_str)
    
    # Verify all fields match
    assert restored.knowledge_id == original.knowledge_id
    assert restored.concept_name == original.concept_name
    assert restored.aliases == original.aliases
    assert restored.source_unit_ids == original.source_unit_ids
    
    print("[PASS] Concept round-trip")


def test_definition_round_trip():
    """Test Definition can survive JSON round-trip"""
    
    original = Definition(
        knowledge_id="DEF_001",
        knowledge_type="definition",
        source_unit_ids=["S003"],
        document_id="TEST_DOC",
        content="A prose narrative of limited length",
        term="short story",
        definition_text="A prose narrative of limited length",
        context="in literature"
    )
    
    # Serialize
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify subclass fields
    assert json_dict["term"] == "short story"
    assert json_dict["definition_text"] == "A prose narrative of limited length"
    assert json_dict["context"] == "in literature"
    
    # Deserialize
    restored = Definition.model_validate_json(json_str)
    
    # Verify all fields match
    assert restored.term == original.term
    assert restored.definition_text == original.definition_text
    assert restored.context == original.context
    
    print("[PASS] Definition round-trip")


def test_explanation_round_trip():
    """Test Explanation can survive JSON round-trip"""
    
    original = Explanation(
        knowledge_id="EXP_001",
        knowledge_type="explanation",
        source_unit_ids=["S004", "S005"],
        document_id="TEST_DOC",
        content="The dream caused the narrator to leave",
        topic="prophetic dreams",
        explanation_text="Because the dream was prophetic, the narrator left Vienna",
        explanation_type="causal"
    )
    
    # Serialize and deserialize
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify subclass fields
    assert json_dict["topic"] == "prophetic dreams"
    assert json_dict["explanation_text"] == "Because the dream was prophetic, the narrator left Vienna"
    assert json_dict["explanation_type"] == "causal"
    
    restored = Explanation.model_validate_json(json_str)
    
    assert restored.topic == original.topic
    assert restored.explanation_text == original.explanation_text
    assert restored.explanation_type == original.explanation_type
    
    print("[PASS] Explanation round-trip")


def test_example_round_trip():
    """Test Example can survive JSON round-trip"""
    
    original = Example(
        knowledge_id="EXM_001",
        knowledge_type="example",
        source_unit_ids=["S006"],
        document_id="TEST_DOC",
        content="Garcia Marquez illustrates magical realism",
        exemplifies="magical realism",
        example_text="Garcia Marquez illustrates magical realism in his stories",
        example_type="literary"
    )
    
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    assert json_dict["exemplifies"] == "magical realism"
    assert json_dict["example_text"] == "Garcia Marquez illustrates magical realism in his stories"
    assert json_dict["example_type"] == "literary"
    
    restored = Example.model_validate_json(json_str)
    
    assert restored.exemplifies == original.exemplifies
    assert restored.example_text == original.example_text
    assert restored.example_type == original.example_type
    
    print("[PASS] Example round-trip")


def test_fact_round_trip():
    """Test Fact can survive JSON round-trip"""
    
    original = Fact(
        knowledge_id="FCT_001",
        knowledge_type="fact",
        source_unit_ids=["S007"],
        document_id="TEST_DOC",
        content="Pablo Neruda was a Chilean poet",
        fact_text="Pablo Neruda was a Chilean poet",
        fact_type="biographical"
    )
    
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    assert json_dict["fact_text"] == "Pablo Neruda was a Chilean poet"
    assert json_dict["fact_type"] == "biographical"
    
    restored = Fact.model_validate_json(json_str)
    
    assert restored.fact_text == original.fact_text
    assert restored.fact_type == original.fact_type
    
    print("[PASS] Fact round-trip")


def test_formula_round_trip():
    """Test Formula can survive JSON round-trip"""
    
    original = Formula(
        knowledge_id="FOR_001",
        knowledge_type="formula",
        source_unit_ids=["S008"],
        document_id="TEST_DOC",
        content="E = mc²",
        formula_text="E = mc²",
        variables={"E": "energy", "m": "mass", "c": "speed of light"},
        conditions="in relativity",
        derivation="Einstein's derivation"
    )
    
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    assert json_dict["formula_text"] == "E = mc²"
    assert json_dict["variables"]["E"] == "energy"
    assert json_dict["conditions"] == "in relativity"
    assert json_dict["derivation"] == "Einstein's derivation"
    
    restored = Formula.model_validate_json(json_str)
    
    assert restored.formula_text == original.formula_text
    assert restored.variables == original.variables
    assert restored.conditions == original.conditions
    assert restored.derivation == original.derivation
    
    print("[PASS] Formula round-trip")


def test_procedure_round_trip():
    """Test Procedure can survive JSON round-trip"""
    
    original = Procedure(
        knowledge_id="PRO_001",
        knowledge_type="procedure",
        source_unit_ids=["S009", "S010"],
        document_id="TEST_DOC",
        content="Steps for literary analysis",
        procedure_name="literary analysis",
        steps=["Read the text", "Identify themes", "Analyze characters"],
        prerequisites=["basic reading skills"],
        outcomes="understanding of literature"
    )
    
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    assert json_dict["procedure_name"] == "literary analysis"
    assert len(json_dict["steps"]) == 3
    assert json_dict["steps"][0] == "Read the text"
    assert json_dict["prerequisites"] == ["basic reading skills"]
    assert json_dict["outcomes"] == "understanding of literature"
    
    restored = Procedure.model_validate_json(json_str)
    
    assert restored.procedure_name == original.procedure_name
    assert restored.steps == original.steps
    assert restored.prerequisites == original.prerequisites
    assert restored.outcomes == original.outcomes
    
    print("[PASS] Procedure round-trip")


def test_relationship_round_trip():
    """Test Relationship can survive JSON round-trip"""
    
    original = Relationship(
        knowledge_id="REL_001",
        knowledge_type="relationship",
        source_unit_ids=["S011"],
        document_id="TEST_DOC",
        content="Short story is a type of prose narrative",
        relationship_type="is_a",
        subject="short story",
        object="prose narrative",
        description="Hierarchical categorization"
    )
    
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    assert json_dict["relationship_type"] == "is_a"
    assert json_dict["subject"] == "short story"
    assert json_dict["object"] == "prose narrative"
    assert json_dict["description"] == "Hierarchical categorization"
    
    restored = Relationship.model_validate_json(json_str)
    
    assert restored.relationship_type == original.relationship_type
    assert restored.subject == original.subject
    assert restored.object == original.object
    assert restored.description == original.description
    
    print("[PASS] Relationship round-trip")


def test_analyzed_knowledge_round_trip():
    """Test AnalyzedKnowledge can survive JSON round-trip with subclass fields"""
    
    # Create a Concept (subclass)
    concept = Concept(
        knowledge_id="CON_002",
        knowledge_type="concept",
        source_unit_ids=["S020"],
        document_id="TEST_DOC",
        content="A narrative technique",
        concept_name="magical realism",
        aliases=["magic realism"]
    )
    
    # Wrap in AnalyzedKnowledge
    original = AnalyzedKnowledge(
        knowledge_item=concept,
        characteristics=[ContentCharacteristic.DEFINITION],
        analysis_confidence="high",
        analysis_reasoning="Concept with aliases implies definition"
    )
    
    # Serialize
    json_str = original.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify subclass fields are preserved in JSON
    assert json_dict["knowledge_item"]["knowledge_type"] == "concept"
    assert json_dict["knowledge_item"]["concept_name"] == "magical realism"
    assert json_dict["knowledge_item"]["aliases"] == ["magic realism"]
    assert json_dict["knowledge_item"]["source_unit_ids"] == ["S020"]
    
    # Deserialize
    restored = AnalyzedKnowledge.model_validate_json(json_str)
    
    # Verify it's still the correct type
    assert isinstance(restored.knowledge_item, Concept)
    assert restored.knowledge_item.concept_name == concept.concept_name
    assert restored.knowledge_item.aliases == concept.aliases
    assert restored.characteristics == [ContentCharacteristic.DEFINITION]
    
    print("[PASS] AnalyzedKnowledge round-trip with subclass fields")


def test_analyzed_knowledge_document_round_trip():
    """Test full AnalyzedKnowledgeDocument round-trip"""
    
    # Create various knowledge items
    concept = Concept(
        knowledge_id="CON_003",
        knowledge_type="concept",
        source_unit_ids=["S030"],
        document_id="TEST_DOC",
        content="Dream interpretation",
        concept_name="dream interpretation",
        aliases=["oneiromancy"]
    )
    
    definition = Definition(
        knowledge_id="DEF_002",
        knowledge_type="definition",
        source_unit_ids=["S031"],
        document_id="TEST_DOC",
        content="A predictive dream",
        term="prophetic dream",
        definition_text="A dream that predicts the future"
    )
    
    # Create analyzed items
    analyzed_concept = AnalyzedKnowledge(
        knowledge_item=concept,
        characteristics=[ContentCharacteristic.DEFINITION],
        analysis_confidence="high",
        analysis_reasoning="Concept with aliases"
    )
    
    analyzed_def = AnalyzedKnowledge(
        knowledge_item=definition,
        characteristics=[ContentCharacteristic.DEFINITION],
        analysis_confidence="high",
        analysis_reasoning="Explicit definition"
    )
    
    # Create document
    original_doc = AnalyzedKnowledgeDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        analysis_timestamp="2026-10-19T12:00:00",
        extraction_timestamp="2026-10-19T11:00:00",
        source_units_processed=109,
        analyzed_items=[analyzed_concept, analyzed_def]
    )
    original_doc.update_statistics()
    
    # Serialize
    json_str = original_doc.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify structure
    assert len(json_dict["analyzed_items"]) == 2
    assert json_dict["analyzed_items"][0]["knowledge_item"]["concept_name"] == "dream interpretation"
    assert json_dict["analyzed_items"][1]["knowledge_item"]["term"] == "prophetic dream"
    assert json_dict["analyzed_items"][1]["knowledge_item"]["definition_text"] == "A dream that predicts the future"
    
    # Deserialize
    restored_doc = AnalyzedKnowledgeDocument.model_validate_json(json_str)
    
    # Verify all items preserved with correct types
    assert len(restored_doc.analyzed_items) == 2
    assert isinstance(restored_doc.analyzed_items[0].knowledge_item, Concept)
    assert isinstance(restored_doc.analyzed_items[1].knowledge_item, Definition)
    assert restored_doc.analyzed_items[0].knowledge_item.concept_name == "dream interpretation"
    assert restored_doc.analyzed_items[1].knowledge_item.term == "prophetic dream"
    
    print("[PASS] AnalyzedKnowledgeDocument full round-trip")


def test_knowledge_document_round_trip():
    """Test KnowledgeDocument with all item types"""
    
    doc = KnowledgeDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        extraction_timestamp="2026-10-19T12:00:00",
        source_units_processed=100
    )
    
    # Add one of each type
    doc.concepts.append(Concept(
        knowledge_id="CON_999",
        knowledge_type="concept",
        source_unit_ids=["S100"],
        document_id="TEST_DOC",
        content="Test concept",
        concept_name="test",
        aliases=["example"]
    ))
    
    doc.definitions.append(Definition(
        knowledge_id="DEF_999",
        knowledge_type="definition",
        source_unit_ids=["S101"],
        document_id="TEST_DOC",
        content="Test definition",
        term="test term",
        definition_text="test definition text"
    ))
    
    doc.update_statistics()
    
    # Serialize
    json_str = doc.model_dump_json()
    json_dict = json.loads(json_str)
    
    # Verify
    assert len(json_dict["concepts"]) == 1
    assert json_dict["concepts"][0]["concept_name"] == "test"
    assert len(json_dict["definitions"]) == 1
    assert json_dict["definitions"][0]["term"] == "test term"
    
    # Deserialize
    restored = KnowledgeDocument.model_validate_json(json_str)
    
    assert len(restored.concepts) == 1
    assert restored.concepts[0].concept_name == "test"
    assert len(restored.definitions) == 1
    assert restored.definitions[0].term == "test term"
    
    print("[PASS] KnowledgeDocument round-trip")


if __name__ == "__main__":
    print("=" * 80)
    print("SERIALIZATION ROUND-TRIP TESTS")
    print("=" * 80)
    print()
    
    tests = [
        test_concept_round_trip,
        test_definition_round_trip,
        test_explanation_round_trip,
        test_example_round_trip,
        test_fact_round_trip,
        test_formula_round_trip,
        test_procedure_round_trip,
        test_relationship_round_trip,
        test_analyzed_knowledge_round_trip,
        test_analyzed_knowledge_document_round_trip,
        test_knowledge_document_round_trip
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
