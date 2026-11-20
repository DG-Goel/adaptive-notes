#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-20 Source Unit Validation with Real LLM

Controlled validation run on 15-20 representative source units.
Follows up on successful 5-unit extraction with expanded scope.

SAMPLE SELECTION CRITERIA:
- 18 content units with substantive text (>50 chars)
- Varied lengths: 83-1371 chars, avg 601 chars
- Pages 2-7 (6 pages covered)
- Narrative paragraphs with mixed complexity
- Excludes: pictures, noise, furniture, structural units

EXPLICIT GROQ PROVIDER - NO MOCK FALLBACK
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
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

# Load environment variables
load_dotenv()

from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import KnowledgeDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


# Selected source unit IDs based on analysis
SELECTED_SOURCE_IDS = [
    "S0012",  # Page 2, 741 chars - wave incident at hotel
    "S0013",  # Page 2, 1196 chars - cleanup and victim discovery
    "S0016",  # Page 3, 1173 chars - narrator's concern about woman
    "S0017",  # Page 3, 172 chars - Vienna description
    "S0020",  # Page 4, 710 chars - Vienna as espionage hub
    "S0022",  # Page 4, 657 chars - woman's background
    "S0023",  # Page 4, 110 chars - dream interpretation (dialogue)
    "S0024",  # Page 4, 1371 chars - boy's reaction to dream
    "S0027",  # Page 5, 616 chars - woman's successful work
    "S0028",  # Page 5, 375 chars - narrator's Vienna stay
    "S0029",  # Page 5, 145 chars - warning dream (dialogue)
    "S0030",  # Page 5, 274 chars - narrator's response to warning
    "S0036",  # Page 6, 784 chars - encounter in Barcelona
    "S0037",  # Page 6, 1008 chars - Pablo Neruda description
    "S0041",  # Page 7, 324 chars - woman staring at narrator
    "S0042",  # Page 7, 373 chars - woman's ship journey
    "S0044",  # Page 7, 713 chars - conversation during walk
    "S0047",  # Page 7, 83 chars - realization of time passed
]


def load_selected_sample(source_path: Path) -> SourceDocument:
    """Load selected 18 source units for validation."""
    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    full_doc = SourceDocument.model_validate(data)
    
    # Filter to selected IDs
    selected_units = [u for u in full_doc.source_units if u.source_id in SELECTED_SOURCE_IDS]
    
    # Verify all IDs found
    found_ids = {u.source_id for u in selected_units}
    missing_ids = set(SELECTED_SOURCE_IDS) - found_ids
    if missing_ids:
        print(f"⚠ WARNING: Missing source IDs: {missing_ids}")
    
    # Create subset document
    subset_doc = SourceDocument(
        document_id=full_doc.document_id,
        filename=f"{full_doc.filename} (18-unit sample)",
        page_count=full_doc.page_count,
        source_units=selected_units
    )
    
    return subset_doc, full_doc.filename


def check_exact_duplicates(knowledge_doc: KnowledgeDocument):
    """Check for exact duplicate knowledge items by content."""
    content_map = defaultdict(list)
    
    for item in knowledge_doc.get_all_items():
        # Use full content as key
        content_key = item.content.strip().lower()
        content_map[content_key].append(item.knowledge_id)
    
    exact_dupes = {k: v for k, v in content_map.items() if len(v) > 1}
    return exact_dupes


