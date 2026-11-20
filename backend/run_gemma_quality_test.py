"""
Quality test for Gemma 3 4B model.

Uses identical source units, prompt, and settings as granite4:micro test
to enable direct comparison of extraction quality.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from app.models.source import SourceDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import OllamaProvider
from app.analysis.analyzer import ContentAnalyzer


def select_test_content(source_file: Path, source_ids: list):
    """Load specific source units for testing"""
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    source_doc = SourceDocument(**data)
    
    # Filter to exact IDs requested
    selected_units = [
        unit for unit in source_doc.source_units
        if unit.source_id in source_ids
    ]
    
    # Sort by source_id to maintain order
    selected_units.sort(key=lambda u: u.source_id)
    
    # Create test document
    test_doc = SourceDocument(
        document_id=source_doc.document_id,
        filename=source_doc.filename,
        page_count=source_doc.page_count,
        source_units=selected_units
    )
    
    return test_doc


def detailed_claim_audit(knowledge_doc, source_doc):
    """
    Audit each claim against actual source text.
    
    Provides detailed assessment of:
    - Support: claim directly stated in source
    - Unsupported: claim not found or inferred beyond source
    - Provenance errors: wrong source IDs cited
    """
    print(f"\n{'='*80}")
    print(f"DETAILED CLAIM AUDIT")
    print(f"{'='*80}")
    
    # Build source text lookup
    source_texts = {unit.source_id: unit.text for unit in source_doc.source_units if unit.text}
    
    # Collect all items
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
    
    results = {
        "supported": [],
        "unsupported": [],
        "provenance_errors": []
    }
    
    for item in all_items:
        print(f"\n{'─'*80}")
        print(f"ID: {item.knowledge_id} | Type: {item.__class__.__name__}")
        
        # Display key content
        if hasattr(item, 'concept_name'):
            print(f"Concept: {item.concept_name}")
        elif hasattr(item, 'term'):
            print(f"Term: {item.term}")
        elif hasattr(item, 'topic'):
            print(f"Topic: {item.topic}")
        elif hasattr(item, 'exemplifies'):
            print(f"Exemplifies: {item.exemplifies}")
        elif hasattr(item, 'fact_text'):
            print(f"Fact: {item.fact_text}")
        elif hasattr(item, 'subject'):
            print(f"Relationship: {item.subject} → {item.object}")
        
        print(f"Content: {item.content[:150]}...")
        print(f"Cited sources: {item.source_unit_ids}")
        
        if not item.source_unit_ids:
            print(f"  ✗ NO SOURCE IDS PROVIDED")
            results["unsupported"].append({
                "id": item.knowledge_id,
                "reason": "No source IDs",
                "type": item.__class__.__name__
            })
            continue
        
        # Check each cited source
        found_support = False
        all_missing = True
        wrong_sources = []
        
        for src_id in item.source_unit_ids:
            if src_id not in source_texts:
                print(f"  ✗ {src_id}: NOT IN DOCUMENT")
                wrong_sources.append(src_id)
                continue
            
            all_missing = False
            src_text = source_texts[src_id]
            print(f"\n  Checking {src_id}:")
            print(f"    Source text: \"{src_text[:100]}...\"")
            
            # Manual verification based on type
            if hasattr(item, 'concept_name'):
                concept_name_lower = item.concept_name.lower()
                src_lower = src_text.lower()
                
                if concept_name_lower in src_lower:
                    # Check if there's actual description, not just mention
                    content_words = set(item.content.lower().split())
                    source_words = set(src_lower.split())
                    overlap = content_words & source_words
                    
                    if len(overlap) >= 5:
                        print(f"    ✓ SUPPORTED: Concept and description present ({len(overlap)} words)")
                        found_support = True
                    else:
                        print(f"    ~ Concept name present, but description not found ({len(overlap)} words)")
                else:
                    print(f"    ✗ Concept name not in source")
            
            elif hasattr(item, 'definition_text'):
                term_lower = item.term.lower()
                def_lower = item.definition_text.lower()
                src_lower = src_text.lower()
                
                if term_lower in src_lower:
                    # Check if definition text is also present
                    def_words = set(def_lower.split())
                    src_words = set(src_lower.split())
                    overlap = def_words & src_words
                    
                    if len(overlap) >= 5:
                        print(f"    ✓ SUPPORTED: Term and definition present")
                        found_support = True
                    else:
                        print(f"    ✗ Term present, but definition not found")
                else:
                    print(f"    ✗ Term not in source")
            
            elif hasattr(item, 'fact_text'):
                fact_words = set(item.fact_text.lower().split())
                src_words = set(src_text.lower().split())
                overlap = fact_words & src_words
                
                # For facts, need substantial overlap
                if len(overlap) >= 6:
                    print(f"    ✓ SUPPORTED: Fact verified ({len(overlap)} matching words)")
                    found_support = True
                else:
                    print(f"    ✗ Insufficient fact support ({len(overlap)} words)")
            
            elif hasattr(item, 'subject') and hasattr(item, 'object'):
                subject_lower = item.subject.lower()
                object_lower = item.object.lower()
                src_lower = src_text.lower()
                
                subject_present = subject_lower in src_lower
                object_present = object_lower in src_lower
                
                if subject_present and object_present:
                    print(f"    ✓ SUPPORTED: Both entities present")
                    found_support = True
                else:
                    print(f"    ✗ Subject: {subject_present}, Object: {object_present}")
            
            elif hasattr(item, 'explanation_text'):
                expl_words = set(item.explanation_text.lower().split())
                src_words = set(src_text.lower().split())
                overlap = expl_words & src_words
                
                if len(overlap) >= 7:
                    print(f"    ✓ SUPPORTED: Explanation verified ({len(overlap)} words)")
                    found_support = True
                else:
                    print(f"    ✗ Insufficient explanation support ({len(overlap)} words)")
            
            elif hasattr(item, 'example_text'):
                exm_words = set(item.example_text.lower().split())
                src_words = set(src_text.lower().split())
                overlap = exm_words & src_words
                
                if len(overlap) >= 5:
                    print(f"    ✓ SUPPORTED: Example verified ({len(overlap)} words)")
                    found_support = True
                else:
                    print(f"    ✗ Insufficient example support ({len(overlap)} words)")
        
        # Categorize
        if all_missing:
            print(f"\n  → UNSUPPORTED: All sources missing from document")
            results["unsupported"].append({
                "id": item.knowledge_id,
                "reason": "All sources missing",
                "type": item.__class__.__name__
            })
            results["provenance_errors"].append(item.knowledge_id)
        elif wrong_sources:
            print(f"\n  → PROVENANCE ERROR: Wrong source IDs: {wrong_sources}")
            results["provenance_errors"].append(item.knowledge_id)
            if not found_support:
                results["unsupported"].append({
                    "id": item.knowledge_id,
                    "reason": "Not found in cited sources",
                    "type": item.__class__.__name__
                })
        elif found_support:
            print(f"\n  → ✓ SUPPORTED AND VERIFIED")
            results["supported"].append(item.knowledge_id)
        else:
            print(f"\n  → UNSUPPORTED: Claim not found in cited sources")
            results["unsupported"].append({
                "id": item.knowledge_id,
                "reason": "Not in source text",
                "type": item.__class__.__name__
            })
    
    return results


def main():
    load_dotenv()
    
    model = "gemma3:4b"
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print(f"\n{'='*80}")
    print(f"GEMMA 3 4B QUALITY TEST")
    print(f"{'='*80}")
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"\nTest configuration:")
    print(f"  - Same source units as granite4:micro test")
    print(f"  - Same extraction prompt and schema")
    print(f"  - Temperature: 0.0")
    print(f"  - Direct comparison enabled")
    
    # Initialize provider
    try:
        provider = OllamaProvider(model=model, base_url=base_url)
        print(f"\n✓ Provider initialized")
    except Exception as e:
        print(f"\n✗ Provider initialization failed: {type(e).__name__}: {e}")
        return 1
    
    # Quick connectivity test
    try:
        test_response = provider.generate('{"test": "ok"}', max_tokens=20)
        print(f"✓ Connectivity verified")
    except Exception as e:
        print(f"✗ Connectivity failed: {e}")
        return 1
    
    # Load exact same source units used in granite test
    source_file = Path("data/output/source_units.json")
    if not source_file.exists():
        print(f"\n✗ Source file not found: {source_file}")
        return 1
    
    print(f"\n{'='*80}")
    print(f"LOADING TEST CONTENT")
    print(f"{'='*80}")
    
    # Use exact same IDs as granite test
    test_source_ids = ['S0016', 'S0017', 'S0020', 'S0021', 'S0022', 'S0023', 'S0024']
    source_doc = select_test_content(source_file, test_source_ids)
    
    print(f"✓ Loaded {len(source_doc.source_units)} source units")
    print(f"  Source IDs: {[u.source_id for u in source_doc.source_units]}")
    
    # Show sample
    print(f"\nSource unit samples:")
    for unit in source_doc.source_units[:2]:
        preview = unit.text[:100] if unit.text else "(empty)"
        print(f"  {unit.source_id}: {preview}...")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/output/gemma3_4b_quality_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    
    # Run extraction
    print(f"\n{'='*80}")
    print(f"EXTRACTION")
    print(f"{'='*80}")
    
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2048,
        max_retries=2,
        verbose=True
    )
    
    start_time = time.time()
    try:
        knowledge_doc = extractor.extract(source_doc)
        extraction_time = time.time() - start_time
        print(f"\n✓ Extraction completed in {extraction_time:.2f}s")
    except Exception as e:
        print(f"\n✗ Extraction failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Save results
    knowledge_file = output_dir / "knowledge.json"
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {knowledge_file}")
    
    source_file_out = output_dir / "source_units_used.json"
    with open(source_file_out, 'w', encoding='utf-8') as f:
        json.dump(source_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {source_file_out}")
    
    # Analyze
    print(f"\n{'='*80}")
    print(f"ANALYSIS")
    print(f"{'='*80}")
    
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    print(f"✓ Analysis completed")
    
    # Detailed audit
    audit_results = detailed_claim_audit(knowledge_doc, source_doc)
    
    # Print results
    print(f"\n{'='*80}")
    print(f"GEMMA 3 4B RESULTS")
    print(f"{'='*80}")
    
    print(f"\nConfiguration:")
    print(f"  Model: {model}")
    print(f"  Source units: {len(source_doc.source_units)}")
    print(f"  Extraction time: {extraction_time:.2f}s")
    print(f"  Avg per unit: {extraction_time/len(source_doc.source_units):.2f}s")
    
    print(f"\nExtraction Results:")
    print(f"  Concepts: {len(knowledge_doc.concepts)}")
    print(f"  Definitions: {len(knowledge_doc.definitions)}")
    print(f"  Explanations: {len(knowledge_doc.explanations)}")
    print(f"  Examples: {len(knowledge_doc.examples)}")
    print(f"  Facts: {len(knowledge_doc.facts)}")
    print(f"  Formulas: {len(knowledge_doc.formulas)}")
    print(f"  Procedures: {len(knowledge_doc.procedures)}")
    print(f"  Relationships: {len(knowledge_doc.relationships)}")
    print(f"  Total items: {knowledge_doc.total_items}")
    
    print(f"\nCompleteness:")
    metadata = knowledge_doc.extraction_metadata or {}
    completeness = metadata.get("completeness", 0.0)
    failed = metadata.get("failed_chunks", [])
    print(f"  Chunks: {metadata.get('total_chunks', 0)}")
    print(f"  Successful: {metadata.get('successful_chunks', 0)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Completeness: {completeness*100:.1f}%")
    
    print(f"\nQuality Audit:")
    total = len(audit_results["supported"]) + len(audit_results["unsupported"])
    supported = len(audit_results["supported"])
    unsupported = len(audit_results["unsupported"])
    provenance_errors = len(audit_results["provenance_errors"])
    
    print(f"  Total claims: {total}")
    print(f"  SUPPORTED: {supported}")
    print(f"  UNSUPPORTED: {unsupported}")
    print(f"  Provenance errors: {provenance_errors}")
    
    if total > 0:
        support_rate = supported / total
        print(f"  Support rate: {support_rate*100:.1f}%")
    else:
        support_rate = 0.0
        print(f"  Support rate: N/A (no extractions)")
    
    # Show examples
    if supported > 0:
        print(f"\nExamples of SUPPORTED claims:")
        for item_id in audit_results["supported"][:3]:
            item = next((i for i in (knowledge_doc.concepts + knowledge_doc.definitions + 
                        knowledge_doc.explanations + knowledge_doc.examples + 
                        knowledge_doc.facts + knowledge_doc.formulas + 
                        knowledge_doc.procedures + knowledge_doc.relationships) 
                        if i.knowledge_id == item_id), None)
            if item:
                print(f"  ✓ {item_id}: {item.content[:80]}...")
    
    if unsupported > 0:
        print(f"\nExamples of UNSUPPORTED claims:")
        for item in audit_results["unsupported"][:3]:
            print(f"  ✗ {item['id']}: {item['reason']} ({item['type']})")
    
    # Comparison with granite
    print(f"\n{'='*80}")
    print(f"COMPARISON WITH GRANITE4:MICRO")
    print(f"{'='*80}")
    print(f"\nGranite results (from previous test):")
    print(f"  Support rate: ~22-25%")
    print(f"  Common issues: Hallucination, wrong inferences, title expansion")
    print(f"\nGemma 3 4B results:")
    print(f"  Support rate: {support_rate*100:.1f}%")
    
    if support_rate > 0.5:
        print(f"  ✓ Significant improvement over Granite")
    elif support_rate > 0.3:
        print(f"  ~ Moderate improvement over Granite")
    else:
        print(f"  ✗ Similar or worse than Granite")
    
    # Assessment
    print(f"\n{'='*80}")
    print(f"ASSESSMENT")
    print(f"{'='*80}")
    
    if support_rate >= 0.7:
        print(f"\n✓ ACCEPTABLE QUALITY")
        print(f"  - Support rate {support_rate*100:.1f}% meets threshold")
        print(f"  - Suitable for broader testing")
    elif support_rate >= 0.5:
        print(f"\n~ MODERATE QUALITY")
        print(f"  - Support rate {support_rate*100:.1f}% shows improvement")
        print(f"  - May be usable with caution")
        print(f"  - Consider prompt refinement")
    else:
        print(f"\n✗ POOR QUALITY")
        print(f"  - Support rate {support_rate*100:.1f}% too low")
        print(f"  - Similar issues to Granite (hallucination, inference)")
        print(f"  - Not suitable for production")
    
    if provenance_errors > 0:
        print(f"\n⚠ Provenance accuracy issue:")
        print(f"  - {provenance_errors} items cite wrong source IDs")
        print(f"  - Critical for traceability")
    
    print(f"\nOutput saved to: {output_dir}")
    print(f"\nTo rerun:")
    print(f"  .\\.venv\\Scripts\\python.exe run_gemma_quality_test.py")
    
    return 0 if support_rate >= 0.7 else 1


if __name__ == "__main__":
    exit(main())
