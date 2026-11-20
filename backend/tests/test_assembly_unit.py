"""
Unit tests for Note Assembler layer.

Tests section organization, ordering, provenance preservation, and edge cases.
"""

from app.representation.models import RepresentationDocument, SelectedRepresentation
from app.representation.formats import RepresentationFormat
from app.assembly import NoteAssembler


# ============================================================================
# Fixtures
# ============================================================================

def create_test_representation(
    knowledge_id: str,
    source_ids: list,
    primary_format: RepresentationFormat = RepresentationFormat.STANDARD_TEXT
) -> SelectedRepresentation:
    """Create a test representation"""
    return SelectedRepresentation(
        knowledge_id=knowledge_id,
        document_id="TEST_DOC",
        knowledge_type="concept",
        source_unit_ids=source_ids,
        primary_format=primary_format,
        format_content={"content": f"Content for {knowledge_id}"},
        selection_confidence=0.8,
        confidence_label="high",
        selection_reasoning="Test reasoning"
    )


def create_test_rep_doc(representations: list) -> RepresentationDocument:
    """Create a test representation document"""
    return RepresentationDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        representation_timestamp="2026-10-19T12:00:00",
        analysis_timestamp="2026-10-19T11:00:00",
        extraction_timestamp="2026-10-19T10:00:00",
        source_units_processed=100,
        representations=representations
    )


# ============================================================================
# Basic Assembly Tests
# ============================================================================