def check_semantic_near_duplicates(knowledge_doc: KnowledgeDocument):
    """
    Identify likely semantic near-duplicates.
    
    Uses same heuristic as 5-unit audit: group by type + content prefix.
    """
    items_by_signature = defaultdict(list)
    
    for item in knowledge_doc.get_all_items():
        # Create signature: type + first 50 chars of content
        content_prefix = item.content[:50].strip().lower()
        signature = f"{item.knowledge_type}:{content_prefix}"
        items_by_signature[signature].append(item.knowledge_id)
    
    # Also check related concepts about same topic
    concept_groups = defaultdict(list)
    for concept in knowledge_doc.concepts:
        # Group by concept name (case-insensitive)
        concept_groups[concept.concept_name.lower()].append(concept.knowledge_id)
    
    near_dupes = []
    
    # Find signature clusters
    for sig, ids in items_by_signature.items():
        if len(ids) > 1:
            near_dupes.append({
                "signature": sig,
                "ids": ids,
                "count": len(ids)
            })
    
    # Find concept name clusters (excluding exact duplicates)
    for name, ids in concept_groups.items():
        if len(ids) > 1:
            # Check if these are genuinely different items
            concepts = [c for c in knowledge_doc.concepts if c.knowledge_id in ids]
            contents = [c.content for c in concepts]
            # Only flag if contents differ (not exact duplicates)
            if len(set(contents)) > 1:
                near_dupes.append({
                    "signature": f"concept:{name}",
                    "ids": ids,
                    "count": len(ids)
                })
    
    return near_dupes


