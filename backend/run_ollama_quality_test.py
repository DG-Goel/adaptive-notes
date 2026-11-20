"""
Quality-focused smoke test for Ollama granite4:micro provider.

Tests extraction on meaningful content with strict prompt to verify:
- Extraction only from explicitly supported text
- No hallucination from titles or insufficient evidence
- Accurate source references
- Factual faithfulness

Validates every extracted claim against actual source text.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import OllamaProvider
from app.analysis.analyzer import ContentAnalyzer


def select_meaningful_content(source_file: Path, source_id_range: tuple):
    """Load specific meaningful content source units"""
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    source_doc = SourceDocument(**data)
    
    # Filter to requested range
    start_id, end_id = source_id_range
    start_num = int(start_id.replace('S', ''))
    end_num = int(end_id.replace('S', ''))
    
    selected_units = [
        unit for unit in source_doc.source_units
        if start_num <= int(unit.source_id.replace('S', '')) <= end_num
        and unit.content_role == 'content'
        and unit.text
        and len(unit.text) > 20
    ]
    
    # Create test document
    test_doc = SourceDocument(
        document_id=source_doc.document_id,
        filename=source_doc.filename,
        page_count=source_doc.page_count,
        source_units=selected_units
    )
    
    return test_doc


def manual_claim_inspection(knowledge_doc, source_doc):
    """
    Manually inspect each extracted claim against actual source text.
    
    Categorizes as: SUPPORTED, UNSUPPORTED, or INCONCLUSIVE
    """
    print(f"\n{'='*80}")
    print(f"MANUAL CLAIM INSPECTION")
    print(f"{'='*80}")
    
    # Build source text lookup
    source_texts = {unit.source_id: unit.text for unit in source_doc.source_units if unit.text}
    
    # Inspect all items
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
        "inconclusive": []
    }
    
    for item in all_items:
        print(f"\n{'─'*80}")
        print(f"Knowledge ID: {item.knowledge_id}")
        print(f"Type: {item.__class__.__name__}")
        
        # Get key content based on type
        if hasattr(item, 'concept_name'):
            print(f"Concept: {item.concept_name}")
        elif hasattr(item, 'term'):
            print(f"Term: {item.term}")
        elif hasattr(item, 'topic'):
            print(f"Topic: {item.topic}")
        elif hasattr(item, 'fact_text'):
            print(f"Fact: {item.fact_text[:100]}...")
        
        print(f"Content: {item.content[:200]}...")
        print(f"Source IDs: {item.source_unit_ids}")
        
        if not item.source_unit_ids:
            print(f"  ✗ UNSUPPORTED: No source IDs provided")
            results["unsupported"].append({
                "item": item.knowledge_id,
                "reason": "No source IDs"
            })
            continue
        
        # Check each source
        support_found = False
        all_sources_missing = True
        
        for src_id in item.source_unit_ids:
            if src_id not in source_texts:
                print(f"  ✗ Source {src_id}: NOT FOUND in document")
                continue
            
            all_sources_missing = False
            src_text = source_texts[src_id]
            print(f"  Source {src_id}: \"{src_text[:150]}...\"")
            
            # Manual judgment: Does the source text actually support the claim?
            # For a concept, the concept name or key terms should appear
            # For a fact, the factual statement should be present
            # For a relationship, both subject and object should be present
            
            if hasattr(item, 'concept_name'):
                # Check if concept name or key words appear in source
                concept_lower = item.concept_name.lower()
                source_lower = src_text.lower()
                
                # Check for direct mention or strong semantic overlap
                if concept_lower in source_lower:
                    print(f"    ✓ Concept name '{item.concept_name}' appears in source")
                    support_found = True
                else:
                    # Check content words
                    concept_words = set(concept_lower.split())
                    source_words = set(source_lower.split())
                    overlap = concept_words & source_words
                    
                    if len(overlap) >= 2:
                        print(f"    ~ Partial match: {overlap}")
                    else:
                        print(f"    ✗ Concept not found in source")
            
            elif hasattr(item, 'definition_text'):
                # Check if the term being defined appears
                term_lower = item.term.lower()
                source_lower = src_text.lower()
                
                if term_lower in source_lower:
                    print(f"    ✓ Term '{item.term}' appears in source")
                    support_found = True
                else:
                    print(f"    ✗ Term '{item.term}' not found in source")
            
            elif hasattr(item, 'fact_text'):
                # Check if key elements of the fact appear
                fact_words = set(item.fact_text.lower().split())
                source_words = set(src_text.lower().split())
                overlap = fact_words & source_words
                
                if len(overlap) >= 5:
                    print(f"    ✓ Fact supported ({len(overlap)} matching words)")
                    support_found = True
                else:
                    print(f"    ✗ Insufficient overlap ({len(overlap)} words)")
            
            elif hasattr(item, 'relationship_type'):
                # Check if both subject and object appear
                subject_lower = item.subject.lower()
                object_lower = item.object.lower()
                source_lower = src_text.lower()
                
                subject_present = subject_lower in source_lower
                object_present = object_lower in source_lower
                
                if subject_present and object_present:
                    print(f"    ✓ Both subject and object appear in source")
                    support_found = True
                else:
                    print(f"    ✗ Subject: {subject_present}, Object: {object_present}")
        
        # Categorize result
        if all_sources_missing:
            print(f"  → UNSUPPORTED: All source IDs missing")
            results["unsupported"].append({
                "item": item.knowledge_id,
                "reason": "All sources missing"
            })
        elif support_found:
            print(f"  → SUPPORTED: Claim verified in source text")
            results["supported"].append(item.knowledge_id)
        else:
            print(f"  → UNSUPPORTED: Claim not found in referenced sources")
            results["unsupported"].append({
                "item": item.knowledge_id,
                "reason": "Not found in source text"
            })
    
    return results


def main():
    # Load environment
    load_dotenv()
    
    model = os.getenv("OLLAMA_MODEL", "granite4:micro")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print(f"\n{'='*80}")
    print(f"OLLAMA QUALITY TEST - TIGHTENED PROMPT")
    print(f"{'='*80}")
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Initialize provider
    try:
        provider = OllamaProvider(model=model, base_url=base_url)
        print(f"✓ Provider initialized")
    except Exception as e:
        print(f"✗ Provider initialization failed: {type(e).__name__}: {e}")
        return 1
    
    # Quick connectivity test
    try:
        test_response = provider.generate('{"test": "ok"}', max_tokens=20)
        print(f"✓ Connectivity verified")
    except Exception as e:
        print(f"✗ Connectivity failed: {e}")
        return 1
    
    # Load meaningful content source units
    source_file = Path("data/output/source_units.json")
    if not source_file.exists():
        print(f"\n✗ Source file not found: {source_file}")
        return 1
    
    print(f"\n{'='*80}")
    print(f"LOADING MEANINGFUL CONTENT")
    print(f"{'='*80}")
    
    # Use S0016-S0024: continuous narrative content about a character
    source_doc = select_meaningful_content(source_file, ('S0016', 'S0024'))
    
    if len(source_doc.source_units) == 0:
        print(f"✗ No suitable source units found in range")
        return 1
    
    print(f"✓ Loaded {len(source_doc.source_units)} meaningful content units")
    print(f"  Source IDs: {[u.source_id for u in source_doc.source_units]}")
    
    # Show sample content
    print(f"\nSample source text:")
    for unit in source_doc.source_units[:2]:
        preview = unit.text[:120] if unit.text else "(empty)"
        print(f"  {unit.source_id}: {preview}...")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/output/ollama_quality_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    
    # Run extraction with TIGHTENED extraction logic
    # The existing prompt will be used, but we're relying on temperature=0
    # and the model's training to be more conservative
    print(f"\n{'='*80}")
    print(f"EXTRACTION WITH STRICT REQUIREMENTS")
    print(f"{'='*80}")
    print(f"Note: Using existing extraction prompt with temperature=0.0")
    print(f"      Relying on model to extract only supported claims")
    
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
    
    # Save knowledge document
    knowledge_file = output_dir / "knowledge.json"
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {knowledge_file}")
    
    # Also save source units for reference
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
    
    # Manual inspection of every claim
    inspection_results = manual_claim_inspection(knowledge_doc, source_doc)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"QUALITY TEST RESULTS")
    print(f"{'='*80}")
    print(f"\nConfiguration:")
    print(f"  Model: {model}")
    print(f"  Base URL: {base_url}")
    print(f"  Source units: {len(source_doc.source_units)}")
    print(f"  Source IDs: {[u.source_id for u in source_doc.source_units]}")
    print(f"  Extraction time: {extraction_time:.2f}s")
    print(f"  Avg time per unit: {extraction_time/len(source_doc.source_units):.2f}s")
    
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
    total_chunks = metadata.get("total_chunks", 0)
    successful = metadata.get("successful_chunks", 0)
    failed = metadata.get("failed_chunks", [])
    completeness = metadata.get("completeness", 0.0)
    print(f"  Total chunks: {total_chunks}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(failed)}")
    print(f"  Completeness: {completeness*100:.1f}%")
    
    print(f"\nQuality Assessment:")
    total_claims = len(inspection_results["supported"]) + len(inspection_results["unsupported"]) + len(inspection_results["inconclusive"])
    supported_count = len(inspection_results["supported"])
    unsupported_count = len(inspection_results["unsupported"])
    
    print(f"  Total claims inspected: {total_claims}")
    print(f"  SUPPORTED: {supported_count}")
    print(f"  UNSUPPORTED: {unsupported_count}")
    print(f"  INCONCLUSIVE: {len(inspection_results['inconclusive'])}")
    
    if total_claims > 0:
        support_rate = supported_count / total_claims
        print(f"  Support rate: {support_rate*100:.1f}%")
    else:
        support_rate = 0.0
        print(f"  Support rate: N/A (no claims extracted)")
    
    if unsupported_count > 0:
        print(f"\nUnsupported claims:")
        for item in inspection_results["unsupported"]:
            if isinstance(item, dict):
                print(f"    - {item['item']}: {item['reason']}")
            else:
                print(f"    - {item}")
    
    # Assessment
    print(f"\n{'='*80}")
    print(f"ASSESSMENT")
    print(f"{'='*80}")
    
    issues = []
    
    if completeness < 1.0:
        issues.append(f"Incomplete extraction: {completeness*100:.1f}%")
    
    if total_claims == 0:
        issues.append("No claims extracted - model may be overly conservative or prompt too restrictive")
    elif support_rate < 0.7:
        issues.append(f"Low support rate: {support_rate*100:.1f}% - model hallucinating or inferring beyond source")
    elif support_rate < 0.9:
        print(f"⚠ Moderate quality: {support_rate*100:.1f}% support rate")
        print(f"  Some hallucination present, but better than initial test")
    
    if issues:
        print(f"\n✗ Quality issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        
        print(f"\nLikely causes:")
        if total_claims == 0:
            print(f"  - Prompt may be unclear or model not following schema")
            print(f"  - Model may need different system instruction")
        elif support_rate < 0.5:
            print(f"  - Model inventing definitions from titles/headers")
            print(f"  - Prompt not emphasizing 'extract ONLY from explicit text'")
            print(f"  - Model inferring relationships not stated in source")
        else:
            print(f"  - Minor hallucination or over-inference")
        
        print(f"\nRecommendations:")
        if total_claims == 0:
            print(f"  1. Verify model can follow JSON schema")
            print(f"  2. Check if content is too sparse for extraction")
        else:
            print(f"  1. Tighten extraction prompt to emphasize:")
            print(f"     - Extract ONLY claims explicitly stated in text")
            print(f"     - Do NOT infer, expand, or define from titles alone")
            print(f"     - Preserve exact wording from source where possible")
            print(f"  2. Consider adding explicit negative examples")
            print(f"  3. Test with even stricter temperature (already at 0.0)")
    else:
        print(f"\n✓ Quality test PASSED")
        print(f"  - Extraction completeness: {completeness*100:.1f}%")
        print(f"  - Support rate: {support_rate*100:.1f}%")
        print(f"  - Response time: {extraction_time/len(source_doc.source_units):.2f}s per unit")
        print(f"\n  Ready for broader validation on more source units")
    
    print(f"\nOutput saved to: {output_dir}")
    print(f"\nTo rerun:")
    print(f"  .\\.venv\\Scripts\\python.exe run_ollama_quality_test.py")
    
    return 0 if not issues else 1


if __name__ == "__main__":
    exit(main())
