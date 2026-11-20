"""
Run semantic verification on corrected knowledge (473 items)
"""

import json
from pathlib import Path
from datetime import datetime

from app.models.knowledge import KnowledgeDocument
from app.models.source import SourceDocument, SourceUnit
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier

def load_knowledge(path: Path) -> KnowledgeDocument:
    """Load knowledge as Pydantic model"""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return KnowledgeDocument(**data)

def load_source_document(path: Path) -> SourceDocument:
    """Load source document as Pydantic model"""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert to SourceDocument with SourceUnit objects
    source_units = []
    for unit_data in data.get('source_units', []):
        source_units.append(SourceUnit(**unit_data))
    
    return SourceDocument(
        document_id=data.get('document_id', 'JAVA'),
        filename=data.get('filename', 'unknown'),
        page_count=data.get('page_count'),
        source_units=source_units
    )

def save_json(data, path: Path):
    """Save JSON with proper encoding"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("=" * 80)
    print("SEMANTIC VERIFICATION OF CORRECTED KNOWLEDGE")
    print("=" * 80)
    
    # Paths
    validation_dir = Path("data/output/complete_e2e_validation/validation_20261101_174430")
    knowledge_path = validation_dir / "knowledge_corrected_v2.json"
    source_units_path = validation_dir / "source_units.json"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/output/semantic_verification_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nInput: {knowledge_path}")
    print(f"Output: {output_dir}")
    
    # Load data
    print("\n1. Loading corrected knowledge (473 items)...")
    knowledge = load_knowledge(knowledge_path)
    print(f"   Total items: {knowledge.total_items}")
    
    print("\n2. Loading source document...")
    source_doc = load_source_document(source_units_path)
    print(f"   Source units: {len(source_doc.source_units)}")
    
    # Verify FCT_0313 and EXM_0215 are absent
    print("\n3. Verifying removed items are absent...")
    all_ids = set()
    for item in knowledge.concepts:
        all_ids.add(item.knowledge_id)
    for item in knowledge.definitions:
        all_ids.add(item.knowledge_id)
    for item in knowledge.explanations:
        all_ids.add(item.knowledge_id)
    for item in knowledge.examples:
        all_ids.add(item.knowledge_id)
    for item in knowledge.facts:
        all_ids.add(item.knowledge_id)
    for item in knowledge.formulas:
        all_ids.add(item.knowledge_id)
    for item in knowledge.procedures:
        all_ids.add(item.knowledge_id)
    for item in knowledge.relationships:
        all_ids.add(item.knowledge_id)
    
    if 'FCT_0313' in all_ids:
        print("   X ERROR: FCT_0313 still present!")
    else:
        print("   OK: FCT_0313 absent (removed)")
    
    if 'EXM_0215' in all_ids:
        print("   X ERROR: EXM_0215 still present!")
    else:
        print("   OK: EXM_0215 absent (removed)")
    
    # Run semantic verification
    print("\n4. Running semantic verification...")
    verifier = DeterministicSemanticVerifier(verbose=True)
    
    try:
        report = verifier.verify(
            knowledge_doc=knowledge,
            source_doc=source_doc
        )
        
        print(f"\n   OK: Verification complete")
        print(f"     Total items verified: {len(report.claim_verifications)}")
        
        # Save full report
        save_json(report.model_dump(), output_dir / "semantic_verification_report.json")
        
        # Analyze by status
        by_status = {
            'SUPPORTED': [],
            'UNSUPPORTED': [],
            'CONTRADICTED': [],
            'INCONCLUSIVE': []
        }
        
        for verification in report.claim_verifications:
            status = verification.verification_status.status
            by_status[status].append(verification)
        
        # Summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total items: {len(report.claim_verifications)}")
        print(f"Supported: {len(by_status['SUPPORTED'])} ({len(by_status['SUPPORTED'])/len(report.claim_verifications)*100:.1f}%)")
        print(f"Unsupported: {len(by_status['UNSUPPORTED'])} ({len(by_status['UNSUPPORTED'])/len(report.claim_verifications)*100:.1f}%)")
        print(f"Contradicted: {len(by_status['CONTRADICTED'])} ({len(by_status['CONTRADICTED'])/len(report.claim_verifications)*100:.1f}%)")
        print(f"Inconclusive: {len(by_status['INCONCLUSIVE'])} ({len(by_status['INCONCLUSIVE'])/len(report.claim_verifications)*100:.1f}%)")
        print(f"\nSupport rate: {report.support_rate*100:.1f}%")
        
        # Non-supported claims
        non_supported = []
        non_supported.extend(by_status['UNSUPPORTED'])
        non_supported.extend(by_status['CONTRADICTED'])
        non_supported.extend(by_status['INCONCLUSIVE'])
        
        if non_supported:
            print(f"\n{'=' * 80}")
            print(f"NON-SUPPORTED CLAIMS: {len(non_supported)}")
            print("=" * 80)
            
            for verification in non_supported:
                # Handle Unicode characters in claim text
                claim_text = verification.claim_text.encode('ascii', 'replace').decode('ascii')
                print(f"\n{verification.knowledge_id} ({verification.knowledge_type.upper()}) - {verification.verification_status.status}")
                print(f"  Claim: {claim_text[:100]}...")
                print(f"  Sources: {verification.source_unit_ids}")
                if verification.verification_status.reason:
                    reason = verification.verification_status.reason.encode('ascii', 'replace').decode('ascii')
                    print(f"  Reason: {reason}")
        
        # Save detailed non-supported list
        non_supported_data = {
            'timestamp': timestamp,
            'total_non_supported': len(non_supported),
            'unsupported': [v.model_dump() for v in by_status['UNSUPPORTED']],
            'contradicted': [v.model_dump() for v in by_status['CONTRADICTED']],
            'inconclusive': [v.model_dump() for v in by_status['INCONCLUSIVE']]
        }
        save_json(non_supported_data, output_dir / "non_supported_claims.json")
        
        # Comparison with previous run
        print(f"\n{'=' * 80}")
        print("COMPARISON WITH PREVIOUS RUN (475 items)")
        print("=" * 80)
        
        previous_report_path = validation_dir / "semantic_verification.json"
        if previous_report_path.exists():
            with open(previous_report_path, encoding='utf-8') as f:
                previous = json.load(f)
            
            prev_supported = previous['claims_supported']
            prev_unsupported = previous['claims_unsupported']
            prev_contradicted = previous['claims_contradicted']
            prev_total = previous['total_claims_verified']
            
            print(f"Previous (475 items):")
            print(f"  Supported: {prev_supported} ({prev_supported/prev_total*100:.1f}%)")
            print(f"  Unsupported: {prev_unsupported} ({prev_unsupported/prev_total*100:.1f}%)")
            print(f"  Contradicted: {prev_contradicted} ({prev_contradicted/prev_total*100:.1f}%)")
            
            print(f"\nCurrent (473 items):")
            print(f"  Supported: {len(by_status['SUPPORTED'])} ({len(by_status['SUPPORTED'])/len(report.claim_verifications)*100:.1f}%)")
            print(f"  Unsupported: {len(by_status['UNSUPPORTED'])} ({len(by_status['UNSUPPORTED'])/len(report.claim_verifications)*100:.1f}%)")
            print(f"  Contradicted: {len(by_status['CONTRADICTED'])} ({len(by_status['CONTRADICTED'])/len(report.claim_verifications)*100:.1f}%)")
            
            print(f"\nChange:")
            print(f"  Total items: {prev_total} -> {len(report.claim_verifications)} ({len(report.claim_verifications) - prev_total:+d})")
            print(f"  Supported: {prev_supported} -> {len(by_status['SUPPORTED'])} ({len(by_status['SUPPORTED']) - prev_supported:+d})")
            print(f"  Contradicted: {prev_contradicted} -> {len(by_status['CONTRADICTED'])} ({len(by_status['CONTRADICTED']) - prev_contradicted:+d})")
        
        print("=" * 80)
        print(f"\nReports saved to: {output_dir}")
        
        # Exit code based on results
        if len(by_status['CONTRADICTED']) > 8:  # Allow some false positives
            print(f"\nWARNING: {len(by_status['CONTRADICTED'])} contradictions detected")
            return 1
        
        return 0
        
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nX FAILED: {error_msg}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
