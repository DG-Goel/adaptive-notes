"""
Quick validation script for ingestion layer
"""

import json
from collections import Counter

from app.ingestion.docling_parser import DoclingParser


def main():
    print("=" * 80)
    print("INGESTION LAYER VALIDATION")
    print("=" * 80)
    
    # Parse the document
    parser = DoclingParser(verbose=False)
    document = parser.parse("data/input/test.pdf", document_id="VALIDATE")
    
    # Basic stats
    print(f"\n✓ Document: {document.filename}")
    print(f"✓ Pages: {document.page_count}")
    print(f"✓ Total source units: {len(document.source_units)}")
    
    # Test 1: Ordering validation
    print("\n" + "-" * 80)
    print("TEST 1: Ordering Validation")
    print("-" * 80)
    
    ordering_ok = all(
        unit.position == i 
        for i, unit in enumerate(document.source_units, start=1)
    )
    print(f"{'✓' if ordering_ok else '✗'} Position ordering: {'PASS' if ordering_ok else 'FAIL'}")
    
    # Test 2: Unique IDs
    print("\n" + "-" * 80)
    print("TEST 2: Unique IDs")
    print("-" * 80)
    
    source_ids = [u.source_id for u in document.source_units]
    unique_ok = len(source_ids) == len(set(source_ids))
    print(f"{'✓' if unique_ok else '✗'} Unique source IDs: {'PASS' if unique_ok else 'FAIL'}")
    
    # Test 3: Provenance preservation
    print("\n" + "-" * 80)
    print("TEST 3: Provenance Preservation")
    print("-" * 80)
    
    units_with_ref = sum(1 for u in document.source_units if u.docling_ref)
    units_with_page = sum(1 for u in document.source_units if u.page is not None)
    units_with_bbox = sum(1 for u in document.source_units if u.bbox is not None)
    
    print(f"✓ Units with docling_ref: {units_with_ref}/{len(document.source_units)} ({100*units_with_ref/len(document.source_units):.1f}%)")
    print(f"✓ Units with page: {units_with_page}/{len(document.source_units)} ({100*units_with_page/len(document.source_units):.1f}%)")
    print(f"✓ Units with bbox: {units_with_bbox}/{len(document.source_units)} ({100*units_with_bbox/len(document.source_units):.1f}%)")
    
    # Test 4: Type distribution
    print("\n" + "-" * 80)
    print("TEST 4: Type Distribution")
    print("-" * 80)
    
    type_counts = Counter(u.type for u in document.source_units)
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name:15s}: {count:3d} ({100*count/len(document.source_units):5.1f}%)")
    
    # Verify we have pictures
    has_pictures = type_counts.get("picture", 0) > 0
    print(f"\n{'✓' if has_pictures else '✗'} Multimodal content preserved: {'PASS' if has_pictures else 'FAIL'}")
    
    # Test 5: Content role distribution
    print("\n" + "-" * 80)
    print("TEST 5: Content Role Distribution")
    print("-" * 80)
    
    role_counts = Counter(u.content_role for u in document.source_units)
    for role, count in sorted(role_counts.items()):
        print(f"  {role:15s}: {count:3d} ({100*count/len(document.source_units):5.1f}%)")
    
    # Verify no units are missing roles
    no_missing_roles = all(u.content_role for u in document.source_units)
    print(f"\n{'✓' if no_missing_roles else '✗'} All units classified: {'PASS' if no_missing_roles else 'FAIL'}")
    
    # Test 6: Empty text handling
    print("\n" + "-" * 80)
    print("TEST 6: Empty Text Handling")
    print("-" * 80)
    
    units_without_text = [u for u in document.source_units if not u.text]
    print(f"✓ Units without text: {len(units_without_text)}")
    
    empty_text_types = Counter(u.type for u in units_without_text)
    for type_name, count in sorted(empty_text_types.items()):
        print(f"  {type_name:15s}: {count:3d}")
    
    # Pictures without text should be content
    pictures_no_text = [u for u in units_without_text if u.type == "picture"]
    pictures_ok = all(p.content_role == "content" for p in pictures_no_text)
    print(f"{'✓' if pictures_ok else '✗'} Pictures without text classified as content: {'PASS' if pictures_ok else 'FAIL'}")
    
    # Test 7: Parent relationships
    print("\n" + "-" * 80)
    print("TEST 7: Parent Relationships")
    print("-" * 80)
    
    units_with_parent = sum(1 for u in document.source_units if u.parent_id)
    print(f"✓ Units with parent_id: {units_with_parent}/{len(document.source_units)}")
    
    # Verify parent IDs are valid
    all_ids = {u.source_id for u in document.source_units}
    invalid_parents = [
        u.source_id for u in document.source_units 
        if u.parent_id and u.parent_id not in all_ids
    ]
    
    if invalid_parents:
        print(f"✗ Invalid parent references found: {invalid_parents}")
    else:
        print(f"✓ All parent references valid")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    all_tests = [
        ordering_ok,
        unique_ok,
        units_with_ref == len(document.source_units),
        has_pictures,
        no_missing_roles,
        pictures_ok,
        len(invalid_parents) == 0,
    ]
    
    passed = sum(all_tests)
    total = len(all_tests)
    
    print(f"\n{passed}/{total} validation checks passed")
    
    if passed == total:
        print("\n✓ VALIDATION PASSED - Ingestion layer is production-ready")
    else:
        print(f"\n✗ VALIDATION FAILED - {total - passed} check(s) failed")
    
    # Save detailed report
    report_path = "data/output/validation_report.json"
    report = {
        "filename": document.filename,
        "document_id": document.document_id,
        "page_count": document.page_count,
        "total_units": len(document.source_units),
        "units_with_docling_ref": units_with_ref,
        "units_with_page": units_with_page,
        "units_with_bbox": units_with_bbox,
        "units_with_parent": units_with_parent,
        "type_distribution": dict(type_counts),
        "role_distribution": dict(role_counts),
        "validation_passed": passed == total,
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
