"""
Apply corrections for confirmed genuine errors:
- FCT_0313: Remove hallucinated fact about byte range 127
- EXM_0215: Remove or generalize the unsupported casting example
"""

import json
from pathlib import Path
from datetime import datetime

def load_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.load(f)

def save_json(data, path, encoding='utf-8'):
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def apply_corrections(validation_dir):
    """Apply corrections to knowledge_corrected.json"""
    knowledge_path = validation_dir / 'knowledge_corrected.json'
    
    print("Loading knowledge...")
    knowledge = load_json(knowledge_path)
    
    # Track removals
    removed_items = []
    
    # 1. Remove FCT_0313 (hallucinated byte range fact)
    print("\n1. Removing FCT_0313 (hallucinated fact)...")
    original_facts_count = len(knowledge['facts'])
    knowledge['facts'] = [f for f in knowledge['facts'] if f['knowledge_id'] != 'FCT_0313']
    if len(knowledge['facts']) < original_facts_count:
        removed_items.append('FCT_0313')
        print(f"   ✓ Removed FCT_0313 from facts ({original_facts_count} → {len(knowledge['facts'])})")
    else:
        print(f"   ⚠ FCT_0313 not found in facts")
    
    # 2. Remove EXM_0215 (unsupported casting example with specific numbers)
    print("\n2. Removing EXM_0215 (unsupported example)...")
    original_examples_count = len(knowledge['examples'])
    knowledge['examples'] = [e for e in knowledge['examples'] if e['knowledge_id'] != 'EXM_0215']
    if len(knowledge['examples']) < original_examples_count:
        removed_items.append('EXM_0215')
        print(f"   ✓ Removed EXM_0215 from examples ({original_examples_count} → {len(knowledge['examples'])})")
    else:
        print(f"   ⚠ EXM_0215 not found in examples")
    
    # Update total count
    old_total = knowledge['total_items']
    knowledge['total_items'] = (
        len(knowledge.get('concepts', [])) +
        len(knowledge.get('definitions', [])) +
        len(knowledge.get('explanations', [])) +
        len(knowledge.get('examples', [])) +
        len(knowledge.get('facts', [])) +
        len(knowledge.get('formulas', [])) +
        len(knowledge.get('procedures', [])) +
        len(knowledge.get('relationships', []))
    )
    
    print(f"\n3. Updated total_items: {old_total} → {knowledge['total_items']}")
    
    # Save corrected knowledge
    output_path = validation_dir / 'knowledge_corrected_v2.json'
    print(f"\n4. Saving corrected knowledge to: {output_path}")
    save_json(knowledge, output_path)
    
    # Create correction report
    report = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "validation_dir": str(validation_dir),
        "corrections_applied": [
            {
                "knowledge_id": "FCT_0313",
                "knowledge_type": "fact",
                "action": "removed",
                "reason": "Hallucinated content - mentions '127' not in source T0033",
                "original_claim": "byte range is -128 to 127"
            },
            {
                "knowledge_id": "EXM_0215",
                "knowledge_type": "example",
                "action": "removed",
                "reason": "Unsupported example - (double)5 / 2 not found in source T0024",
                "original_claim": "double result = (double)5 / 2; // result is 2.5"
            }
        ],
        "items_removed": removed_items,
        "old_total_items": old_total,
        "new_total_items": knowledge['total_items'],
        "items_changed": old_total - knowledge['total_items']
    }
    
    report_path = validation_dir / 'corrections_applied.json'
    save_json(report, report_path)
    print(f"5. Correction report saved to: {report_path}")
    
    return report

if __name__ == "__main__":
    validation_dir = Path("data/output/complete_e2e_validation/validation_20261101_174430")
    
    print("=" * 80)
    print("APPLYING QUALITY CORRECTIONS")
    print("=" * 80)
    
    report = apply_corrections(validation_dir)
    
    print("\n" + "=" * 80)
    print("CORRECTION SUMMARY")
    print("=" * 80)
    print(f"Items removed: {len(report['items_removed'])}")
    print(f"Total items: {report['old_total_items']} → {report['new_total_items']}")
    print("\nRemoved items:")
    for item in report['corrections_applied']:
        print(f"  - {item['knowledge_id']} ({item['knowledge_type']}): {item['reason']}")
    print("=" * 80)
