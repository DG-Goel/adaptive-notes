#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real LLM Validation Script

Runs knowledge extraction using Groq API on a small subset of source units.
This validates that the Groq provider works correctly with actual API calls.

IMPORTANT: This consumes API credits. Run with small sample only.
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
load_dotenv()

from app.models.source import SourceDocument, SourceUnit
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


def load_source_subset(source_path: Path, max_units: int = 5) -> SourceDocument:
    """Load a subset of source units for testing."""
    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load full document first
    full_doc = SourceDocument.model_validate(data)
    
    # Filter to units with text content only
    text_units = [u for u in full_doc.source_units if u.text and len(u.text.strip()) > 10]
    
    # Take first max_units units
    subset_units = text_units[:max_units]
    
    # Create subset document
    subset_doc = SourceDocument(
        document_id=full_doc.document_id,
        filename=f"{full_doc.filename} (subset {len(subset_units)} units)",
        page_count=full_doc.page_count,
        source_units=subset_units
    )
    
    return subset_doc, full_doc.filename


def check_for_duplicates(knowledge_doc):
    """Check for duplicate knowledge items across chunks."""
    # Group items by type and content
    items_by_content = {}
    duplicates = []
    
    for item in knowledge_doc.get_all_items():
        # Create a content key (type + main content field)
        if hasattr(item, 'concept_name'):
            key = f"concept:{item.concept_name}"
        elif hasattr(item, 'term'):
            key = f"definition:{item.term}"
        elif hasattr(item, 'fact_text'):
            key = f"fact:{item.fact_text[:50]}"
        else:
            key = f"{item.knowledge_type}:{item.content[:50]}"
        
        if key in items_by_content:
            duplicates.append((key, item.knowledge_id, items_by_content[key]))
        else:
            items_by_content[key] = item.knowledge_id
    
    return duplicates


