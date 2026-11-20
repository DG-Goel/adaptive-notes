#!/usr/bin/env python3
"""
Smoke test for Gemini provider with small sample extraction.

This script tests the Gemini API integration with a small number of source units
to verify:
- API authentication
- JSON output format compatibility
- Extraction completeness
- Provenance validity
- Token budget management
- Error handling

Run this BEFORE full-document extraction to catch integration issues early.
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from app.models.source import SourceDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GeminiProvider


def main():
    print("="*80)
    print("GEMINI PROVIDER SMOKE TEST")
    print("="*80)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY not set in environment")
        print("   Set it in .env file or export it:")
        print("   export GEMINI_API_KEY=your_key_here")
        return 1
    
    # Get model name
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    print(f"\n✓ API key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"✓ Model: {model}")
    
    # Load sample document
    sample_path = Path("data/output/real_llm_validation_15_20/source_sample.json")
    
    if not sample_path.exists():
        print(f"\n❌ ERROR: Sample not found at {sample_path}")
        print("   Run a previous extraction test to generate this sample.")
        return 1
    
    with open(sample_path, 'r', encoding='utf-8') as f:
        doc = SourceDocument.model_validate(json.load(f))
    
    # Limit to first 5 units for smoke test
    original_count = len(doc.source_units)
    doc.source_units = doc.source_units[:5]
    
    print(f"\n✓ Loaded sample document")
    print(f"  Original units: {original_count}")
    print(f"  Testing with: {len(doc.source_units)} units (smoke test)")
    print(f"  Source IDs: {[u.source_id for u in doc.source_units]}")
    
    # Initialize Gemini provider
    print(f"\n{'='*80}")
    print("INITIALIZING GEMINI PROVIDER")
    print(f"{'='*80}")
    
    try:
        provider = GeminiProvider(model=model, api_key=api_key)
        print(f"✓ Provider initialized")
        print(f"  Model: {provider.model}")
        print(f"  TPM limit: {provider.tokens_per_minute}")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize provider: {e}")
        return 1
    
    # Run extraction
    print(f"\n{'='*80}")
    print("RUNNING EXTRACTION")
    print(f"{'='*80}")
    
    try:
        start = time.time()
        extractor = KnowledgeExtractor(provider, verbose=True, max_retries=2)
        result = extractor.extract(doc)
        elapsed = time.time() - start
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {type(e).__name__}: {e}")
        return 1
    
    # Validate results
    print(f"\n{'='*80}")
    print("VALIDATION RESULTS")
    print(f"{'='*80}")
    
    success = True
    
    # Check extraction completeness
    metadata = result.extraction_metadata
    if metadata:
        completeness = metadata.get('completeness', 0.0)
        failed_chunks = metadata.get('failed_chunks', [])
        
        print(f"\n📊 EXTRACTION COMPLETENESS:")
        print(f"   Total chunks: {metadata.get('total_chunks', 0)}")
        print(f"   Successful: {metadata.get('successful_chunks', 0)}")
        print(f"   Failed: {len(failed_chunks)}")
        print(f"   Completeness: {completeness*100:.1f}%")
        
        if completeness < 1.0:
            print(f"\n⚠️  WARNING: Incomplete extraction")
            print(f"   Failed chunks: {failed_chunks}")
            success = False
    
    # Check for extracted items
    print(f"\n📦 EXTRACTED ITEMS:")
    print(f"   Total items: {result.total_items}")
    print(f"   Concepts: {len(result.concepts)}")
    print(f"   Definitions: {len(result.definitions)}")
    print(f"   Explanations: {len(result.explanations)}")
    print(f"   Examples: {len(result.examples)}")
    print(f"   Facts: {len(result.facts)}")
    print(f"   Formulas: {len(result.formulas)}")
    print(f"   Procedures: {len(result.procedures)}")
    print(f"   Relationships: {len(result.relationships)}")
    
    if result.total_items == 0:
        print(f"\n⚠️  WARNING: Zero items extracted!")
        print(f"   This could indicate:")
        print(f"   - API response format issues")
        print(f"   - JSON parsing failures")
        print(f"   - Content filtering by Gemini")
        success = False
    
    # Check provenance validity
    all_source_ids = {u.source_id for u in doc.source_units}
    invalid_refs = 0
    
    for item in (result.concepts + result.definitions + result.explanations + 
                 result.examples + result.facts + result.formulas + 
                 result.procedures + result.relationships):
        for source_id in item.source_unit_ids:
            if source_id not in all_source_ids:
                invalid_refs += 1
    
    print(f"\n🔗 PROVENANCE VALIDITY:")
    print(f"   Valid source IDs in document: {len(all_source_ids)}")
    print(f"   Invalid references: {invalid_refs}")
    
    if invalid_refs > 0:
        print(f"\n⚠️  WARNING: {invalid_refs} invalid source ID references")
        success = False
    
    # Performance metrics
    print(f"\n⏱️  PERFORMANCE:")
    print(f"   Total time: {elapsed:.2f}s")
    print(f"   Time per unit: {elapsed/len(doc.source_units):.2f}s")
    if result.total_items > 0:
        print(f"   Items per unit: {result.total_items/len(doc.source_units):.1f}")
    
    # Save results
    output_dir = Path("data/output/gemini_smoke_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"knowledge_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    
    # Print sample items
    if result.concepts:
        print(f"\n📝 SAMPLE CONCEPT:")
        concept = result.concepts[0]
        print(f"   Name: {concept.concept_name}")
        print(f"   Content: {concept.content[:100]}...")
        print(f"   Sources: {concept.source_unit_ids}")
    
    if result.definitions:
        print(f"\n📝 SAMPLE DEFINITION:")
        defn = result.definitions[0]
        print(f"   Term: {defn.term}")
        print(f"   Definition: {defn.definition_text[:100]}...")
        print(f"   Sources: {defn.source_unit_ids}")
    
    # Final status
    print(f"\n{'='*80}")
    if success and result.total_items > 0:
        print("✅ SMOKE TEST PASSED")
        print(f"{'='*80}")
        print("\nGemini provider is working correctly!")
        print("You can now run full-document extraction with:")
        print("  python run_full_document_gemini.py")
        return 0
    else:
        print("⚠️  SMOKE TEST COMPLETED WITH WARNINGS")
        print(f"{'='*80}")
        print("\nReview the warnings above before running full extraction.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
