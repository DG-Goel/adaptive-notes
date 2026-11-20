#!/usr/bin/env python3
"""
Apply provenance corrections to knowledge extraction artifacts.

Corrections identified in manual provenance audit:
- EXP_0303: Add T0033 to source_unit_ids (currently only has T0032)
- EXM_0215: Change source_unit_ids from T0022 to T0024
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def apply_corrections(knowledge_path: Path) -> Dict[str, Any]:
    """
    Apply provenance corrections to a knowledge JSON file.
    
    Returns audit record of changes made.
    """
    print(f"Loading knowledge from: {knowledge_path}")
    
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        knowledge_doc = json.load(f)
    
    changes = []
    
    # Correction 1: EXP_0303 - Add T0033 to source_unit_ids
    for exp in knowledge_doc.get('explanations', []):
        if exp['knowledge_id'] == 'EXP_0303':
            old_sources = exp['source_unit_ids'].copy()
            if 'T0033' not in exp['source_unit_ids']:
                exp['source_unit_ids'].append('T0033')
                exp['source_unit_ids'].sort()  # Keep sorted
                changes.append({
                    'knowledge_id': 'EXP_0303',
                    'knowledge_type': 'explanation',
                    'field': 'source_unit_ids',
                    'old_value': old_sources,
                    'new_value': exp['source_unit_ids'],
                    'reason': 'Missing T0033 reference for "30 years" mention'
                })
                print(f"✓ Corrected EXP_0303: {old_sources} → {exp['source_unit_ids']}")
    
    # Correction 2: EXM_0215 - Change T0022 to T0024
    for exm in knowledge_doc.get('examples', []):
        if exm['knowledge_id'] == 'EXM_0215':
            old_sources = exm['source_unit_ids'].copy()
            if 'T0022' in exm['source_unit_ids']:
                exm['source_unit_ids'] = ['T0024' if sid == 'T0022' else sid 
                                           for sid in exm['source_unit_ids']]
                changes.append({
                    'knowledge_id': 'EXM_0215',
                    'knowledge_type': 'example',
                    'field': 'source_unit_ids',
                    'old_value': old_sources,
                    'new_value': exm['source_unit_ids'],
                    'reason': 'Incorrect source - should reference T0024 (casting discussion) not T0022 (constants)'
                })
                print(f"✓ Corrected EXM_0215: {old_sources} → {exm['source_unit_ids']}")
    
    if not changes:
        print("⚠ No corrections applied - items not found or already corrected")
        return {
            'timestamp': datetime.now().isoformat(),
            'knowledge_file': str(knowledge_path),
            'corrections_applied': 0,
            'changes': []
        }
    
    # Save corrected knowledge
    backup_path = knowledge_path.with_suffix('.backup.json')
    print(f"\nBacking up original to: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc, f, indent=2, ensure_ascii=False)
    
    print(f"Saving corrected knowledge to: {knowledge_path}")
    with open(knowledge_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc, f, indent=2, ensure_ascii=False)
    
    # Create audit record
    audit = {
        'timestamp': datetime.now().isoformat(),
        'knowledge_file': str(knowledge_path),
        'backup_file': str(backup_path),
        'corrections_applied': len(changes),
        'changes': changes
    }
    
    audit_path = knowledge_path.parent / f'provenance_corrections_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    print(f"Saving audit record to: {audit_path}")
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    
    return audit


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_provenance_corrections.py <knowledge_json_path>")
        print("\nApplies provenance corrections:")
        print("  - EXP_0303: Add T0033 to source_unit_ids")
        print("  - EXM_0215: Change source_unit_ids from T0022 to T0024")
        sys.exit(1)
    
    knowledge_path = Path(sys.argv[1])
    
    if not knowledge_path.exists():
        print(f"Error: File not found: {knowledge_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("PROVENANCE CORRECTION SCRIPT")
    print("=" * 70)
    print()
    
    audit = apply_corrections(knowledge_path)
    
    print()
    print("=" * 70)
    print(f"SUMMARY: {audit['corrections_applied']} corrections applied")
    print("=" * 70)
    
    for change in audit['changes']:
        print(f"\n{change['knowledge_id']} ({change['knowledge_type']}):")
        print(f"  Old: {change['old_value']}")
        print(f"  New: {change['new_value']}")
        print(f"  Reason: {change['reason']}")
    
    return 0 if audit['corrections_applied'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
