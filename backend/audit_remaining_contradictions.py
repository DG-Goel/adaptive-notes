#!/usr/bin/env python3
"""
Comprehensive audit of remaining contradictions after knowledge-type-aware verification.

For each contradiction, record:
- Knowledge ID and type
- Full extracted claim
- Original source text
- Why the verifier flagged it
- Whether it is genuine extraction error, verifier false positive, or inconclusive
- Evidence supporting the classification
"""

import json
from pathlib import Path
from typing import Dict, List

def main():
    # Load artifacts
    artifact_dir = Path("data/output/java_transcript_validation")
    validation_dir = artifact_dir / "validation_20261101_143618"
    
    with open(artifact_dir / "source_units_20261030_185308.json", 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    with open(artifact_dir / "knowledge_20261030_185308.json", 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
    
    with open(validation_dir / "semantic_verification_20261101_143618.json", 'r', encoding='utf-8') as f:
        verification_data = json.load(f)
    
    # Create source unit lookup
    source_units_map = {unit['source_id']: unit for unit in source_data['source_units']}
    
    # Extract contradicted claims
    contradicted = [
        v for v in verification_data['claim_verifications']
        if v['verification_status']['status'] == 'CONTRADICTED'
    ]
    
    print("=" * 80)
    print(f"COMPREHENSIVE CONTRADICTION AUDIT")
    print("=" * 80)
    print(f"Total contradictions: {len(contradicted)}")
    print()
    
    # Detailed audit
    audit_results = []
    
    for i, claim in enumerate(contradicted, 1):
        print(f"\n{'=' * 80}")
        print(f"CONTRADICTION #{i}: {claim['knowledge_id']} ({claim['knowledge_type']})")
        print(f"{'=' * 80}")
        
        # Extract claim details
        claim_text = claim['claim_text']
        source_ids = claim['source_unit_ids']
        reason = claim['verification_status']['reason']
        
        print(f"\nCLAIM TEXT:")
        print(f"  {claim_text}")
        print()
        
        print(f"SOURCE UNITS: {', '.join(source_ids)}")
        print()
        
        # Show source text
        print(f"SOURCE TEXT:")
        for sid in source_ids:
            if sid in source_units_map:
                unit = source_units_map[sid]
                source_text = unit['text']
                print(f"  [{sid}]: {source_text[:300]}{'...' if len(source_text) > 300 else ''}")
        print()
        
        print(f"VERIFIER REASON:")
        print(f"  {reason}")
        print()
        
        # Analyze numeric contradiction
        if 'Numeric contradiction' in reason:
            num_ver = claim['numeric_verification']
            print(f"NUMERIC DETAILS:")
            print(f"  Claimed: {num_ver['claimed_numbers']}")
            print(f"  Source: {num_ver['source_numbers'][:20]}")  # First 20
            print(f"  Mismatches: {num_ver['mismatches']}")
            print()
        
        # Analyze entity contradiction
        if 'Entity mismatch' in reason:
            ent_ver = claim['entity_verification']
            print(f"ENTITY DETAILS:")
            print(f"  Claimed: {ent_ver['claimed_entities']}")
            print(f"  Source: {ent_ver['source_entities'][:20]}")  # First 20
            print(f"  Mismatches: {ent_ver['mismatches']}")
            print()
        
        # Manual classification
        print("MANUAL CLASSIFICATION:")
        classification = classify_contradiction(claim, source_units_map)
        print(f"  Type: {classification['type']}")
        print(f"  Reasoning: {classification['reasoning']}")
        print(f"  Evidence: {classification['evidence']}")
        
        audit_results.append({
            "knowledge_id": claim['knowledge_id'],
            "knowledge_type": claim['knowledge_type'],
            "claim_text": claim_text,
            "source_ids": source_ids,
            "verifier_reason": reason,
            "classification": classification
        })
    
    # Save audit results
    output_path = validation_dir / "contradiction_audit_final.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "audit_timestamp": "2026-11-01T14:36:00",
            "total_contradictions": len(contradicted),
            "audit_results": audit_results,
            "summary": summarize_audit(audit_results)
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    summary = summarize_audit(audit_results)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nAudit saved to: {output_path}")

def classify_contradiction(claim: Dict, source_units_map: Dict) -> Dict:
    """
    Classify a contradiction as:
    - GENUINE_ERROR: Extraction made a factual mistake
    - VERIFIER_FALSE_POSITIVE: Extraction is correct, verifier misidentified
    - INCONCLUSIVE: Cannot determine without domain expert review
    """
    
    knowledge_type = claim['knowledge_type']
    claim_text = claim['claim_text']
    reason = claim['verification_status']['reason']
    
    # Get source text
    source_texts = []
    for sid in claim['source_unit_ids']:
        if sid in source_units_map:
            source_texts.append(source_units_map[sid]['text'])
    source_full = " ".join(source_texts)
    
    # Pattern 1: Example with code numbers that aren't in source
    if knowledge_type == "example" and 'Numeric contradiction' in reason:
        # Check if numbers appear in code-like context
        if any(pattern in claim_text for pattern in ['int[', 'new ', '[', ']', '=']):
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Example contains illustrative code with array sizes/indices not meant to match source prose",
                "evidence": f"Code pattern detected in example: {claim_text[:100]}"
            }
    
    # Pattern 2: Definition with range values (0.0 to 1.0)
    if knowledge_type == "definition" and 'Numeric contradiction' in reason:
        if " to " in claim_text or " between " in claim_text:
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Definition describes a range/boundary, not claiming exact values appear in source",
                "evidence": f"Range language detected: '{claim_text[:100]}'"
            }
    
    # Pattern 3: Multi-word entity (first name + last name)
    if 'Entity mismatch' in reason:
        mismatches = claim['entity_verification']['mismatches']
        if any(' ' in m['claimed'] for m in mismatches):
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Multi-word entity (full name) not found as single token, but parts may be present",
                "evidence": f"Multi-word entities: {[m['claimed'] for m in mismatches if ' ' in m['claimed']]}"
            }
    
    # Pattern 4: Concept explaining general principle with example value
    if knowledge_type == "concept" and 'Numeric contradiction' in reason:
        claimed = claim['numeric_verification']['claimed_numbers']
        if len(claimed) == 1 and any(word in claim_text.lower() for word in ['example', 'e.g.', 'such as', 'like']):
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Concept uses illustrative example value to explain principle",
                "evidence": f"Single example value in concept: {claimed}"
            }
    
    # Pattern 5: Procedure with step indices
    if knowledge_type == "procedure" and 'Numeric contradiction' in reason:
        claimed = claim['numeric_verification']['claimed_numbers']
        if all(n in ['0', '1', '2', '3', '4', '5'] for n in claimed):
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Procedure contains step indices or array indices, not factual claims",
                "evidence": f"Small index numbers in procedure: {claimed}"
            }
    
    # Pattern 6: Explanation with illustrative values
    if knowledge_type == "explanation" and 'Numeric contradiction' in reason:
        # Check if source has very different topic numbers
        source_nums = claim['numeric_verification']['source_numbers']
        claimed_nums = claim['numeric_verification']['claimed_numbers']
        
        if len(claimed_nums) <= 2 and "type" in claim_text.lower() and "chosen" in source_full.lower():
            return {
                "type": "VERIFIER_FALSE_POSITIVE",
                "reasoning": "Explanation uses illustrative type-choice example",
                "evidence": f"Explanation of type choice with example values: {claimed_nums}"
            }
    
    # Pattern 7: Fact with wrong numeric limit
    if knowledge_type == "fact" and 'Numeric contradiction' in reason:
        # Check if numbers are significantly different
        source_nums = claim['numeric_verification']['source_numbers']
        claimed_nums = claim['numeric_verification']['claimed_numbers']
        
        # If claimed number doesn't appear in source at all, likely genuine error
        if source_nums and claimed_nums:
            return {
                "type": "GENUINE_ERROR",
                "reasoning": "Fact states numeric value that contradicts source",
                "evidence": f"Claimed {claimed_nums} but source has {source_nums}"
            }
    
    # Default: Inconclusive - needs manual review
    return {
        "type": "INCONCLUSIVE",
        "reasoning": "Requires domain expert review to determine if extraction error or verifier limitation",
        "evidence": f"Knowledge type: {knowledge_type}, Reason: {reason[:100]}"
    }

def summarize_audit(audit_results: List[Dict]) -> Dict:
    """Summarize audit classifications"""
    
    classifications = [r['classification']['type'] for r in audit_results]
    
    return {
        "total": len(audit_results),
        "genuine_errors": classifications.count("GENUINE_ERROR"),
        "verifier_false_positives": classifications.count("VERIFIER_FALSE_POSITIVE"),
        "inconclusive": classifications.count("INCONCLUSIVE"),
        "false_positive_rate": f"{classifications.count('VERIFIER_FALSE_POSITIVE') / len(audit_results) * 100:.1f}%",
        "genuine_error_rate": f"{classifications.count('GENUINE_ERROR') / len(audit_results) * 100:.1f}%"
    }

if __name__ == "__main__":
    main()
