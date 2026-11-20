"""
Comprehensive tests for the ingestion layer.

Tests validate:
- Ordering preservation
- Provenance tracking
- Multimodal content retention
- Classification behavior
- Robustness to edge cases

NOTE: These tests are skipped on Windows due to a critical bug in the Docling library
(versions up to 2.127.0) where PyTorch RT-DETR layout detection models cause access
violations. See INGESTION_WINDOWS_LIMITATION.md for details.
"""

import sys
from pathlib import Path
import pytest

# Skip all ingestion tests on Windows due to Docling library bug
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Docling has critical Windows bug in layout detection models (access violation 0xc0000374)"
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.docling_parser import DoclingParser
from app.ingestion.content_classifier import ContentRoleClassifier
from app.models.source import SourceUnit, BoundingBox


def test_ordering_preservation():
    """Test 1: Verify SourceUnit ordering matches doc.body.children"""
    print("\n" + "=" * 80)
    print("TEST 1: Ordering Preservation")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_ORDER")
    
    # Check that positions are sequential
    for i, unit in enumerate(document.source_units, start=1):
        assert unit.position == i, f"Position mismatch: expected {i}, got {unit.position}"
    
    print(f"✓ All {len(document.source_units)} units have correct sequential positions")
    return True


def test_provenance_tracking():
    """Test 2: Verify docling_ref, page, and bbox are preserved"""
    print("\n" + "=" * 80)
    print("TEST 2: Provenance Tracking")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_PROV")
    
    units_with_ref = sum(1 for u in document.source_units if u.docling_ref)
    units_with_page = sum(1 for u in document.source_units if u.page is not None)
    units_with_bbox = sum(1 for u in document.source_units if u.bbox is not None)
    
    print(f"✓ Units with docling_ref: {units_with_ref}/{len(document.source_units)}")
    print(f"✓ Units with page: {units_with_page}/{len(document.source_units)}")
    print(f"✓ Units with bbox: {units_with_bbox}/{len(document.source_units)}")
    
    # All units should have docling_ref
    assert units_with_ref == len(document.source_units), "Some units missing docling_ref"
    
    # Most units should have page and bbox
    assert units_with_page > 0.9 * len(document.source_units), "Too few units have page numbers"
    assert units_with_bbox > 0.9 * len(document.source_units), "Too few units have bounding boxes"
    
    return True


def test_multimodal_content():
    """Test 3: Verify pictures and other non-text content are retained"""
    print("\n" + "=" * 80)
    print("TEST 3: Multimodal Content Retention")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_MULTI")
    
    # Count different types
    type_counts = {}
    for unit in document.source_units:
        type_counts[unit.type] = type_counts.get(unit.type, 0) + 1
    
    print(f"✓ Type distribution:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name:15s}: {count:3d}")
    
    # Verify we have pictures
    assert type_counts.get("picture", 0) > 0, "No pictures found - multimodal content lost"
    
    # Verify pictures without text are preserved
    pictures = [u for u in document.source_units if u.type == "picture"]
    pictures_without_text = sum(1 for p in pictures if not p.text)
    print(f"✓ Pictures without text preserved: {pictures_without_text}/{len(pictures)}")
    
    return True


def test_classification_non_destructive():
    """Test 4: Verify classifier assigns roles without deleting units"""
    print("\n" + "=" * 80)
    print("TEST 4: Non-Destructive Classification")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_CLASS")
    
    # Count content roles
    role_counts = {}
    for unit in document.source_units:
        role_counts[unit.content_role] = role_counts.get(unit.content_role, 0) + 1
    
    print(f"✓ Content role distribution:")
    for role, count in sorted(role_counts.items()):
        print(f"  {role:15s}: {count:3d}")
    
    # All units should have a content_role assigned
    assert all(u.content_role for u in document.source_units), "Some units missing content_role"
    
    # No units should be deleted
    assert len(document.source_units) > 0, "All units were deleted"
    
    # Check that we have various roles
    assert "content" in role_counts, "No content role assigned"
    assert "structural" in role_counts, "No structural role assigned"
    
    return True


def test_empty_text_handling():
    """Test 8: Items without text must still survive if meaningful"""
    print("\n" + "=" * 80)
    print("TEST 8: Empty Text Handling")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_EMPTY")
    
    # Find units without text
    units_without_text = [u for u in document.source_units if not u.text]
    
    print(f"✓ Units without text: {len(units_without_text)}")
    
    # Check their types
    type_counts = {}
    for unit in units_without_text:
        type_counts[unit.type] = type_counts.get(unit.type, 0) + 1
    
    print(f"✓ Types of units without text:")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name:15s}: {count:3d}")
    
    # Pictures without text should be preserved as content
    pictures_without_text = [u for u in units_without_text if u.type == "picture"]
    if pictures_without_text:
        assert all(p.content_role == "content" for p in pictures_without_text), \
            "Pictures without text should be classified as content"
        print(f"✓ All {len(pictures_without_text)} pictures without text classified as content")
    
    return True