def main():
    """Run small real LLM extraction."""
    print(f"\n{'#'*80}")
    print(f"# REAL LLM VALIDATION (Groq)")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    if not api_key:
        print("\n✗ ERROR: GROQ_API_KEY not found in environment")
        print("  Please set GROQ_API_KEY in .env file or environment")
        return 1
    
    print(f"\n✓ Groq API key found")
    print(f"  Model: {model}")
    print(f"  ⚠ WARNING: This will consume API credits")
    
    # Setup paths
    base_dir = Path(__file__).parent
    source_path = base_dir / "data" / "output" / "fresh_ingestion_test" / "source_units.json"
    output_dir = base_dir / "data" / "output" / "real_llm_validation"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_path.exists():
        print(f"\n✗ ERROR: Source document not found at {source_path}")
        return 1
    
    # Load subset of source units
    print(f"\n{'='*80}")
    print(f"LOADING SOURCE SUBSET")
    print(f"{'='*80}")
    
    subset_doc, original_filename = load_source_subset(source_path, max_units=5)
    
    print(f"✓ Loaded {len(subset_doc.source_units)} source units from {original_filename}")
    print(f"  Source IDs: {[u.source_id for u in subset_doc.source_units]}")
    
    # Save subset
    subset_path = output_dir / "source_subset.json"
    with open(subset_path, 'w', encoding='utf-8') as f:
        json.dump(subset_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    overall_start = time.time()
    
    try:
        # Initialize Groq provider
        print(f"\n{'='*80}")
        print(f"INITIALIZING GROQ PROVIDER")
        print(f"{'='*80}")
        
        provider = GroqProvider(model=model, api_key=api_key)
        print(f"✓ Groq provider initialized")
        print(f"  Model: {provider.model}")
        
        # Extract knowledge
        print(f"\n{'='*80}")
        print(f"EXTRACTING KNOWLEDGE (REAL LLM)")
        print(f"{'='*80}")
        
        extractor = KnowledgeExtractor(provider, verbose=True)
        knowledge_doc = extractor.extract(subset_doc)
        
        extraction_time = time.time() - overall_start
        
        # Save knowledge document
        knowledge_path = output_dir / "knowledge_document.json"
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"EXTRACTION RESULTS")
        print(f"{'='*80}")
        print(f"Total items extracted: {knowledge_doc.total_items}")
        print(f"Extraction time: {extraction_time:.2f}s")
        print(f"Items per source unit: {knowledge_doc.total_items / len(subset_doc.source_units):.1f}")
        print(f"\nBy type:")
        print(f"  Concepts: {len(knowledge_doc.concepts)}")
        print(f"  Definitions: {len(knowledge_doc.definitions)}")
        print(f"  Explanations: {len(knowledge_doc.explanations)}")
        print(f"  Examples: {len(knowledge_doc.examples)}")
        print(f"  Facts: {len(knowledge_doc.facts)}")
        print(f"  Formulas: {len(knowledge_doc.formulas)}")
        print(f"  Procedures: {len(knowledge_doc.procedures)}")
        print(f"  Relationships: {len(knowledge_doc.relationships)}")
        
        # Check for duplicates
        print(f"\n{'='*80}")
        print(f"DUPLICATE DETECTION")
        print(f"{'='*80}")
        
        duplicates = check_for_duplicates(knowledge_doc)
        if duplicates:
            print(f"⚠ Found {len(duplicates)} potential duplicates:")
            for content_key, kid1, kid2 in duplicates[:5]:
                print(f"  - {content_key}: {kid1} and {kid2}")
        else:
            print(f"✓ No duplicates detected")
        
        # Verify provenance
        print(f"\n{'='*80}")
        print(f"PROVENANCE VERIFICATION")
        print(f"{'='*80}")
        
        valid_source_ids = {u.source_id for u in subset_doc.source_units}
        invalid_refs = 0
        
        for item in knowledge_doc.get_all_items():
            for source_id in item.source_unit_ids:
                if source_id not in valid_source_ids:
                    invalid_refs += 1
                    print(f"  ⚠ {item.knowledge_id} references invalid source: {source_id}")
        
        if invalid_refs == 0:
            print(f"✓ All source references valid ({len([i for item in knowledge_doc.get_all_items() for i in item.source_unit_ids])} total references)")
        else:
            print(f"✗ Found {invalid_refs} invalid source references")
        
        # Run semantic verification
        print(f"\n{'='*80}")
        print(f"SEMANTIC VERIFICATION")
        print(f"{'='*80}")
        
        verifier = DeterministicSemanticVerifier(verbose=False)
        semantic_report = verifier.verify(knowledge_doc, subset_doc)
        
        # Save semantic report
        semantic_path = output_dir / "semantic_verification.json"
        with open(semantic_path, 'w', encoding='utf-8') as f:
            json.dump(semantic_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        supported = sum(
            1 for c in semantic_report.claim_verifications
            if c.verification_status.status == "SUPPORTED"
        )
        unsupported = sum(
            1 for c in semantic_report.claim_verifications
            if c.verification_status.status == "UNSUPPORTED"
        )
        inconclusive = sum(
            1 for c in semantic_report.claim_verifications
            if c.verification_status.status == "INCONCLUSIVE"
        )
        total = len(semantic_report.claim_verifications)
        
        print(f"Total claims: {total}")
        print(f"  SUPPORTED: {supported} ({supported/total*100 if total > 0 else 0:.1f}%)")
        print(f"  UNSUPPORTED: {unsupported} ({unsupported/total*100 if total > 0 else 0:.1f}%)")
        print(f"  INCONCLUSIVE: {inconclusive} ({inconclusive/total*100 if total > 0 else 0:.1f}%)")
        
        if unsupported > 0:
            print(f"\nUnsupported claims:")
            for claim in semantic_report.claim_verifications:
                if claim.verification_status.status == "UNSUPPORTED":
                    print(f"  - {claim.knowledge_id}: {claim.claim_text[:80]}...")
                    print(f"    Reason: {claim.verification_status.reason}")
        
        # Summary
        print(f"\n{'#'*80}")
        print(f"# VALIDATION COMPLETE")
        print(f"# Total time: {time.time() - overall_start:.2f}s")
        print(f"{'#'*80}")
        
        print(f"\n📁 Artifacts saved to: {output_dir}")
        print(f"  - source_subset.json ({len(subset_doc.source_units)} units)")
        print(f"  - knowledge_document.json ({knowledge_doc.total_items} items)")
        print(f"  - semantic_verification.json ({total} claims)")
        
        print(f"\n{'='*80}")
        print(f"KEY FINDINGS")
        print(f"{'='*80}")
        print(f"✓ Groq provider: Working (model={model})")
        print(f"✓ JSON parsing: {knowledge_doc.total_items} items parsed successfully")
        print(f"✓ Provenance: {invalid_refs} invalid references (should be 0)")
        print(f"✓ Duplicates: {len(duplicates)} found")
        print(f"✓ Semantic faithfulness: {supported}/{total} supported ({supported/total*100 if total > 0 else 0:.1f}%)")
        
        if knowledge_doc.total_items == 0:
            print(f"\n⚠ WARNING: Zero items extracted!")
            print(f"  This indicates extraction may have failed.")
            return 2
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: Validation failed")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
