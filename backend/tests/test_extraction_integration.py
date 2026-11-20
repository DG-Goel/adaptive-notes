"""
Integration tests for knowledge extraction with real LLM provider.

These tests are OPTIONAL and only run when API credentials are configured.
They verify that the extraction pipeline works with real LLM responses.

IMPORTANT:
- These tests incur API costs
- They are SKIPPED by default when no API key is present
- They use minimal input to minimize cost
- They test integration, not semantic quality
"""

import os
import json
from typing import Optional
import pytest

from app.models.source import SourceDocument, SourceUnit
from app.extraction.llm_provider import OpenAIProvider
from app.extraction.extractor import KnowledgeExtractor


def get_api_key() -> Optional[str]:
    """Get API key from environment, returns None if not configured"""
    return os.getenv("OPENAI_API_KEY")


def create_minimal_test_document() -> SourceDocument:
    """
    Create minimal test document (text-only, no pictures).
    
    Small content to minimize API costs.
    """
    return SourceDocument(
        document_id="INTEGRATION_TEST",
        filename="integration_test.txt",
        page_count=1,
        source_units=[
            SourceUnit(
                source_id="INT_001",
                document_id="INTEGRATION_TEST",
                type="paragraph",
                content_role="content",
                text="Machine learning is a subset of artificial intelligence.",
                position=1,
                page=1
            ),
            SourceUnit(
                source_id="INT_002",
                document_id="INTEGRATION_TEST",
                type="paragraph",
                content_role="content",
                text="Neural networks are a type of machine learning algorithm inspired by the human brain.",
                position=2,
                page=1
            ),
        ]
    )


def test_extraction_with_real_openai():
    """
    Integration test with real OpenAI API.
    
    SKIPPED if OPENAI_API_KEY environment variable is not set.
    """
    api_key = get_api_key()
    
    if not api_key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    
    print("\n" + "=" * 80)
    print("RUNNING: test_extraction_with_real_openai")
    print("This test will make a real API call and incur costs")
    print("=" * 80)
    
    try:
        # Create provider with real API key
        provider = OpenAIProvider(
            api_key=api_key,
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            max_tokens=500  # Limit response size to minimize cost
        )
        
        # Create extractor
        extractor = KnowledgeExtractor(provider, verbose=True)
        
        # Create minimal test document
        doc = create_minimal_test_document()
        
        print(f"\nExtracting from {len(doc.source_units)} source units...")
        
        # Extract knowledge
        result = extractor.extract(doc)
        
        # Validation checks
        print("\n" + "-" * 80)
        print("VALIDATION RESULTS:")
        print("-" * 80)
        
        # Check 1: Result is not empty
        has_items = result.total_items > 0
        print(f"✓ Knowledge items extracted: {result.total_items}" if has_items else "✗ No knowledge items extracted")
        
        # Check 2: Source IDs are valid
        all_source_ids = set()
        valid_ids = {"INT_001", "INT_002"}
        
        for concept in result.concepts:
            all_source_ids.update(concept.source_unit_ids)
        for definition in result.definitions:
            all_source_ids.update(definition.source_unit_ids)
        for explanation in result.explanations:
            all_source_ids.update(explanation.source_unit_ids)
        for relationship in result.relationships:
            all_source_ids.update(relationship.source_unit_ids)
        
        invalid_ids = all_source_ids - valid_ids
        source_valid = len(invalid_ids) == 0
        print(f"✓ All source IDs valid: {all_source_ids}" if source_valid else f"✗ Invalid source IDs found: {invalid_ids}")
        
        # Check 3: Invalid refs count
        validation_warnings = extractor.invalid_refs_count == 0
        print(f"✓ No validation warnings ({extractor.invalid_refs_count} invalid refs)" if validation_warnings else f"⚠ Validation warnings: {extractor.invalid_refs_count} invalid refs filtered")
        
        # Check 4: Document ID preserved
        doc_id_preserved = True
        for concept in result.concepts:
            if concept.document_id != "INTEGRATION_TEST":
                doc_id_preserved = False
        print(f"✓ Document IDs preserved" if doc_id_preserved else "✗ Document ID mismatch")
        
        # Summary
        print("\n" + "-" * 80)
        if has_items and source_valid and doc_id_preserved:
            print("✅ INTEGRATION TEST PASSED")
            print("\nNOTE: This test validates integration, not semantic quality.")
            print("Semantic accuracy should be evaluated manually or with dedicated QA tests.")
        else:
            print("❌ INTEGRATION TEST FAILED")
            print("Check validation results above for details.")
        
        print("=" * 80)
        
        # Assert all checks passed
        assert has_items, "No knowledge items extracted"
        assert source_valid, f"Invalid source IDs found: {invalid_ids}"
        assert doc_id_preserved, "Document ID not preserved"
        
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("=" * 80)
    print("KNOWLEDGE EXTRACTION INTEGRATION TESTS")
    print("=" * 80)
    print("\nThese tests use real LLM providers and incur API costs.")
    print("They are skipped if credentials are not configured.")
    print()
    
    # Run integration test
    status = test_extraction_with_real_openai()
    
    # Report results
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Real LLM Provider Test: {status}")
    print()
    
    if status == "SKIPPED":
        print("To enable integration tests:")
        print("  1. Set OPENAI_API_KEY environment variable")
        print("  2. Re-run this test file")
        print()
        print("Example:")
        print("  $env:OPENAI_API_KEY = 'sk-...'")
        print("  python tests/test_extraction_integration.py")
    elif status == "PASSED":
        print("✅ Integration with real LLM provider working correctly")
        print("   - API connection successful")
        print("   - Response parsing working")
        print("   - Source validation working")
    elif status == "FAILED":
        print("❌ Integration test failed - see details above")
        exit(1)
    elif status == "ERROR":
        print("❌ Integration test encountered an error")
        exit(1)
    
    print("=" * 80)