def test_duplicate_ids():
    """Test 7: Ensure SourceUnit IDs are unique"""
    print("\n" + "=" * 80)
    print("TEST 7: Duplicate ID Detection")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_DUP")
    
    source_ids = [u.source_id for u in document.source_units]
    unique_ids = set(source_ids)
    
    print(f"✓ Total IDs: {len(source_ids)}")
    print(f"✓ Unique IDs: {len(unique_ids)}")
    
    assert len(source_ids) == len(unique_ids), "Duplicate source IDs found"
    
    return True


def test_parent_mapping():
    """Test 6: Verify parent IDs are resolved when possible"""
    print("\n" + "=" * 80)
    print("TEST 6: Parent Mapping")
    print("=" * 80)
    
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="TEST_PARENT")
    
    units_with_parent = sum(1 for u in document.source_units if u.parent_id)
    
    print(f"✓ Units with parent_id: {units_with_parent}/{len(document.source_units)}")
    
    # Verify parent_id references exist
    all_ids = {u.source_id for u in document.source_units}
    
    for unit in document.source_units:
        if unit.parent_id:
            assert unit.parent_id in all_ids, \
                f"Unit {unit.source_id} has invalid parent_id {unit.parent_id}"
    
    if units_with_parent > 0:
        print(f"✓ All parent_id references are valid")
    else:
        print(f"  Note: No parent relationships found in this document")
    
    return True


def test_classifier_edge_cases():
    """Test classifier with edge cases"""
    print("\n" + "=" * 80)
    print("TEST: Classifier Edge Cases")
    print("=" * 80)
    
    classifier = ContentRoleClassifier()
    
    test_cases = [
        # (SourceUnit, expected_role)
        (
            SourceUnit(
                source_id="T001", document_id="TEST", type="paragraph",
                text="1", position=1, bbox=BoundingBox(left=0, top=600, right=10, bottom=590)
            ),
            "furniture",  # Page number at bottom
            "Page number at bottom"
        ),
        (
            SourceUnit(
                source_id="T002", document_id="TEST", type="picture",
                text=None, position=2
            ),
            "content",  # Picture without text
            "Picture without text"
        ),
        (
            SourceUnit(
                source_id="T003", document_id="TEST", type="paragraph",
                text="Reprint 2026-27", position=3
            ),
            "furniture",  # Generic footer
            "Reprint footer"
        ),
        (
            SourceUnit(
                source_id="T004", document_id="TEST", type="paragraph",
                text="1 1 1 1 1", position=4
            ),
            "noise",  # Repeated chars
            "Repeated extraction artifact"
        ),
        (
            SourceUnit(
                source_id="T005", document_id="TEST", type="heading",
                text="Introduction", position=5
            ),
            "structural",  # Heading
            "Heading"
        ),
        (
            SourceUnit(
                source_id="T006", document_id="TEST", type="paragraph",
                text="This is a normal paragraph with educational content.", position=6
            ),
            "content",  # Normal content
            "Normal paragraph"
        ),
    ]
    
    all_passed = True
    for unit, expected, description in test_cases:
        result = classifier.classify(unit)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: {result} {'==' if result == expected else '!='} {expected}")
        if result != expected:
            all_passed = False
    
    assert all_passed, "Some classifier test cases failed"
    
    return True


def run_all_tests():
    """Run all ingestion tests"""
    print("\n" + "=" * 80)
    print("INGESTION LAYER TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Ordering Preservation", test_ordering_preservation),
        ("Provenance Tracking", test_provenance_tracking),
        ("Multimodal Content", test_multimodal_content),
        ("Non-Destructive Classification", test_classification_non_destructive),
        ("Empty Text Handling", test_empty_text_handling),
        ("Duplicate ID Detection", test_duplicate_ids),
        ("Parent Mapping", test_parent_mapping),
        ("Classifier Edge Cases", test_classifier_edge_cases),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL", None))
        except Exception as e:
            results.append((test_name, "FAIL", str(e)))
            print(f"\n✗ {test_name} FAILED: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, status, error in results:
        print(f"{status:6s} - {test_name}")
        if error:
            print(f"         Error: {error}")
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
