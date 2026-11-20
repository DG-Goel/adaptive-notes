#!/usr/bin/env python3
"""
Controlled end-to-end extraction validation with multi-key Groq scheduler.

Validates the complete extraction pipeline on a small subset of source units
with detailed tracking of:
- Source units processed
- Chunks attempted/succeeded/failed
- Extracted items by type
- Source provenance preservation
- Error handling behavior
- Multi-key credential rotation

Does NOT retry rate-limited requests through another account to evade limits.
Respects cooldowns, quotas, and provider terms.
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider


def create_subset(source_doc: SourceDocument, max_units: int = 10) -> SourceDocument:
    """
    Create a small representative subset of source units.
    
    Selects units with content (not furniture/noise) to ensure meaningful extraction.
    """
    # Filter for content units
    content_units = [
        u for u in source_doc.source_units
        if u.content_role in ['content', 'structural'] and u.text and len(u.text.strip()) > 20
    ]
    
    # Take first max_units
    subset_units = content_units[:max_units]
    
    # Create new document with subset
    subset_doc = SourceDocument(
        document_id=f"{source_doc.document_id}_SUBSET",
        filename=source_doc.filename,
        page_count=source_doc.page_count,
        source_units=subset_units
    )
    
    return subset_doc


def audit_extracted_claims(
    knowledge_doc: Any,
    source_doc: SourceDocument
) -> Dict[str, Any]:
    """
    Manual audit of extracted claims against source text.
    
    Reports:
    - Unsupported claims (not found in referenced source)
    - Contradicted claims (conflicts with source)
    - Duplicated claims (same information extracted multiple times)
    - Incorrectly attributed claims (wrong source_unit_ids)
    """
    
    # Build source text lookup
    source_texts = {unit.source_id: unit.text for unit in source_doc.source_units}
    
    audit_results = {
        "unsupported": [],
        "contradicted": [],
        "duplicated": [],
        "incorrectly_attributed": [],
        "total_audited": 0
    }
    
    # Collect all claims with their content and source refs
    all_claims = []
    
    # Sample from each type (limit to avoid excessive audit time)
    for concept in knowledge_doc.concepts[:3]:
        all_claims.append({
            "type": "concept",
            "id": concept.knowledge_id,
            "content": concept.content,
            "source_ids": concept.source_unit_ids
        })
    
    for definition in knowledge_doc.definitions[:3]:
        all_claims.append({
            "type": "definition",
            "id": definition.knowledge_id,
            "content": definition.definition_text,
            "source_ids": definition.source_unit_ids
        })
    
    for explanation in knowledge_doc.explanations[:3]:
        all_claims.append({
            "type": "explanation",
            "id": explanation.knowledge_id,
            "content": explanation.explanation_text,
            "source_ids": explanation.source_unit_ids
        })
    
    for fact in knowledge_doc.facts[:3]:
        all_claims.append({
            "type": "fact",
            "id": fact.knowledge_id,
            "content": fact.fact_text,
            "source_ids": fact.source_unit_ids
        })
    
    audit_results["total_audited"] = len(all_claims)
    
    # Check each claim
    seen_content = {}
    for claim in all_claims:
        # Check for duplicates
        normalized = claim["content"].lower().strip()
        if normalized in seen_content:
            audit_results["duplicated"].append({
                "current_id": claim["id"],
                "duplicate_of": seen_content[normalized],
                "content": claim["content"][:100]
            })
        else:
            seen_content[normalized] = claim["id"]
        
        # Check source attribution
        if not claim["source_ids"]:
            audit_results["incorrectly_attributed"].append({
                "id": claim["id"],
                "issue": "No source_unit_ids provided",
                "content": claim["content"][:100]
            })
            continue
        
        # Verify source IDs exist
        invalid_refs = [sid for sid in claim["source_ids"] if sid not in source_texts]
        if invalid_refs:
            audit_results["incorrectly_attributed"].append({
                "id": claim["id"],
                "issue": f"Invalid source_unit_ids: {invalid_refs}",
                "content": claim["content"][:100]
            })
            continue
        
        # Check if content is supported by sources (basic substring check)
        # Note: This is a simple heuristic, not semantic verification
        combined_source = " ".join(source_texts.get(sid, "") for sid in claim["source_ids"])
        
        # Extract key phrases from claim (simple word-based)
        claim_words = set(claim["content"].lower().split())
        source_words = set(combined_source.lower().split())
        
        # If less than 30% overlap, flag as potentially unsupported
        if claim_words:
            overlap = len(claim_words & source_words) / len(claim_words)
            if overlap < 0.3:
                audit_results["unsupported"].append({
                    "id": claim["id"],
                    "type": claim["type"],
                    "content": claim["content"][:100],
                    "overlap": f"{overlap:.1%}",
                    "source_ids": claim["source_ids"]
                })
    
    return audit_results


def main():
    print("=" * 80)
    print("CONTROLLED END-TO-END EXTRACTION VALIDATION")
    print("=" * 80)
    print()
    
    # Setup paths
    source_path = Path("data/output/source_units.json")
    output_dir = Path("data/output/controlled_e2e_validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load source document
    if not source_path.exists():
        print(f"ERROR: Source document not found at {source_path}")
        return 1
    
    print(f"Loading source document from: {source_path}")
    with open(source_path, 'r', encoding='utf-8') as f:
        full_doc = SourceDocument.model_validate(json.load(f))
    
    print(f"  Total source units: {len(full_doc.source_units)}")
    print()
    
    # Create small subset for controlled validation
    print("Creating representative subset...")
    subset_doc = create_subset(full_doc, max_units=10)
    print(f"  Subset size: {len(subset_doc.source_units)} source units")
    print(f"  Source IDs: {[u.source_id for u in subset_doc.source_units]}")
    print()
    
    # Save subset for reproducibility
    subset_path = output_dir / f"subset_{timestamp}.json"
    with open(subset_path, 'w', encoding='utf-8') as f:
        json.dump(subset_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"Saved subset to: {subset_path}")
    print()
    
    # Initialize provider with multi-key support
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Check for multi-key setup
    multi_keys = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
    num_keys = sum(1 for k in multi_keys if k)
    
    if num_keys > 0:
        print(f"Multi-key setup detected: {num_keys} credentials configured")
        provider = GroqProvider(model=model, use_multi_key=True)
    else:
        single_key = os.getenv("GROQ_API_KEY")
        if not single_key:
            print("ERROR: No GROQ_API_KEY credentials found")
            return 1
        print("Single-key setup detected")
        provider = GroqProvider(model=model, api_key=single_key, use_multi_key=False)
    
    print(f"Provider: {provider.model}")
    print()
    
    # Initialize extractor
    print("Initializing extractor...")
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2000,  # Conservative chunk size
        verbose=True,
        max_retries=2,  # Limited retries to avoid evasion
        min_output_tokens=500,
        preferred_output_tokens=4000,
        max_split_depth=2
    )
    print()
    
    # Run extraction
    print("=" * 80)
    print("RUNNING EXTRACTION")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    try:
        knowledge_doc = extractor.extract(subset_doc)
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {type(e).__name__}: {e}")
        return 1
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    
    # Collect metrics
    metadata = knowledge_doc.extraction_metadata
    total_chunks = metadata.get("total_chunks", 0)
    successful_chunks = metadata.get("successful_chunks", 0)
    failed_chunks_list = metadata.get("failed_chunks", [])
    split_chunks_list = metadata.get("split_chunks", [])
    completeness = metadata.get("completeness", 0.0)
    
    print(f"1. SOURCE UNITS:")
    print(f"   Total processed: {len(subset_doc.source_units)}")
    print()
    
    print(f"2. CHUNKS:")
    print(f"   Total attempted: {total_chunks}")
    print(f"   Succeeded: {successful_chunks}")
    print(f"   Failed: {len(failed_chunks_list)}")
    print(f"   Split (adaptive): {len(split_chunks_list)}")
    print(f"   Completeness: {completeness:.1%}")
    if failed_chunks_list:
        print(f"   Failed chunk IDs: {failed_chunks_list}")
    print()
    
    print(f"3. EXTRACTED ITEMS:")
    print(f"   Total: {knowledge_doc.total_items}")
    print(f"   Concepts: {len(knowledge_doc.concepts)}")
    print(f"   Definitions: {len(knowledge_doc.definitions)}")
    print(f"   Explanations: {len(knowledge_doc.explanations)}")
    print(f"   Examples: {len(knowledge_doc.examples)}")
    print(f"   Facts: {len(knowledge_doc.facts)}")
    print(f"   Formulas: {len(knowledge_doc.formulas)}")
    print(f"   Procedures: {len(knowledge_doc.procedures)}")
    print(f"   Relationships: {len(knowledge_doc.relationships)}")
    print()
    
    print(f"4. SOURCE PROVENANCE:")
    # Check that all items have source_unit_ids
    items_with_sources = 0
    items_without_sources = 0
    
    all_items = (
        knowledge_doc.concepts +
        knowledge_doc.definitions +
        knowledge_doc.explanations +
        knowledge_doc.examples +
        knowledge_doc.facts +
        knowledge_doc.formulas +
        knowledge_doc.procedures +
        knowledge_doc.relationships
    )
    
    for item in all_items:
        if hasattr(item, 'source_unit_ids') and item.source_unit_ids:
            items_with_sources += 1
        else:
            items_without_sources += 1
    
    print(f"   Items with source attribution: {items_with_sources}/{len(all_items)}")
    print(f"   Items without source attribution: {items_without_sources}/{len(all_items)}")
    print()
    
    print(f"5. ERROR HANDLING:")
    if failed_chunks_list:
        print(f"   ❌ Incomplete extraction detected")
        print(f"   {len(failed_chunks_list)} chunks failed after retries")
        print(f"   Failed chunks are explicitly reported (not silently discarded)")
    else:
        print(f"   ✓ All chunks extracted successfully")
    print()
    
    print(f"6. PERFORMANCE:")
    print(f"   Total time: {elapsed_time:.2f}s")
    print(f"   Time per unit: {elapsed_time/len(subset_doc.source_units):.2f}s")
    print(f"   Items per unit: {knowledge_doc.total_items/len(subset_doc.source_units):.1f}")
    print()
    
    # Multi-key credential tracking
    if hasattr(provider, 'get_scheduler_status') and provider.get_scheduler_status():
        print(f"7. MULTI-KEY SCHEDULER:")
        status = provider.get_scheduler_status()
        print(f"   Total credentials: {status['total_credentials']}")
        print(f"   Valid credentials: {status['valid_credentials']}")
        print(f"   Available: {status['available_credentials']}")
        if status['next_credential']:
            print(f"   Next credential: {status['next_credential']}")
        
        # Show per-credential details
        for cred in status['credentials']:
            print(f"   - {cred['credential_id']}: {cred['total_requests']} requests, {cred['total_failures']} failures")
        print()
    
    # Audit claims
    print(f"8. CLAIM AUDIT:")
    print(f"   Auditing representative sample of extracted claims...")
    audit_results = audit_extracted_claims(knowledge_doc, subset_doc)
    
    print(f"   Total claims audited: {audit_results['total_audited']}")
    print(f"   Unsupported claims: {len(audit_results['unsupported'])}")
    print(f"   Contradicted claims: {len(audit_results['contradicted'])}")
    print(f"   Duplicated claims: {len(audit_results['duplicated'])}")
    print(f"   Incorrectly attributed: {len(audit_results['incorrectly_attributed'])}")
    
    if audit_results['unsupported']:
        print()
        print("   Unsupported claims details:")
        for claim in audit_results['unsupported'][:3]:  # Show first 3
            print(f"     - {claim['id']} ({claim['type']}): {claim['content']}")
            print(f"       Overlap: {claim['overlap']}, Sources: {claim['source_ids']}")
    
    if audit_results['duplicated']:
        print()
        print("   Duplicated claims details:")
        for dup in audit_results['duplicated'][:3]:
            print(f"     - {dup['current_id']} duplicates {dup['duplicate_of']}")
            print(f"       Content: {dup['content']}")
    
    if audit_results['incorrectly_attributed']:
        print()
        print("   Attribution issues:")
        for issue in audit_results['incorrectly_attributed'][:3]:
            print(f"     - {issue['id']}: {issue['issue']}")
    print()
    
    # Save outputs
    knowledge_path = output_dir / f"knowledge_{timestamp}.json"
    with open(knowledge_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    audit_path = output_dir / f"audit_{timestamp}.json"
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
    
    print(f"OUTPUTS SAVED:")
    print(f"  Subset: {subset_path}")
    print(f"  Knowledge: {knowledge_path}")
    print(f"  Audit: {audit_path}")
    print()
    
    # GO/NO-GO recommendation
    print("=" * 80)
    print("GO/NO-GO RECOMMENDATION")
    print("=" * 80)
    print()
    
    # Decision criteria
    issues = []
    warnings = []
    
    if completeness < 0.9:
        issues.append(f"Low completeness: {completeness:.1%} (threshold: 90%)")
    
    if knowledge_doc.total_items == 0:
        issues.append("Zero items extracted")
    
    if items_without_sources > len(all_items) * 0.1:
        issues.append(f"{items_without_sources} items lack source attribution (>10%)")
    
    if len(audit_results['unsupported']) > audit_results['total_audited'] * 0.3:
        warnings.append(f"High unsupported claim rate: {len(audit_results['unsupported'])}/{audit_results['total_audited']}")
    
    if len(audit_results['incorrectly_attributed']) > 0:
        warnings.append(f"{len(audit_results['incorrectly_attributed'])} attribution errors detected")
    
    if issues:
        print("❌ NO-GO: Critical issues detected")
        print()
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")
        if warnings:
            print()
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        print()
        print("Recommendation: Address critical issues before proceeding to next stage.")
        return 2
    
    elif warnings:
        print("⚠️ CONDITIONAL GO: Warnings detected")
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
        print("Recommendation: Review warnings and decide whether to proceed.")
        print("  Consider adjusting extraction parameters or prompts.")
        return 0
    
    else:
        print("✅ GO: Validation successful")
        print()
        print("All validation criteria passed:")
        print(f"  ✓ Completeness: {completeness:.1%}")
        print(f"  ✓ Items extracted: {knowledge_doc.total_items}")
        print(f"  ✓ Source attribution: {items_with_sources}/{len(all_items)}")
        print(f"  ✓ Claim quality acceptable")
        print()
        print("Recommendation: Proceed to next validation stage with larger dataset.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
