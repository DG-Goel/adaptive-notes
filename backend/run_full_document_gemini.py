#!/usr/bin/env python3
"""
Full document extraction using Gemini provider.

This script runs the complete extraction pipeline on a full document using
Google's Gemini API. It includes:
- Token budget management
- Retry logic for transient failures
- Adaptive chunk splitting for truncation
- Detailed error reporting
- Extraction completeness tracking
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
    print("FULL DOCUMENT EXTRACTION - GEMINI PROVIDER")
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
    
    print(f"\n✓ Configuration:")
    print(f"  API key: {api_key[:10]}...{api_key[-4:]}")
    print(f"  Model: {model}")
    
    # Load source document
    source_path = Path("data/output/source_units.json")
    
    if not source_path.exists():
        print(f"\n❌ ERROR: Source document not found at {source_path}")
        print("   Run ingestion first to generate source document.")
        return 1
    
    with open(source_path, 'r', encoding='utf-8') as f:
        doc = SourceDocument.model_validate(json.load(f))
    
    print(f"\n✓ Loaded source document:")
    print(f"  Document ID: {doc.document_id}")
    print(f"  Filename: {doc.filename}")
    print(f"  Total units: {len(doc.source_units)}")
    print(f"  Pages: {doc.page_count}")
    
    # Initialize Gemini provider
    print(f"\n{'='*80}")
    print("INITIALIZING GEMINI PROVIDER")
    print(f"{'='*80}")
    
    try:
        provider = GeminiProvider(
            model=model,
            api_key=api_key,
            tokens_per_minute=15000  # Adjust based on your tier
        )
        print(f"✓ Provider initialized")
        print(f"  Model: {provider.model}")
        print(f"  TPM limit: {provider.tokens_per_minute}")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize provider: {e}")
        return 1
    
    # Configure extraction
    print(f"\n{'='*80}")
    print("EXTRACTION CONFIGURATION")
    print(f"{'='*80}")
    print(f"  Max tokens per chunk: 2000")
    print(f"  Min output tokens: 500")
    print(f"  Preferred output tokens: 4000")
    print(f"  Max retries: 2")
    print(f"  Max split depth: 2")
    
    # Run extraction
    print(f"\n{'='*80}")
    print("RUNNING EXTRACTION")
    print(f"{'='*80}")
    
    try:
        start = time.time()
        
        extractor = KnowledgeExtractor(
            provider,
            max_tokens_per_chunk=2000,
            verbose=True,
            max_retries=2,
            min_output_tokens=500,
            preferred_output_tokens=4000,
            max_split_depth=2
        )
        
        result = extractor.extract(doc)
        
        elapsed = time.time() - start
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Report results
    print(f"\n{'='*80}")
    print("EXTRACTION RESULTS")
    print(f"{'='*80}")
    
    # Extraction completeness
    metadata = result.extraction_metadata
    if metadata:
        completeness = metadata.get('completeness', 0.0)
        total_chunks = metadata.get('total_chunks', 0)
        successful_chunks = metadata.get('successful_chunks', 0)
        failed_chunks = metadata.get('failed_chunks', [])
        split_chunks = metadata.get('split_chunks', [])
        
        print(f"\n📊 EXTRACTION COMPLETENESS:")
        print(f"   Total chunks: {total_chunks}")
        print(f"   Successful: {successful_chunks}")
        print(f"   Failed: {len(failed_chunks)}")
        print(f"   Split (adaptive): {len(split_chunks)}")
        print(f"   Completeness: {completeness*100:.1f}%")
        
        if failed_chunks:
            print(f"\n⚠️  Failed chunks: {failed_chunks}")
    
    # Knowledge items
    print(f"\n📦 EXTRACTED KNOWLEDGE:")
    print(f"   Total items: {result.total_items}")
    print(f"   Concepts: {len(result.concepts)}")
    print(f"   Definitions: {len(result.definitions)}")
    print(f"   Explanations: {len(result.explanations)}")
    print(f"   Examples: {len(result.examples)}")
    print(f"   Facts: {len(result.facts)}")
    print(f"   Formulas: {len(result.formulas)}")
    print(f"   Procedures: {len(result.procedures)}")
    print(f"   Relationships: {len(result.relationships)}")
    
    # Performance
    print(f"\n⏱️  PERFORMANCE:")
    print(f"   Total time: {elapsed:.2f}s ({elapsed/60:.1f} min)")
    print(f"   Time per unit: {elapsed/len(doc.source_units):.2f}s")
    print(f"   Items per unit: {result.total_items/len(doc.source_units):.2f}")
    print(f"   Extraction rate: {result.total_items/elapsed:.1f} items/sec")
    
    # Save results
    output_dir = Path("data/output/gemini_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"knowledge_document_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Knowledge document saved to: {output_path}")
    
    # Also save metadata separately for analysis
    metadata_path = output_dir / f"extraction_metadata_{timestamp}.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Extraction metadata saved to: {metadata_path}")
    
    # Final summary
    print(f"\n{'='*80}")
    
    if completeness >= 1.0 and result.total_items > 0:
        print("✅ EXTRACTION COMPLETE - 100% SUCCESS")
        print(f"{'='*80}")
        print(f"\nExtracted {result.total_items} knowledge items from {len(doc.source_units)} source units.")
        print("All chunks processed successfully.")
        return 0
    elif completeness >= 0.9:
        print("✅ EXTRACTION COMPLETE - MOSTLY SUCCESSFUL")
        print(f"{'='*80}")
        print(f"\nExtracted {result.total_items} knowledge items with {completeness*100:.1f}% completeness.")
        print("Some chunks may have failed due to rate limits or content filtering.")
        return 0
    else:
        print("⚠️  EXTRACTION COMPLETE - PARTIAL SUCCESS")
        print(f"{'='*80}")
        print(f"\nExtracted {result.total_items} knowledge items but only {completeness*100:.1f}% completeness.")
        print("Review failed chunks and consider:")
        print("  - Reducing chunk size")
        print("  - Checking API quotas")
        print("  - Reviewing content for filtering triggers")
        return 2


if __name__ == "__main__":
    sys.exit(main())
