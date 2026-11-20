#!/usr/bin/env python3
"""Analyze remaining contradictions after verifier improvements."""

import json
from pathlib import Path

def main():
    verification_path = Path("data/output/java_transcript_validation/validation_20261101_140531/semantic_verification_20261101_140531.json")
    
    with open(verification_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    contradicted = [v for v in data['claim_verifications'] if v['verification_status']['status'] == 'CONTRADICTED']
    
    print(f"Total contradicted claims: {len(contradicted)}")
    print("=" * 80)
    
    # Group by reason type
    numeric_contradictions = []
    entity_contradictions = []
    other_contradictions = []
    
    for claim in contradicted:
        reason = claim['verification_status']['reason']
        if 'Numeric contradiction' in reason:
            numeric_contradictions.append(claim)
        elif 'Entity mismatch' in reason:
            entity_contradictions.append(claim)
        else:
            other_contradictions.append(claim)
    
    print(f"\nNumeric contradictions: {len(numeric_contradictions)}")
    print(f"Entity contradictions: {len(entity_contradictions)}")
    print(f"Other contradictions: {len(other_contradictions)}")
    print()
    
    # Analyze numeric contradictions
    print("=" * 80)
    print("NUMERIC CONTRADICTIONS")
    print("=" * 80)
    
    for claim in numeric_contradictions[:10]:  # First 10
        print(f"\n{claim['knowledge_id']} ({claim['knowledge_type']}):")
        print(f"Claim: {claim['claim_text'][:150]}...")
        print(f"Reason: {claim['verification_status']['reason']}")
        print(f"Source IDs: {claim['source_unit_ids']}")
        
        # Show numeric details
        num_ver = claim.get('numeric_verification', {})
        print(f"  Claimed: {num_ver.get('claimed_numbers', [])}")
        print(f"  Source: {num_ver.get('source_numbers', [])[:20]}")  # First 20
    
    # Analyze entity contradictions
    if entity_contradictions:
        print("\n" + "=" * 80)
        print("ENTITY CONTRADICTIONS")
        print("=" * 80)
        
        for claim in entity_contradictions:
            print(f"\n{claim['knowledge_id']} ({claim['knowledge_type']}):")
            print(f"Claim: {claim['claim_text'][:150]}...")
            print(f"Reason: {claim['verification_status']['reason']}")
            
            # Show entity details
            ent_ver = claim.get('entity_verification', {})
            print(f"  Claimed: {ent_ver.get('claimed_entities', [])}")
            print(f"  Source: {ent_ver.get('source_entities', [])[:20]}")

if __name__ == "__main__":
    main()