def main():
    """Run 15-20 unit validation."""
    print(f"\n{'#'*80}")
    print(f"# 15-20 UNIT VALIDATION (Groq openai/gpt-oss-120b)")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    if not api_key:
        print("\n✗ ERROR: GROQ_API_KEY not found in environment")
        print("  Set GROQ_API_KEY in .env file")
        return 1
    
    print(f"\n✓ Groq API key found")
    print(f"  Model: {model}")
    print(f"  Selected units: {len(SELECTED_SOURCE_IDS)}")
    print(f"  ⚠ WARNING: This will consume API credits")
    
    # Setup paths
    base_dir = Path(__file__).parent
    source_path = base_dir / "data" / "output" / "fresh_ingestion_test" / "source_units.json"
    output_dir = base_dir / "data" / "output" / "real_llm_validation_15_20"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not source_path.exists():
        print(f"\n✗ ERROR: Source document not found at {source_path}")
        return 1
    
    # Load selected sample
    print(f"\n{'='*80}")
    print(f"LOADING SELECTED SAMPLE")
    print(f"{'='*80}")
    
    sample_doc, original_filename = load_selected_sample(source_path)
    
    print(f"✓ Loaded {len(sample_doc.source_units)} source units from {original_filename}")
    print(f"  Source IDs: {[u.source_id for u in sample_doc.source_units]}")
    print(f"  Pages covered: {sorted(set(u.page for u in sample_doc.source_units))}")
    
    # Calculate text statistics
    text_lengths = [len(u.text) for u in sample_doc.source_units if u.text]
    total_chars = sum(text_lengths)
    print(f"  Total text: {total_chars} characters")
    print(f"  Avg per unit: {total_chars // len(sample_doc.source_units)} chars")
    print(f"  Range: {min(text_lengths)}-{max(text_lengths)} chars")
    
    # Save sample subset
    sample_path = output_dir / "source_sample.json"
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(sample_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Record selection rationale
    rationale_path = output_dir / "SAMPLE_SELECTION.md"
    with open(rationale_path, 'w', encoding='utf-8') as f:
        f.write("# Sample Selection Rationale\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Selection Criteria\n\n")
        f.write(f"- **Target:** 15-20 source units with substantive content\n")
        f.write(f"- **Actual:** {len(sample_doc.source_units)} units selected\n")
        f.write(f"- **Text filter:** content_role='content' AND text.length > 50 chars\n")
        f.write(f"- **Exclusions:** pictures ({len([u for u in sample_doc.source_units if u.type == 'picture'])}), ")
        f.write(f"noise, furniture, structural units\n\n")
        f.write(f"## Sample Characteristics\n\n")
        f.write(f"- **Pages:** {min(u.page for u in sample_doc.source_units)}-{max(u.page for u in sample_doc.source_units)} ")
        f.write(f"({len(set(u.page for u in sample_doc.source_units))} pages)\n")
        f.write(f"- **Total characters:** {total_chars}\n")
        f.write(f"- **Average length:** {total_chars // len(sample_doc.source_units)} chars/unit\n")
        f.write(f"- **Length range:** {min(text_lengths)}-{max(text_lengths)} chars\n\n")
        f.write(f"## Selected Source Units\n\n")
        f.write(f"| ID | Page | Length | Preview |\n")
        f.write(f"|----|------|--------|----------|\n")
        for u in sample_doc.source_units:
            preview = u.text[:60] + "..." if len(u.text) > 60 else u.text
            preview = preview.replace('\n', ' ').replace('|', '\\|')
            f.write(f"| {u.source_id} | {u.page} | {len(u.text)} | {preview} |\n")
    
    overall_start = time.time()
    
    try:
        # Initialize Groq provider
        print(f"\n{'='*80}")
        print(f"INITIALIZING GROQ PROVIDER")
        print(f"{'='*80}")
        
        provider = GroqProvider(model=model, api_key=api_key)
        print(f"✓ Groq provider initialized")
        print(f"  Model: {provider.model}")
        print(f"  No mock fallback configured")
        
        # STAGE 1: EXTRACTION
        print(f"\n{'='*80}")
        print(f"STAGE 1: KNOWLEDGE EXTRACTION")
        print(f"{'='*80}")
        
        extraction_start = time.time()
        extractor = KnowledgeExtractor(provider, verbose=True)
        knowledge_doc = extractor.extract(sample_doc)
        extraction_time = time.time() - extraction_start
        
        # Save knowledge document
        knowledge_path = output_dir / "knowledge_document.json"
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Extraction complete: {knowledge_doc.total_items} items in {extraction_time:.2f}s")
        print(f"  Extraction rate: {knowledge_doc.total_items / len(sample_doc.source_units):.1f} items/unit")
        
        # STAGE 2: CONTENT ANALYSIS
        print(f"\n{'='*80}")
        print(f"STAGE 2: CONTENT ANALYSIS")
        print(f"{'='*80}")
        
        analyzer = ContentAnalyzer(verbose=False)
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        analyzed_path = output_dir / "analyzed_knowledge.json"
        with open(analyzed_path, 'w', encoding='utf-8') as f:
            json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Analysis complete: {len(analyzed_doc.get_all_items())} items analyzed")
        
        # STAGE 3: REPRESENTATION SELECTION
        print(f"\n{'='*80}")
        print(f"STAGE 3: REPRESENTATION SELECTION")
        print(f"{'='*80}")
        
        selector = RepresentationSelector(verbose=False)
        representation_doc = selector.select_representations(analyzed_doc)
        
        repr_path = output_dir / "representation.json"
        with open(repr_path, 'w', encoding='utf-8') as f:
            json.dump(representation_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Representation selection complete")
        
        # STAGE 4: ASSEMBLY
        print(f"\n{'='*80}")
        print(f"STAGE 4: ASSEMBLY")
        print(f"{'='*80}")
        
        assembler = NoteAssembler(verbose=False)
        assembled_doc = assembler.assemble(representation_doc)
        
        assembled_path = output_dir / "assembled_notes.json"
        with open(assembled_path, 'w', encoding='utf-8') as f:
            json.dump(assembled_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Assembly complete: {len(assembled_doc.sections)} sections")
        
        # STAGE 5: RENDERING
        print(f"\n{'='*80}")
        print(f"STAGE 5: RENDERING")
        print(f"{'='*80}")
        
        renderer = MarkdownRenderer(verbose=False)
        markdown, manifest = renderer.render(assembled_doc)
        
        rendered_path = output_dir / "rendered_notes.md"
        with open(rendered_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        manifest_path = output_dir / "render_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Rendering complete: {len(markdown)} characters")
        
        # STAGE 6: EVALUATION
        print(f"\n{'='*80}")
        print(f"STAGE 6: EVALUATION")
        print(f"{'='*80}")
        
        evaluator = FaithfulnessEvaluator(verbose=False)
        eval_report = evaluator.evaluate(
            source_doc=sample_doc,
            knowledge_doc=knowledge_doc,
            analyzed_doc=analyzed_doc,
            representation_doc=representation_doc,
            assembled_doc=assembled_doc,
            render_manifest=manifest
        )
        
        eval_path = output_dir / "evaluation_report.json"
        with open(eval_path, 'w', encoding='utf-8') as f:
            json.dump(eval_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Evaluation complete")
        
        # STAGE 7: SEMANTIC VERIFICATION
        print(f"\n{'='*80}")
        print(f"STAGE 7: SEMANTIC VERIFICATION")
        print(f"{'='*80}")
        
        verifier = DeterministicSemanticVerifier(verbose=False)
        semantic_report = verifier.verify(knowledge_doc, sample_doc)
        
        semantic_path = output_dir / "semantic_verification.json"
        with open(semantic_path, 'w', encoding='utf-8') as f:
            json.dump(semantic_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Semantic verification complete: {len(semantic_report.claim_verifications)} claims")
        
        # QUALITY CHECKS
        print(f"\n{'='*80}")
        print(f"QUALITY AUDIT")
        print(f"{'='*80}")
        
        # Check exact duplicates
        exact_dupes = check_exact_duplicates(knowledge_doc)
        print(f"Exact duplicates: {len(exact_dupes)}")
        if exact_dupes:
            print(f"  ⚠ {sum(len(v)-1 for v in exact_dupes.values())} duplicate items found")
            for content, ids in list(exact_dupes.items())[:3]:
                print(f"    {ids}")
        
        # Check near-duplicates
        near_dupes = check_semantic_near_duplicates(knowledge_doc)
        total_near_dupe_items = sum(cluster['count'] for cluster in near_dupes)
        print(f"Near-duplicate clusters: {len(near_dupes)} clusters, {total_near_dupe_items} items")
        if near_dupes:
            print(f"  ⚠ {total_near_dupe_items}/{knowledge_doc.total_items} items in near-duplicate clusters ({total_near_dupe_items/knowledge_doc.total_items*100:.1f}%)")
        
        # Provenance check
        valid_source_ids = {u.source_id for u in sample_doc.source_units}
        invalid_refs = 0
        for item in knowledge_doc.get_all_items():
            for source_id in item.source_unit_ids:
                if source_id not in valid_source_ids:
                    invalid_refs += 1
        
        print(f"Provenance: {invalid_refs} invalid references")
        
        # Semantic verification summary
        print(f"Semantic verification:")
        print(f"  SUPPORTED: {semantic_report.claims_supported} ({semantic_report.claims_supported/semantic_report.total_claims_verified*100:.1f}%)")
        print(f"  UNSUPPORTED: {semantic_report.claims_unsupported} ({semantic_report.claims_unsupported/semantic_report.total_claims_verified*100:.1f}%)")
        print(f"  CONTRADICTED: {semantic_report.claims_contradicted} ({semantic_report.claims_contradicted/semantic_report.total_claims_verified*100:.1f}%)")
        print(f"  INCONCLUSIVE: {semantic_report.claims_inconclusive} ({semantic_report.claims_inconclusive/semantic_report.total_claims_verified*100:.1f}%)")
        
        total_time = time.time() - overall_start
        
        # SUMMARY
        print(f"\n{'#'*80}")
        print(f"# VALIDATION COMPLETE")
        print(f"# Total time: {total_time:.2f}s")
        print(f"{'#'*80}")
        
        print(f"\n📁 All artifacts saved to: {output_dir}")
        print(f"\n{'='*80}")
        print(f"KEY METRICS")
        print(f"{'='*80}")
        print(f"Source units: {len(sample_doc.source_units)}")
        print(f"Extracted items: {knowledge_doc.total_items}")
        print(f"Extraction rate: {knowledge_doc.total_items/len(sample_doc.source_units):.1f} items/unit")
        print(f"Exact duplicates: {len(exact_dupes)}")
        print(f"Near-duplicate clusters: {len(near_dupes)} ({total_near_dupe_items} items, {total_near_dupe_items/knowledge_doc.total_items*100:.1f}%)")
        print(f"Invalid provenance: {invalid_refs}")
        print(f"Semantic support: {semantic_report.claims_supported}/{semantic_report.total_claims_verified} ({semantic_report.claims_supported/semantic_report.total_claims_verified*100:.1f}%)")
        print(f"Extraction time: {extraction_time:.2f}s")
        print(f"Total time: {total_time:.2f}s")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: Validation failed")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
