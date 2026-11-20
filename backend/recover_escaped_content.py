#!/usr/bin/env python3
"""
Recover T0016, T0017, T0018 with careful JSON validation and escape handling.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider

def validate_json_locally(json_str: str) -> bool:
    """Validate JSON string before accepting"""
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError as e:
        print(f"  JSON validation failed: {e}")
        return False

def main():
    print("=" * 80)
    print("RECOVERY: T0016, T0017, T0018 (Java String escape sequences)")
    print("=" * 80)
    
    # Load source document
    artifact_dir = Path("data/output/java_transcript_validation")
    source_data_path = artifact_dir / "source_units_20261030_185308.json"
    
    with open(source_data_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    source_doc = SourceDocument(**source_data)
    
    # Extract target units
    target_unit_ids = ['T0016', 'T0017', 'T0018']
    target_units = [u for u in source_doc.source_units if u.source_id in target_unit_ids]
    
    print(f"\nTarget units: {len(target_units)}")
    for unit in target_units:
        print(f"  {unit.source_id}: {unit.text[:80]}...")
    print()
    
    # Try extraction ONE UNIT AT A TIME
    api_keys = [
        os.getenv("GROQ_API_KEY_1"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
    ]
    api_keys = [k for k in api_keys if k]
    
    if not api_keys:
        print("ERROR: No API keys found")
        return 1
    
    provider = GroqProvider(api_key=api_keys[0], use_multi_key=True)
    
    # Try each unit individually with very small token limit
    all_extracted = []
    failed_units = []
    
    for unit in target_units:
        print(f"\n{'='*80}")
        print(f"Extracting: {unit.source_id}")
        print(f"{'='*80}")
        
        # Create single-unit document
        mini_doc = SourceDocument(
            document_id=source_doc.document_id,
            filename=source_doc.filename,
            page_count=1,
            source_units=[unit]
        )
        
        # Use very conservative settings
        extractor = KnowledgeExtractor(
            llm_provider=provider,
            max_tokens_per_chunk=1500,  # Small chunk
            verbose=True,
            max_retries=2,
            max_split_depth=1
        )
        
        try:
            result = extractor.extract(mini_doc)
            
            if result.total_items > 0:
                print(f"  ✓ Success: {result.total_items} items extracted")
                all_extracted.append({
                    "source_id": unit.source_id,
                    "result": result,
                    "items": result.total_items
                })
            else:
                print(f"  ✗ No items extracted")
                failed_units.append({
                    "source_id": unit.source_id,
                    "reason": "No items returned"
                })
                
        except Exception as e:
            print(f"  ✗ Extraction failed: {str(e)[:200]}")
            failed_units.append({
                "source_id": unit.source_id,
                "reason": str(e)[:500]
            })
    
    # Report results
    print("\n" + "=" * 80)
    print("RECOVERY RESULTS")
    print("=" * 80)
    print(f"Successful: {len(all_extracted)}/{len(target_units)}")
    print(f"Failed: {len(failed_units)}/{len(target_units)}")
    
    if all_extracted:
        print("\n✓ Successfully extracted:")
        for item in all_extracted:
            print(f"  {item['source_id']}: {item['items']} knowledge items")
    
    if failed_units:
        print("\n✗ Failed units:")
        for item in failed_units:
            print(f"  {item['source_id']}: {item['reason'][:100]}")
    
    # Save recovery report
    output_dir = artifact_dir / "validation_20261101_143618"
    report_path = output_dir / f"recovery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "recovery_timestamp": datetime.now().isoformat(),
            "target_units": target_unit_ids,
            "successful_count": len(all_extracted),
            "failed_count": len(failed_units),
            "successful_extractions": [
                {
                    "source_id": item['source_id'],
                    "items_extracted": item['items']
                }
                for item in all_extracted
            ],
            "failed_extractions": failed_units,
            "notes": "Attempted single-unit extraction with reduced token limits"
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nRecovery report saved to: {report_path.name}")
    
    # If any succeeded, save the extracted knowledge
    if all_extracted:
        for item in all_extracted:
            knowledge_path = output_dir / f"recovered_{item['source_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(knowledge_path, 'w', encoding='utf-8') as f:
                json.dump(item['result'].model_dump(), f, indent=2, ensure_ascii=False)
            print(f"  Saved: {knowledge_path.name}")
    
    return 1 if failed_units else 0

if __name__ == "__main__":
    sys.exit(main())
