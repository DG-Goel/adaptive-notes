#!/usr/bin/env python3
"""
Recover failed chunk JAVA_CHUNK_006 by retrying with smaller unit-aligned chunks.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider

def load_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path: Path, data: dict):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 80)
    print("FAILED CHUNK RECOVERY: JAVA_CHUNK_006")
    print("=" * 80)
    print()
    
    # Load source document
    artifact_dir = Path("data/output/java_transcript_validation")
    source_data = load_json(artifact_dir / "source_units_20261030_185308.json")
    source_doc = SourceDocument(**source_data)
    
    # Load knowledge document to check metadata
    knowledge_data = load_json(artifact_dir / "knowledge_20261030_185308.json")
    
    print("Analyzing failed chunk...")
    failed_chunks = knowledge_data['extraction_metadata'].get('failed_chunks', [])
    print(f"Failed chunks: {failed_chunks}")
    
    chunk_attempts = knowledge_data['extraction_metadata'].get('chunk_attempts', [])
    failed_attempts = [a for a in chunk_attempts if a['chunk_id'] == 'JAVA_CHUNK_006']
    
    if failed_attempts:
        print(f"\nFailed chunk attempts:")
        for attempt in failed_attempts:
            print(f"  Attempt {attempt['attempt']}: {attempt['error'][:200]}")
    print()
    
    # Extract source units T0016, T0017, T0018
    target_unit_ids = ['T0016', 'T0017', 'T0018']
    target_units = [u for u in source_doc.source_units if u.source_id in target_unit_ids]
    
    print(f"Target source units:")
    for unit in target_units:
        print(f"  {unit.source_id}: {unit.text[:100]}...")
    print()
    
    # Create a mini source document with just these units
    mini_doc = SourceDocument(
        document_id=source_doc.document_id,
        filename=source_doc.filename,
        page_count=1,
        source_units=target_units
    )
    
    print(f"Attempting extraction with {len(target_units)} units individually...")
    print()
    
    # Initialize extractor with Groq
    api_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
        os.getenv("GROQ_API_KEY_4"),
        os.getenv("GROQ_API_KEY_5"),
    ]
    api_keys = [k for k in api_keys if k]  # Filter None values
    
    if not api_keys:
        print("ERROR: No GROQ_API_KEY_* found in environment")
        return 1
    
    provider = GroqProvider(api_key=api_keys[0], use_multi_key=True)
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2000,  # Smaller chunks
        verbose=True,
        max_retries=2,
        max_split_depth=2
    )
    
    # Extract from mini doc
    try:
        result = extractor.extract(mini_doc)
        
        print()
        print("=" * 80)
        print("EXTRACTION RESULTS")
        print("=" * 80)
        print(f"Total items extracted: {result.total_items}")
        print(f"  Concepts: {len(result.concepts)}")
        print(f"  Definitions: {len(result.definitions)}")
        print(f"  Explanations: {len(result.explanations)}")
        print(f"  Examples: {len(result.examples)}")
        print(f"  Facts: {len(result.facts)}")
        print(f"  Formulas: {len(result.formulas)}")
        print(f"  Procedures: {len(result.procedures)}")
        print(f"  Relationships: {len(result.relationships)}")
        print()
        
        metadata = result.extraction_metadata
        print(f"Extraction metadata:")
        print(f"  Completeness: {metadata.get('completeness', 0):.1%}")
        print(f"  Successful chunks: {metadata.get('successful_chunks', 0)}")
        print(f"  Failed chunks: {len(metadata.get('failed_chunks', []))}")
        print()
        
        if result.total_items > 0:
            # Save recovered knowledge
            output_path = artifact_dir / "validation_20261030_231138" / f"recovered_chunk_006_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_json(output_path, result.model_dump())
            print(f"✓ Saved recovered knowledge to: {output_path.name}")
            return 0
        else:
            print("✗ No items extracted - recovery failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
