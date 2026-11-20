#!/usr/bin/env python3
"""
Focused 18-unit extraction with detailed error diagnostics.

Handles JSON parsing failures and provides retry logic.
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
from app.extraction.llm_provider import GroqProvider


def main():
    print("="*80)
    print("18-UNIT EXTRACTION WITH ERROR HANDLING")
    print("="*80)
    
    # Load sample
    sample_path = Path("data/output/real_llm_validation_15_20/source_sample.json")
    if not sample_path.exists():
        print(f"ERROR: Sample not found at {sample_path}")
        return 1
    
    with open(sample_path, 'r', encoding='utf-8') as f:
        doc = SourceDocument.model_validate(json.load(f))
    
    print(f"\nLoaded: {len(doc.source_units)} source units")
    print(f"Source IDs: {[u.source_id for u in doc.source_units]}")
    
    # Initialize provider
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY not set")
        return 1
    
    provider = GroqProvider(model=model, api_key=api_key)
    print(f"\nProvider: {provider.model}")
    
    # Extract with detailed logging
    print("\nExtracting...")
    start = time.time()
    
    extractor = KnowledgeExtractor(provider, verbose=True)
    result = extractor.extract(doc)
    
    elapsed = time.time() - start
    
    print(f"\n{'='*80}")
    print("EXTRACTION RESULTS")
    print(f"{'='*80}")
    print(f"Total items: {result.total_items}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Rate: {result.total_items/len(doc.source_units):.1f} items/unit")
    
    if result.total_items == 0:
        print("\n⚠ WARNING: Zero items extracted!")
        print("This indicates all chunks failed JSON parsing.")
        print("Check Groq API logs or reduce chunk size.")
        return 2
    
    # Save result
    output_path = Path("data/output/real_llm_validation_15_20/knowledge_document.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
