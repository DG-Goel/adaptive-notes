"""
Fast ingestion tests (OCR disabled for speed and Windows compatibility).

These tests validate core ingestion functionality without OCR:
- Ordering preservation
- Provenance tracking
- Multimodal content retention
- Classification behavior
- Document ID propagation

For OCR-enabled integration tests, see test_ingestion_ocr.py

NOTE: These tests are skipped on Windows due to a critical bug in the Docling library
(versions up to 2.127.0) where PyTorch RT-DETR layout detection models cause access
violations even with OCR disabled. See INGESTION_WINDOWS_LIMITATION.md for details.
"""

import sys
import pytest
from pathlib import Path
from app.ingestion.docling_parser import DoclingParser
from app.ingestion.content_classifier import ContentRoleClassifier
from app.models.source import SourceUnit, BoundingBox


# Skip all ingestion tests on Windows due to Docling library bug
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Docling has critical Windows bug in layout detection models (access violation 0xc0000374)"
)


# Use session-scoped parser to avoid threading issues
@pytest.fixture(scope="session")
def parser():
    """Create parser with OCR disabled (fast mode) - reused across all tests"""
    return DoclingParser(verbose=False, enable_ocr=False)


def test_ordering_preservation(parser):
    """Verify SourceUnit ordering matches document order"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_ORDER")
    
    # Check sequential positions
    for i, unit in enumerate(document.source_units, start=1):
        assert unit.position == i, f"Position mismatch: expected {i}, got {unit.position}"
    
    print(f"\n✓ All {len(document.source_units)} units have correct sequential positions")


def test_provenance_tracking(parser):
    """Verify docling_ref, page, and bbox are preserved"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_PROV")
    
    units_with_ref = sum(1 for u in document.source_units if u.docling_ref)
    units_with_page = sum(1 for u in document.source_units if u.page is not None)
    units_with_bbox = sum(1 for u in document.source_units if u.bbox is not None)
    
    print(f"\n✓ Units with docling_ref: {units_with_ref}/{len(document.source_units)}")
    print(f"✓ Units with page: {units_with_page}/{len(document.source_units)}")
    print(f"✓ Units with bbox: {units_with_bbox}/{len(document.source_units)}")
    
    # All units should have docling_ref
    assert units_with_ref == len(document.source_units), "Some units missing docling_ref"
    
    # Most units should have page and bbox
    assert units_with_page > 0.9 * len(document.source_units), "Too few units have page numbers"
    assert units_with_bbox > 0.9 * len(document.source_units), "Too few units have bounding boxes"


def test_multimodal_content(parser):
    """Verify pictures and other non-text content are retained"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_MULTI")
    
    # Count different types
    type_counts = {}
    for unit in document.source_units:
        type_counts[unit.type] = type_counts.get(unit.type, 0) + 1
    
    print(f"\n✓ Type distribution:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name:15s}: {count:3d}")
    
    # Verify we have pictures
    assert type_counts.get("picture", 0) > 0, "No pictures found - multimodal content lost"
    
    # Verify pictures without text are preserved
    pictures = [u for u in document.source_units if u.type == "picture"]
    pictures_without_text = sum(1 for p in pictures if not p.text)
    print(f"✓ Pictures without text preserved: {pictures_without_text}/{len(pictures)}")


def test_classification_non_destructive(parser):
    """Verify classifier assigns roles without deleting units"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_CLASS")
    
    # Count content roles
    role_counts = {}
    for unit in document.source_units:
        role_counts[unit.content_role] = role_counts.get(unit.content_role, 0) + 1
    
    print(f"\n✓ Content role distribution:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role:15s}: {count:3d}")
    
    # All units should have a content_role assigned
    assert all(u.content_role for u in document.source_units), "Some units missing content_role"
    
    # No units should be deleted
    assert len(document.source_units) > 0, "All units were deleted"
    
    # Check that we have various roles
    assert "content" in role_counts, "No content role assigned"
    assert "structural" in role_counts, "No structural role assigned"


