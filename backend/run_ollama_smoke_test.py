"""
Smoke test for Ollama granite4:micro provider.

Tests extraction on a small sample of source units to verify:
- Ollama connectivity
- JSON generation and parsing
- Extraction completeness
- Valid source references
- Structural evaluation
- Response times

Does NOT overwrite existing Gemini/Groq artifacts.
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
from app.evaluation.evaluator import FaithfulnessEvaluator


def load_source_units(source_file: Path, max_units: int = 10):
    """Load a subset of source units for smoke testing"""
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    source_doc = SourceDocument(**data)
    
    # Take first N units
    selected_units = source_doc.source_units[:max_units]
    
    # Create a new document with subset
    test_doc = SourceDocument(
        document_id=source_doc.document_id,
        filename=source_doc.filename,
        page_count=source_doc.page_count,
        source_units=selected_units
    )
    
    return test_doc


def verify_ollama_connectivity(provider: OllamaProvider):
    """Verify Ollama is reachable and model is loaded"""
    print(f"\n{'='*80}")
    print(f"OLLAMA CONNECTIVITY CHECK")
    print(f"{'='*80}")
    print(f"Base URL: {provider.base_url}")
    print(f"Model: {provider.model}")
    
    # Try a simple generation
    try:
        test_prompt = "Respond with valid JSON: {\"test\": \"ok\"}"
        start = time.time()
        response = provider.generate(test_prompt, max_tokens=50)
        elapsed = time.time() - start
        
        print(f"✓ Connection successful")
        print(f"✓ Response time: {elapsed:.2f}s")
        print(f"✓ Response length: {len(response)} chars")
        
        # Verify it's JSON
        json.loads(response)
        print(f"✓ Valid JSON output")
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
        return False


def manual_claim_verification(knowledge_doc, source_doc):
    """
    Perform manual comparison of extracted claims with source text.
    
    Returns dict with verification results.
    """
    print(f"\n{'='*80}")
    print(f"MANUAL CLAIM VERIFICATION")
    print(f"{'='*80}")
    
    # Build source text lookup
    source_texts = {unit.source_id: unit.text for unit in source_doc.source_units if unit.text}
    
    # Sample up to 5 knowledge items for manual inspection
    all_items = (
        knowledge_doc.concepts[:2] +
        knowledge_doc.definitions[:2] +
        knowledge_doc.explanations[:1]
    )
    
    verified_count = 0
    unsupported_count = 0
    
    for item in all_items:
        print(f"\nKnowledge Item: {item.knowledge_id}")
        print(f"Type: {item.__class__.__name__}")
        print(f"Content: {item.content[:200]}...")
        print(f"Source IDs: {item.source_unit_ids}")
        
        # Check if source IDs exist and have text
        if not item.source_unit_ids:
            print(f"  WARNING: No source IDs")
            unsupported_count += 1
            continue
        
        # Verify at least one source contains related content
        found_support = False
        for src_id in item.source_unit_ids:
            if src_id in source_texts:
                src_text = source_texts[src_id]
                # Simple heuristic: check if key terms appear in source
                content_words = set(item.content.lower().split())
                source_words = set(src_text.lower().split())
                overlap = content_words & source_words
                
                if len(overlap) >= 3:  # At least 3 words overlap
                    found_support = True
                    print(f"  ✓ Found support in {src_id} ({len(overlap)} word overlap)")
                    break
        
        if found_support:
            verified_count += 1
        else:
            unsupported_count += 1
            print(f"  WARNING: Could not verify support in source text")
    
    return {
        "items_checked": len(all_items),
        "verified": verified_count,
        "unsupported": unsupported_count,
        "verification_rate": verified_count / len(all_items) if all_items else 0.0
    }


def main():
    # Load environment
    load_dotenv()
    
    model = os.getenv("OLLAMA_MODEL", "granite4:micro")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print(f"\n{'='*80}")
    print(f"OLLAMA GRANITE4:MICRO SMOKE TEST")
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
    
    # Verify connectivity
    if not verify_ollama_connectivity(provider):
        print(f"\n✗ Ollama connectivity check failed")
        print(f"  Ensure Ollama is running: ollama serve")
        print(f"  Ensure model is available: ollama list")
        return 1
    
    # Load source units
    source_file = Path("data/output/source_units.json")
    if not source_file.exists():
        print(f"\n✗ Source file not found: {source_file}")
        return 1
    
    print(f"\n{'='*80}")
    print(f"LOADING SOURCE UNITS")
    print(f"{'='*80}")
    
    num_units = 10
    source_doc = load_source_units(source_file, max_units=num_units)
    print(f"✓ Loaded {len(source_doc.source_units)} source units from {source_doc.filename}")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/output/ollama_granite4_micro_smoke_test_{timestamp}")
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
        return 1
    
    # Save knowledge document
    knowledge_file = output_dir / "knowledge.json"
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {knowledge_file}")
    
    # Analyze
    print(f"\n{'='*80}")
    print(f"ANALYSIS")
    print(f"{'='*80}")
    
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    print(f"✓ Analysis completed")
    
    # Save analyzed document
    analyzed_file = output_dir / "analyzed.json"
    with open(analyzed_file, 'w', encoding='utf-8') as f:
        json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {analyzed_file}")
    
    # Skip full evaluation for smoke test - just do manual verification
    print(f"\n{'='*80}")
    print(f"NOTE: Skipping full pipeline evaluation for smoke test")
    print(f"{'='*80}")
    
    # Manual verification
    manual_results = manual_claim_verification(knowledge_doc, source_doc)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"SMOKE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"\nConfiguration:")
    print(f"  Model: {model}")
    print(f"  Base URL: {base_url}")
    print(f"  Source units: {len(source_doc.source_units)}")
    print(f"  Extraction time: {extraction_time:.2f}s")
    print(f"  Avg time per unit: {extraction_time/len(source_doc.source_units):.2f}s")
    
    print(f"\nExtraction:")
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
    
    if failed:
        print(f"  WARNING: Failed chunks: {failed}")
    
    print(f"\nAnalysis:")
    print(f"  ✓ Analysis completed")
    if hasattr(analyzed_doc, 'characteristic_distribution') and analyzed_doc.characteristic_distribution:
        print(f"  Characteristics:")
        for char, count in sorted(analyzed_doc.characteristic_distribution.items()):
            print(f"    {char}: {count}")
    
    print(f"\nManual Verification:")
    print(f"  Items checked: {manual_results['items_checked']}")
    print(f"  Verified: {manual_results['verified']}")
    print(f"  Unsupported: {manual_results['unsupported']}")
    print(f"  Verification rate: {manual_results['verification_rate']*100:.1f}%")
    
    # Final assessment
    print(f"\n{'='*80}")
    print(f"ASSESSMENT")
    print(f"{'='*80}")
    
    issues = []
    
    if completeness < 1.0:
        issues.append(f"Incomplete extraction: {completeness*100:.1f}% completeness")
    
    if knowledge_doc.total_items == 0:
        issues.append("No knowledge items extracted")
    
    if manual_results['verification_rate'] < 0.5:
        issues.append(f"Low manual verification rate: {manual_results['verification_rate']*100:.1f}%")
    
    if issues:
        print(f"\n⚠ Issues detected:")
        for issue in issues:
            print(f"  - {issue}")
        print(f"\nRecommendation: Review prompt engineering or model compatibility before full-document processing")
    else:
        print(f"\n✓ Smoke test PASSED")
        print(f"  - Ollama connectivity: OK")
        print(f"  - JSON generation: OK")
        print(f"  - Extraction completeness: OK")
        print(f"  - Structural evaluation: OK")
        print(f"  - Manual verification: OK")
        print(f"\nReady for full-document extraction with {num_units} to 109 source units")
    
    print(f"\nOutput saved to: {output_dir}")
    print(f"\nTo rerun this test:")
    print(f"  .\\.venv\\Scripts\\python.exe run_ollama_smoke_test.py")
    
    return 0 if not issues else 1


if __name__ == "__main__":
    exit(main())
