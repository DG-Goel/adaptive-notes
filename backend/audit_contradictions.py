#!/usr/bin/env python3
"""
Manual audit of all contradicted claims.

Loads source units, knowledge items, and verification results to inspect
each CONTRADICTED claim against its actual source text and classify the issue.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument

def load_json(path: Path):
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def truncate_text(text: str, max_len: int = 200) -> str:
    """Truncate text for display, handling unicode"""
    # Replace problematic unicode characters
    text = text.replace('\u2192', '->')  # → arrow
    text = text.replace('\u2265', '>=')  # ≥
    text = text.replace('\u2264', '<=')  # ≤
    text = text.encode('ascii', errors='replace').decode('ascii')
    
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."

def main():
    print("=" * 100)
    print("MANUAL CONTRADICTION AUDIT")
    print("=" * 100)
    print()
    
    # Load artifacts
    artifact_dir = Path("data/output/java_transcript_validation")
    
    print("Loading artifacts...")
    source_doc = SourceDocument(**load_json(artifact_dir / "source_units_20261030_185308.json"))
    knowledge_doc = KnowledgeDocument(**load_json(artifact_dir / "knowledge_20261030_185308.json"))
    verification = load_json(artifact_dir / "validation_20261030_231138" / "semantic_verification_20261030_231138.json")
    
    # Build source lookup
    source_map = {unit.source_id: unit for unit in source_doc.source_units}
    
    # Build knowledge lookup
    knowledge_map = {}
    for item in knowledge_doc.get_all_items():
        knowledge_map[item.knowledge_id] = item
    
    # Get all contradicted claims
    contradicted = [v for v in verification['claim_verifications'] if v['verification_status']['status'] == 'CONTRADICTED']
    
    print(f"Total contradicted claims: {len(contradicted)}")
    print()
    
    # Categories for classification
    categories = {
        'ENTITY_EXTRACTION_ERROR': [],  # Imperative verbs, code identifiers treated as entities
        'NUMERIC_FORMAT_MISMATCH': [],  # "100,000" vs "100000", etc.
        'INSUFFICIENT_SOURCE_CONTEXT': [],  # Claim needs broader context than source unit
        'GENUINE_CONTRADICTION': [],  # Actually wrong information
        'CODE_IDENTIFIER_MISMATCH': [],  # Java keywords, class names, method names
        'PARTIAL_MATCH': [],  # Claim partially correct but has additions/modifications
    }
    
    print("=" * 100)
    print("DETAILED AUDIT")
    print("=" * 100)
    print()
    
    for idx, claim_verification in enumerate(contradicted, 1):
        knowledge_id = claim_verification['knowledge_id']
        knowledge_type = claim_verification['knowledge_type']
        claim_text = claim_verification['claim_text']
        source_unit_ids = claim_verification['source_unit_ids']
        reason = claim_verification['verification_status']['reason']
        
        # Get source text
        source_texts = []
        for source_id in source_unit_ids:
            if source_id in source_map:
                source_texts.append(source_map[source_id].text)
        source_full_text = " ".join(source_texts)
        
        print(f"[{idx}/{len(contradicted)}] {knowledge_id} ({knowledge_type})")
        print(f"  Claim: {truncate_text(claim_text, 150)}")
        print(f"  Source IDs: {source_unit_ids}")
        print(f"  Verifier Reason: {reason}")
        print(f"  Source Text: {truncate_text(source_full_text, 200)}")
        
        # Manual classification based on patterns
        category = None
        classification_reason = ""
        
        # Check for entity mismatches with imperative verbs or code
        if "Entity mismatch" in reason:
            claimed_entities = []
            # Extract entities from reason
            if "claimed entities [" in reason:
                start = reason.index("claimed entities [") + 18
                end = reason.index("]", start)
                entities_str = reason[start:end]
                claimed_entities = [e.strip().strip("'") for e in entities_str.split(",")]
            
            # Check if these are imperative verbs (procedures)
            imperative_verbs = {
                'Accept', 'Download', 'Double', 'Click', 'Install', 'Enter', 'Finish', 'Move',
                'Open', 'Ensure', 'Project', 'Next', 'Create', 'Set', 'Run', 'Select', 'Date',
                'Press', 'Tab', 'Use', 'Assign', 'Import', 'Call', 'Pass', 'System', 'Cast',
                'Perform', 'Right', 'Refactor', 'Rename', 'Type', 'Store', 'Identify', 'Read',
                'Compute', 'Apply', 'Format', 'Remove', 'Delete', 'Reformat', 'Declare', 'Write',
                'Follow', 'Provide', 'Add', 'Prompt', 'Convert', 'Echo', 'Start', 'Place', 'Close',
                'Keep', 'Extract', 'Check', 'If', 'Otherwise', 'While', 'Instantiate', 'Continue'
            }
            
            # Check if entities are Java/code keywords
            java_keywords = {
                'String', 'Scanner', 'System', 'Arrays', 'Main', 'Integer', 'Double', 'Boolean',
                'Array', 'Object', 'Class', 'Method', 'Function', 'Variable', 'Type', 'Value'
            }
            
            if any(e in imperative_verbs for e in claimed_entities):
                category = 'ENTITY_EXTRACTION_ERROR'
                classification_reason = f"Imperative verbs treated as entities: {', '.join(e for e in claimed_entities if e in imperative_verbs)}"
            elif any(e in java_keywords for e in claimed_entities):
                category = 'CODE_IDENTIFIER_MISMATCH'
                classification_reason = f"Java keywords/identifiers: {', '.join(e for e in claimed_entities if e in java_keywords)}"
            else:
                # Check if entities appear in lowercased source (may be case issues)
                source_lower = source_full_text.lower()
                claim_lower = claim_text.lower()
                missing_in_source = []
                found_in_source = []
                for e in claimed_entities:
                    if e.lower() in source_lower:
                        found_in_source.append(e)
                    else:
                        missing_in_source.append(e)
                
                if len(found_in_source) > len(missing_in_source):
                    category = 'ENTITY_EXTRACTION_ERROR'
                    classification_reason = f"Case-sensitivity issue: {', '.join(found_in_source)} found in lowercase"
                elif len(missing_in_source) > 0 and len(missing_in_source) <= 2:
                    # Check if it's part of paraphrase
                    if any(word in source_full_text for word in claim_text.split()):
                        category = 'PARTIAL_MATCH'
                        classification_reason = f"Entities {', '.join(missing_in_source)} not in source but claim has content overlap"
                    else:
                        category = 'GENUINE_CONTRADICTION'
                        classification_reason = f"Entities {', '.join(missing_in_source)} genuinely not in source"
                else:
                    category = 'GENUINE_CONTRADICTION'
                    classification_reason = f"Multiple entities not found: {', '.join(missing_in_source)}"
        
        # Check for numeric contradictions
        elif "Numeric contradiction" in reason:
            # Extract numbers
            if "claimed [" in reason and "but source has [" in reason:
                claimed_nums_start = reason.index("claimed [") + 9
                claimed_nums_end = reason.index("]", claimed_nums_start)
                claimed_nums = reason[claimed_nums_start:claimed_nums_end].split(", ")
                claimed_nums = [n.strip().strip("'") for n in claimed_nums]
                
                source_nums_start = reason.index("but source has [") + 16
                source_nums_end = reason.index("]", source_nums_start)
                source_nums = reason[source_nums_start:source_nums_end].split(", ")
                source_nums = [n.strip().strip("'") for n in source_nums]
                
                # Check for format differences (commas in numbers)
                claimed_normalized = [n.replace(',', '') for n in claimed_nums]
                source_normalized = [n.replace(',', '') for n in source_nums]
                
                if set(claimed_normalized).issubset(set(source_normalized)):
                    category = 'NUMERIC_FORMAT_MISMATCH'
                    classification_reason = f"Format difference: {claimed_nums} vs {source_nums} (semantically same)"
                else:
                    # Check if numbers are in reasonable range/context
                    # Some may be array indices, others actual values
                    if knowledge_type == 'example':
                        # Examples might have synthetic values
                        category = 'PARTIAL_MATCH'
                        classification_reason = f"Example uses {claimed_nums} but source shows {source_nums} - may be illustrative"
                    else:
                        category = 'GENUINE_CONTRADICTION'
                        classification_reason = f"Numbers {claimed_nums} contradict source {source_nums}"
        
        # If still no category, mark as needing review
        if category is None:
            category = 'INSUFFICIENT_SOURCE_CONTEXT'
            classification_reason = "Requires manual review - reason unclear"
        
        categories[category].append({
            'knowledge_id': knowledge_id,
            'knowledge_type': knowledge_type,
            'claim': claim_text,
            'source_ids': source_unit_ids,
            'source_text': source_full_text,
            'verifier_reason': reason,
            'classification_reason': classification_reason
        })
        
        print(f"  CLASSIFICATION: {category}")
        print(f"  Reason: {classification_reason}")
        print()
    
    # Summary
    print("=" * 100)
    print("AUDIT SUMMARY")
    print("=" * 100)
    print()
    
    for category, items in categories.items():
        if items:
            print(f"{category}: {len(items)}")
            for item in items[:3]:  # Show first 3 of each
                print(f"  - {item['knowledge_id']}: {truncate_text(item['claim'], 80)}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more")
            print()
    
    # Calculate breakdown
    total = sum(len(items) for items in categories.values())
    print(f"TOTAL: {total}")
    print()
    
    false_positives = (
        len(categories['ENTITY_EXTRACTION_ERROR']) +
        len(categories['NUMERIC_FORMAT_MISMATCH']) +
        len(categories['CODE_IDENTIFIER_MISMATCH'])
    )
    
    genuine_issues = len(categories['GENUINE_CONTRADICTION'])
    needs_review = (
        len(categories['INSUFFICIENT_SOURCE_CONTEXT']) +
        len(categories['PARTIAL_MATCH'])
    )
    
    print(f"Verifier False Positives: {false_positives} ({false_positives/total*100:.1f}%)")
    print(f"Genuine Contradictions: {genuine_issues} ({genuine_issues/total*100:.1f}%)")
    print(f"Needs Review: {needs_review} ({needs_review/total*100:.1f}%)")
    print()
    
    # Save detailed audit
    audit_report = {
        'total_contradicted': total,
        'categories': {k: len(v) for k, v in categories.items()},
        'breakdown': {
            'false_positives': false_positives,
            'genuine_issues': genuine_issues,
            'needs_review': needs_review
        },
        'detailed_findings': categories
    }
    
    output_path = artifact_dir / "validation_20261030_231138" / "contradiction_audit.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)
    
    print(f"Detailed audit saved to: {output_path}")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