def test_document_id_propagation(parser):
    """Verify document ID is propagated to all source units"""
    test_id = "CUSTOM_DOC_ID_12345"
    document = parser.parse("data/input/test.pdf", document_id=test_id)
    
    # Document should have the provided ID
    assert document.document_id == test_id, f"Document ID not preserved: {document.document_id}"
    
    # All source units should have the same document ID
    for unit in document.source_units:
        assert unit.document_id == test_id, \
            f"Source unit {unit.source_id} has wrong document_id: {unit.document_id}"
    
    print(f"\n✓ Document ID '{test_id}' correctly propagated to all {len(document.source_units)} units")


def test_empty_text_handling(parser):
    """Items without text must still survive if meaningful"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_EMPTY")
    
    # Find units without text
    units_without_text = [u for u in document.source_units if not u.text]
    
    print(f"\n✓ Units without text: {len(units_without_text)}")
    
    # Check their types
    type_counts = {}
    for unit in units_without_text:
        type_counts[unit.type] = type_counts.get(unit.type, 0) + 1
    
    if type_counts:
        print(f"✓ Types of units without text:")
        for type_name, count in sorted(type_counts.items()):
            print(f"  {type_name:15s}: {count:3d}")
    
    # Pictures without text should be preserved as content
    pictures_without_text = [u for u in units_without_text if u.type == "picture"]
    if pictures_without_text:
        assert all(p.content_role == "content" for p in pictures_without_text), \
            "Pictures without text should be classified as content"
        print(f"✓ All {len(pictures_without_text)} pictures without text classified as content")


def test_duplicate_ids(parser):
    """Ensure SourceUnit IDs are unique"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_DUP")
    
    source_ids = [u.source_id for u in document.source_units]
    unique_ids = set(source_ids)
    
    print(f"\n✓ Total IDs: {len(source_ids)}")
    print(f"✓ Unique IDs: {len(unique_ids)}")
    
    assert len(source_ids) == len(unique_ids), "Duplicate source IDs found"


def test_parent_mapping(parser):
    """Verify parent IDs are resolved when possible"""
    document = parser.parse("data/input/test.pdf", document_id="TEST_PARENT")
    
    units_with_parent = sum(1 for u in document.source_units if u.parent_id)
    
    print(f"\n✓ Units with parent_id: {units_with_parent}/{len(document.source_units)}")
    
    # Verify parent_id references exist
    all_ids = {u.source_id for u in document.source_units}
    
    for unit in document.source_units:
        if unit.parent_id:
            assert unit.parent_id in all_ids, \
                f"Unit {unit.source_id} has invalid parent_id {unit.parent_id}"
    
    if units_with_parent > 0:
        print(f"✓ All parent_id references are valid")


def test_missing_file():
    """Parser should raise FileNotFoundError for missing files"""
    parser = DoclingParser(verbose=False, enable_ocr=False)
    
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf", document_id="TEST")


def test_classifier_edge_cases():
    """Test classifier with edge cases"""
    classifier = ContentRoleClassifier()
    
    test_cases = [
        # (SourceUnit, expected_role, description)
        (
            SourceUnit(
                source_id="T001", document_id="TEST", type="paragraph",
                text="1", position=1, bbox=BoundingBox(left=0, top=600, right=10, bottom=590)
            ),
            "furniture",
            "Page number at bottom"
        ),
        (
            SourceUnit(
                source_id="T002", document_id="TEST", type="picture",
                text=None, position=2
            ),
            "content",
            "Picture without text"
        ),
        (
            SourceUnit(
                source_id="T003", document_id="TEST", type="heading",
                text="Introduction", position=3
            ),
            "structural",
            "Heading"
        ),
        (
            SourceUnit(
                source_id="T004", document_id="TEST", type="paragraph",
                text="This is a normal paragraph with educational content.", position=4
            ),
            "content",
            "Normal paragraph"
        ),
    ]
    
    print("\n✓ Classifier edge cases:")
    all_passed = True
    for unit, expected, description in test_cases:
        result = classifier.classify(unit)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {description}: {result}")
        if result != expected:
            all_passed = False
            print(f"    Expected: {expected}, got: {result}")
    
    assert all_passed, "Some classifier test cases failed"