def test_normal_assembly():
    """Test normal assembly with multiple items"""
    
    reps = [
        create_test_representation("CON_001", ["S0001"]),
        create_test_representation("DEF_002", ["S0002"]),
        create_test_representation("EXP_003", ["S0003"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Verify basic structure
    assert result.document_id == "TEST_DOC"
    assert result.statistics.total_items == 3
    assert result.statistics.total_sections >= 1
    
    # Verify all items present
    all_items = []
    for section in result.sections:
        all_items.extend(section.items)
    
    assert len(all_items) == 3
    
    # Verify provenance preserved
    assert all_items[0].knowledge_id in ["CON_001", "DEF_002", "EXP_003"]
    assert all_items[0].document_id == "TEST_DOC"
    assert len(all_items[0].source_unit_ids) > 0
    
    print("[PASS] Normal assembly")


def test_empty_input():
    """Test assembly with no representations"""
    
    rep_doc = create_test_rep_doc([])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Should return valid document with 0 items
    assert result.statistics.total_items == 0
    assert result.statistics.total_sections == 0
    assert len(result.sections) == 0
    assert result.metadata.ordering_strategy == "none"
    
    print("[PASS] Empty input handled")


def test_single_item():
    """Test assembly with single item"""
    
    rep = create_test_representation("CON_001", ["S0001"])
    rep_doc = create_test_rep_doc([rep])
    
    assembler = NoteAssembler()
    result = assembler.assemble(rep_doc)
    
    assert result.statistics.total_items == 1
    assert result.statistics.total_sections == 1
    assert len(result.sections[0].items) == 1
    
    print("[PASS] Single item assembly")


# ============================================================================
# Ordering Tests
# ============================================================================

def test_source_order_maintained():
    """Test that source unit order is maintained"""
    
    # Create items with non-sequential source IDs
    reps = [
        create_test_representation("CON_003", ["S0030"]),
        create_test_representation("CON_001", ["S0010"]),
        create_test_representation("CON_002", ["S0020"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Verify items are ordered by source_unit_id
    items = result.sections[0].items
    assert items[0].knowledge_id == "CON_001"  # S0010
    assert items[1].knowledge_id == "CON_002"  # S0020
    assert items[2].knowledge_id == "CON_003"  # S0030
    
    print("[PASS] Source order maintained")


def test_deterministic_ordering():
    """Test that ordering is deterministic"""
    
    reps = [
        create_test_representation("CON_003", ["S0030"]),
        create_test_representation("CON_001", ["S0010"]),
        create_test_representation("CON_002", ["S0020"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result1 = assembler.assemble(rep_doc)
    result2 = assembler.assemble(rep_doc)
    
    # Results should be identical
    ids1 = [item.knowledge_id for section in result1.sections for item in section.items]
    ids2 = [item.knowledge_id for section in result2.sections for item in section.items]
    
    assert ids1 == ids2
    
    print("[PASS] Deterministic ordering")


def test_id_based_fallback():
    """Test fallback to ID-based ordering when source IDs missing"""
    
    reps = [
        create_test_representation("DEF_003", []),  # No source IDs
        create_test_representation("CON_001", []),
        create_test_representation("CON_002", [])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Should fallback to knowledge_id ordering
    items = result.sections[0].items
    assert items[0].knowledge_id == "CON_001"
    assert items[1].knowledge_id == "CON_002"
    assert items[2].knowledge_id == "DEF_003"
    assert items[0].ordering_rationale == "id-based"
    
    print("[PASS] ID-based fallback ordering")


def test_position_in_section():
    """Test that position_in_section is correctly assigned"""
    
    reps = [
        create_test_representation("CON_001", ["S0001"]),
        create_test_representation("CON_002", ["S0002"]),
        create_test_representation("CON_003", ["S0003"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    items = result.sections[0].items
    assert items[0].position_in_section == 0
    assert items[1].position_in_section == 1
    assert items[2].position_in_section == 2
    
    print("[PASS] Position in section assigned correctly")


# ============================================================================
# Provenance Preservation Tests
# ============================================================================

def test_provenance_preserved():
    """Test that all provenance fields are preserved"""
    
    rep = create_test_representation("CON_001", ["S0001", "S0002"])
    rep.selection_confidence = 0.95
    rep.confidence_label = "high"
    rep.selection_reasoning = "Test reasoning for preservation"
    
    rep_doc = create_test_rep_doc([rep])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    item = result.sections[0].items[0]
    
    # Verify all fields preserved
    assert item.knowledge_id == "CON_001"
    assert item.document_id == "TEST_DOC"
    assert item.source_unit_ids == ["S0001", "S0002"]
    assert item.selection_confidence == 0.95
    assert item.confidence_label == "high"
    assert item.selection_reasoning == "Test reasoning for preservation"
    
    print("[PASS] Provenance preserved")


def test_format_content_preserved():
    """Test that format_content is not modified"""
    
    rep = create_test_representation("DEF_001", ["S0001"])
    rep.primary_format = RepresentationFormat.DEFINITION_BOX
    rep.format_content = {
        "term": "test term",
        "definition": "test definition",
        "context": "test context"
    }
    
    rep_doc = create_test_rep_doc([rep])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    item = result.sections[0].items[0]
    
    # Verify format content exactly matches
    assert item.format_content["term"] == "test term"
    assert item.format_content["definition"] == "test definition"
    assert item.format_content["context"] == "test context"
    
    # Verify it's a copy (not reference)
    assert item.format_content is not rep.format_content
    
    print("[PASS] Format content preserved")


def test_secondary_format_preserved():
    """Test that secondary format is preserved when present"""
    
    rep = create_test_representation("CON_001", ["S0001"])
    rep.secondary_format = RepresentationFormat.EXAMPLE_CALLOUT
    rep.secondary_content = {"exemplifies": "test", "example_text": "example"}
    
    rep_doc = create_test_rep_doc([rep])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    item = result.sections[0].items[0]
    
    assert item.secondary_format == RepresentationFormat.EXAMPLE_CALLOUT
    assert item.secondary_content is not None
    assert item.secondary_content["exemplifies"] == "test"
    
    print("[PASS] Secondary format preserved")


# ============================================================================
# Edge Cases
# ============================================================================

def test_duplicate_ids():
    """Test handling of duplicate knowledge IDs"""
    
    # Create items with duplicate IDs (but different content)
    reps = [
        create_test_representation("CON_001", ["S0001"]),
        create_test_representation("CON_001", ["S0002"]),  # Duplicate ID
        create_test_representation("CON_002", ["S0003"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # All items should be present (no silent dropping)
    assert result.statistics.total_items == 3
    assert result.metadata.duplicate_ids_found > 0
    
    print("[PASS] Duplicate IDs handled without dropping")


def test_identical_content_different_ids():
    """Test distinct items with identical content"""
    
    rep1 = create_test_representation("CON_001", ["S0001"])
    rep2 = create_test_representation("CON_002", ["S0002"])
    # Same format_content, different IDs
    rep1.format_content = {"content": "Identical content"}
    rep2.format_content = {"content": "Identical content"}
    
    rep_doc = create_test_rep_doc([rep1, rep2])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Both items should be present
    assert result.statistics.total_items == 2
    items = result.sections[0].items
    assert items[0].knowledge_id != items[1].knowledge_id
    
    print("[PASS] Identical content with different IDs preserved")


def test_missing_source_ids():
    """Test items with empty source_unit_ids list"""
    
    reps = [
        create_test_representation("CON_001", []),
        create_test_representation("CON_002", []),
        create_test_representation("CON_003", [])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # All items should be present
    assert result.statistics.total_items == 3
    # Should use ID-based ordering
    assert result.sections[0].items[0].ordering_rationale == "id-based"
    
    print("[PASS] Missing source IDs handled")


def test_overlapping_source_ids():
    """Test items with overlapping source IDs"""
    
    reps = [
        create_test_representation("CON_001", ["S0001", "S0002"]),
        create_test_representation("CON_002", ["S0002", "S0003"]),  # Overlaps
        create_test_representation("CON_003", ["S0004"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # All items should be present
    assert result.statistics.total_items == 3
    # Ordering should be by minimum source ID
    items = result.sections[0].items
    assert items[0].knowledge_id == "CON_001"  # min: S0001
    assert items[1].knowledge_id == "CON_002"  # min: S0002
    assert items[2].knowledge_id == "CON_003"  # min: S0004
    
    print("[PASS] Overlapping source IDs handled")


# ============================================================================
# Statistics Tests
# ============================================================================

def test_statistics_accurate():
    """Test that statistics are calculated correctly"""
    
    reps = [
        create_test_representation("CON_001", ["S0001"], RepresentationFormat.DEFINITION_BOX),
        create_test_representation("CON_002", ["S0002"], RepresentationFormat.DEFINITION_BOX),
        create_test_representation("CON_003", ["S0003"], RepresentationFormat.STANDARD_TEXT),
        create_test_representation("CON_004", ["S0004"], RepresentationFormat.EXAMPLE_CALLOUT)
    ]
    
    # Set different confidence labels
    reps[0].confidence_label = "high"
    reps[1].confidence_label = "high"
    reps[2].confidence_label = "fallback"
    reps[3].confidence_label = "medium"
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Verify statistics
    assert result.statistics.total_items == 4
    assert result.statistics.items_by_format[RepresentationFormat.DEFINITION_BOX] == 2
    assert result.statistics.items_by_format[RepresentationFormat.STANDARD_TEXT] == 1
    assert result.statistics.items_by_format[RepresentationFormat.EXAMPLE_CALLOUT] == 1
    assert result.statistics.items_by_confidence["high"] == 2
    assert result.statistics.items_by_confidence["fallback"] == 1
    assert result.statistics.items_by_confidence["medium"] == 1
    
    print("[PASS] Statistics calculated accurately")


# ============================================================================
# Serialization Tests
# ============================================================================

def test_assembled_document_serialization():
    """Test that assembled document can be serialized to JSON"""
    
    reps = [
        create_test_representation("CON_001", ["S0001"]),
        create_test_representation("CON_002", ["S0002"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Serialize to JSON
    json_str = result.model_dump_json()
    
    # Verify it's valid JSON
    import json
    json_data = json.loads(json_str)
    
    assert json_data["document_id"] == "TEST_DOC"
    assert len(json_data["sections"]) >= 1
    assert json_data["statistics"]["total_items"] == 2
    
    print("[PASS] Assembled document serialization")


def test_assembled_document_round_trip():
    """Test JSON round-trip for assembled document"""
    
    reps = [
        create_test_representation("CON_001", ["S0001"]),
        create_test_representation("CON_002", ["S0002"])
    ]
    
    rep_doc = create_test_rep_doc(reps)
    assembler = NoteAssembler()
    
    original = assembler.assemble(rep_doc)
    
    # Serialize and deserialize
    json_str = original.model_dump_json()
    
    from app.assembly.models import AssembledNotesDocument
    restored = AssembledNotesDocument.model_validate_json(json_str)
    
    # Verify data matches
    assert restored.document_id == original.document_id
    assert restored.statistics.total_items == original.statistics.total_items
    assert len(restored.sections) == len(original.sections)
    assert restored.sections[0].items[0].knowledge_id == original.sections[0].items[0].knowledge_id
    
    print("[PASS] Assembled document round-trip")


# ============================================================================
# No Unsupported Content Tests
# ============================================================================

def test_no_invented_content():
    """Test that assembler doesn't invent any content"""
    
    rep = create_test_representation("CON_001", ["S0001"])
    original_content = rep.format_content.copy()
    
    rep_doc = create_test_rep_doc([rep])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    # Verify content exactly matches (no additions)
    item = result.sections[0].items[0]
    assert item.format_content == original_content
    
    # Verify no extra fields added to format_content
    assert set(item.format_content.keys()) == set(original_content.keys())
    
    print("[PASS] No invented content")


def test_no_format_modification():
    """Test that assembler doesn't change representation formats"""
    
    rep = create_test_representation("DEF_001", ["S0001"], RepresentationFormat.DEFINITION_BOX)
    
    rep_doc = create_test_rep_doc([rep])
    assembler = NoteAssembler()
    
    result = assembler.assemble(rep_doc)
    
    item = result.sections[0].items[0]
    assert item.primary_format == RepresentationFormat.DEFINITION_BOX
    
    print("[PASS] No format modification")


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("NOTE ASSEMBLER UNIT TESTS")
    print("=" * 80)
    print()
    
    tests = [
        # Basic
        test_normal_assembly,
        test_empty_input,
        test_single_item,
        
        # Ordering
        test_source_order_maintained,
        test_deterministic_ordering,
        test_id_based_fallback,
        test_position_in_section,
        
        # Provenance
        test_provenance_preserved,
        test_format_content_preserved,
        test_secondary_format_preserved,
        
        # Edge cases
        test_duplicate_ids,
        test_identical_content_different_ids,
        test_missing_source_ids,
        test_overlapping_source_ids,
        
        # Statistics
        test_statistics_accurate,
        
        # Serialization
        test_assembled_document_serialization,
        test_assembled_document_round_trip,
        
        # Content integrity
        test_no_invented_content,
        test_no_format_modification
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
