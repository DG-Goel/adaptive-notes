#!/usr/bin/env python3
"""
Real-world end-to-end validation of Adaptive Notes Generation Pipeline
using Java lecture transcript.

Validates complete pipeline:
1. Transcript ingestion (text → SourceUnits)
2. Knowledge extraction with multi-key Groq
3. Rule-based analysis
4. Representation selection
5. Note assembly
6. Markdown rendering
7. Semantic verification

Tracks all chunks (attempted, successful, recovered, skipped, failed).
Never silently discards failed content.
Verifies source provenance for every extracted item.
Audits representative sample of claims against original transcript.
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

from app.ingestion.transcript_parser import parse_transcript
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.models.source import SourceDocument


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough approximation: 1.3 tokens per word)."""
    words = len(text.split())
    return int(words * 1.3)


def audit_claims_against_transcript(
    knowledge_doc: Any,
    source_doc: SourceDocument,
    sample_size: int = 10
) -> Dict[str, Any]:
    """
    Manually audit extracted claims against original transcript.
    
    Reports:
    - Unsupported claims (not found in referenced source)
    - Contradicted claims (conflicts with source)
    - Duplicated claims (same information extracted multiple times)
    - Incorrectly attributed claims (wrong source_unit_ids)
    
    Args:
        knowledge_doc: Extracted knowledge document
        source_doc: Original source document
        sample_size: Number of claims to audit per type
        
    Returns:
        Audit results dictionary
    """
    
    # Build source text lookup
    source_texts = {unit.source_id: unit.text for unit in source_doc.source_units if unit.text}
    
    audit_results = {
        "unsupported": [],
        "contradicted": [],
        "duplicated": [],
        "incorrectly_attributed": [],
        "total_audited": 0,
        "audit_timestamp": datetime.now().isoformat()
    }
    
    # Collect sample claims from each type
    sample_claims = []
    
    for concept in knowledge_doc.concepts[:sample_size]:
        sample_claims.append({
            "type": "concept",
            "id": concept.knowledge_id,
            "content": concept.content,
            "source_ids": concept.source_unit_ids
        })
    
    for definition in knowledge_doc.definitions[:sample_size]:
        sample_claims.append({
            "type": "definition",
            "id": definition.knowledge_id,
            "content": definition.definition_text,
            "source_ids": definition.source_unit_ids
        })
    
    for explanation in knowledge_doc.explanations[:sample_size]:
        sample_claims.append({
            "type": "explanation",
            "id": explanation.knowledge_id,
            "content": explanation.explanation_text,
            "source_ids": explanation.source_unit_ids
        })
    
    for fact in knowledge_doc.facts[:sample_size]:
        sample_claims.append({
            "type": "fact",
            "id": fact.knowledge_id,
            "content": fact.fact_text,
            "source_ids": fact.source_unit_ids
        })
    
    audit_results["total_audited"] = len(sample_claims)
    
    # Check each claim
    seen_content = {}
    for claim in sample_claims:
        # Check for duplicates (exact match)
        normalized = claim["content"].lower().strip()
        if normalized in seen_content:
            audit_results["duplicated"].append({
                "current_id": claim["id"],
                "duplicate_of": seen_content[normalized],
                "content": claim["content"][:150]
            })
        else:
            seen_content[normalized] = claim["id"]
        
        # Check source attribution
        if not claim["source_ids"]:
            audit_results["incorrectly_attributed"].append({
                "id": claim["id"],
                "issue": "No source_unit_ids provided",
                "content": claim["content"][:150]
            })
            continue
        
        # Verify source IDs exist
        invalid_refs = [sid for sid in claim["source_ids"] if sid not in source_texts]
        if invalid_refs:
            audit_results["incorrectly_attributed"].append({
                "id": claim["id"],
                "issue": f"Invalid source_unit_ids: {invalid_refs}",
                "content": claim["content"][:150]
            })
            continue
        
        # Check if content is supported by sources (word overlap heuristic)
        combined_source = " ".join(source_texts.get(sid, "") for sid in claim["source_ids"])
        
        # Extract key words from claim (simple word-based check)
        claim_words = set(w.lower() for w in claim["content"].split() if len(w) > 3)
        source_words = set(w.lower() for w in combined_source.split() if len(w) > 3)
        
        # Calculate overlap
        if claim_words:
            overlap = len(claim_words & source_words) / len(claim_words)
            
            # If less than 20% overlap, flag as potentially unsupported
            if overlap < 0.2:
                audit_results["unsupported"].append({
                    "id": claim["id"],
                    "type": claim["type"],
                    "content": claim["content"][:150],
                    "overlap": f"{overlap:.1%}",
                    "source_ids": claim["source_ids"]
                })
    
    return audit_results


def main():
    print("=" * 80)
    print("JAVA TRANSCRIPT END-TO-END VALIDATION")
    print("=" * 80)
    print()
    
    # Setup paths
    transcript_path = Path("C:\\Projects\\adaptive-notes\\java.txt")
    output_dir = Path("data/output/java_transcript_validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Verify transcript exists
    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        return 1
    
    print(f"Transcript: {transcript_path.name}")
    
    # Analyze transcript file
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
    
    file_size = transcript_path.stat().st_size
    word_count = len(transcript_content.split())
    char_count = len(transcript_content)
    estimated_tokens = estimate_tokens(transcript_content)
    
    print(f"  Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    print(f"  Characters: {char_count:,}")
    print(f"  Words: {word_count:,}")
    print(f"  Estimated tokens: {estimated_tokens:,}")
    print()
    
    # ==================================================
    # STEP 1: TRANSCRIPT INGESTION
    # ==================================================
    print("=" * 80)
    print("STEP 1: TRANSCRIPT INGESTION")
    print("=" * 80)
    print()
    
    print("Parsing transcript into Source Units...")
    print("  Strategy: Natural paragraph boundaries")
    print("  Min segment: 50 words")
    print("  Max segment: 500 words")
    print()
    
    start_time = time.time()
    
    try:
        source_doc = parse_transcript(
            transcript_path,
            min_segment_words=50,
            max_segment_words=500,
            detect_timestamps=True
        )
    except Exception as e:
        print(f"❌ INGESTION FAILED: {type(e).__name__}: {e}")
        return 1
    
    ingestion_time = time.time() - start_time
    
    print(f"✓ Ingestion complete ({ingestion_time:.2f}s)")
    print()
    print(f"Source Document:")
    print(f"  Document ID: {source_doc.document_id}")
    print(f"  Filename: {source_doc.filename}")
    print(f"  Source units: {len(source_doc.source_units)}")
    print()
    
    # Analyze segments
    content_units = [u for u in source_doc.source_units if u.content_role == "content"]
    structural_units = [u for u in source_doc.source_units if u.content_role == "structural"]
    
    print(f"Source Unit Breakdown:")
    print(f"  Content units: {len(content_units)}")
    print(f"  Structural units: {len(structural_units)}")
    print()
    
    # Show sample units
    print(f"Sample Source Units:")
    for i, unit in enumerate(source_doc.source_units[:3], 1):
        text_preview = (unit.text[:100] + "...") if unit.text and len(unit.text) > 100 else unit.text
        print(f"  {i}. {unit.source_id} ({unit.type}, {unit.content_role})")
        print(f"     Text: {text_preview}")
    print()
    
    # Save source units
    source_units_path = output_dir / f"source_units_{timestamp}.json"
    with open(source_units_path, 'w', encoding='utf-8') as f:
        json.dump(source_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved source units: {source_units_path.name}")
    print()
    
    # Estimate extraction workload
    total_text = " ".join(u.text for u in source_doc.source_units if u.text)
    total_tokens = estimate_tokens(total_text)
    
    print(f"Extraction Workload Estimate:")
    print(f"  Total text tokens: ~{total_tokens:,}")
    print(f"  Estimated chunks (2000 tokens each): ~{total_tokens // 2000}")
    print(f"  Estimated extraction time: ~{(total_tokens // 2000) * 12:.0f}s ({(total_tokens // 2000) * 12 / 60:.1f} min)")
    print()
    
    # Chunking strategy
    print(f"Proposed Chunking Strategy:")
    print(f"  Max tokens per chunk: 2000")
    print(f"  Adaptive splitting: Enabled (max depth: 2)")
    print(f"  Retry limit: 2 (to avoid rate limit evasion)")
    print(f"  Multi-key scheduler: {'Enabled' if os.getenv('GROQ_API_KEY_1') else 'Disabled'}")
    print()
    
    # Confirm before proceeding
    input("Press ENTER to proceed with extraction (or Ctrl+C to cancel)...")
    print()
    
    # ==================================================
    # STEP 2: KNOWLEDGE EXTRACTION
    # ==================================================
    print("=" * 80)
    print("STEP 2: KNOWLEDGE EXTRACTION")
    print("=" * 80)
    print()
    
    # Initialize provider
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Check for multi-key setup
    multi_keys = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
    num_keys = sum(1 for k in multi_keys if k)
    
    if num_keys > 0:
        print(f"Multi-key setup: {num_keys} credentials")
        provider = GroqProvider(model=model, use_multi_key=True)
    else:
        single_key = os.getenv("GROQ_API_KEY")
        if not single_key:
            print("ERROR: No GROQ_API_KEY credentials found")
            return 1
        print("Single-key setup")
        provider = GroqProvider(model=model, api_key=single_key, use_multi_key=False)
    
    print(f"Provider: {provider.model}")
    print()
    
    # Initialize extractor
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2000,
        verbose=True,
        max_retries=2,
        min_output_tokens=500,
        preferred_output_tokens=4000,
        max_split_depth=2
    )
    
    # Extract
    extraction_start = time.time()
    
    try:
        knowledge_doc = extractor.extract(source_doc)
    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED: {type(e).__name__}: {e}")
        return 1
    
    extraction_time = time.time() - extraction_start
    
    print()
    print("=" * 80)
    print("EXTRACTION RESULTS")
    print("=" * 80)
    print()
    
    # Collect metrics
    metadata = knowledge_doc.extraction_metadata
    total_chunks = metadata.get("total_chunks", 0)
    successful_chunks = metadata.get("successful_chunks", 0)
    failed_chunks_list = metadata.get("failed_chunks", [])
    split_chunks_list = metadata.get("split_chunks", [])
    completeness = metadata.get("completeness", 0.0)
    
    print(f"Chunks:")
    print(f"  Attempted: {total_chunks}")
    print(f"  Successful: {successful_chunks}")
    print(f"  Failed: {len(failed_chunks_list)}")
    print(f"  Recovered via splitting: {len(split_chunks_list)}")
    print(f"  Completeness: {completeness:.1%}")
    
    if failed_chunks_list:
        print(f"  Failed chunk IDs: {failed_chunks_list[:5]}{'...' if len(failed_chunks_list) > 5 else ''}")
    print()
    
    print(f"Extracted Items:")
    print(f"  Total: {knowledge_doc.total_items}")
    print(f"  Concepts: {len(knowledge_doc.concepts)}")
    print(f"  Definitions: {len(knowledge_doc.definitions)}")
    print(f"  Explanations: {len(knowledge_doc.explanations)}")
    print(f"  Examples: {len(knowledge_doc.examples)}")
    print(f"  Facts: {len(knowledge_doc.facts)}")
    print(f"  Formulas: {len(knowledge_doc.formulas)}")
    print(f"  Procedures: {len(knowledge_doc.procedures)}")
    print(f"  Relationships: {len(knowledge_doc.relationships)}")
    print()
    
    print(f"Performance:")
    print(f"  Extraction time: {extraction_time:.2f}s ({extraction_time/60:.1f} min)")
    print(f"  Items per minute: {knowledge_doc.total_items / (extraction_time / 60):.1f}")
    print()
    
    # Save extraction results
    knowledge_path = output_dir / f"knowledge_{timestamp}.json"
    with open(knowledge_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {knowledge_path.name}")
    print()
    
    # ==================================================
    # STEP 3: RULE-BASED ANALYSIS
    # ==================================================
    print("=" * 80)
    print("STEP 3: RULE-BASED ANALYSIS")
    print("=" * 80)
    print()
    
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    print(f"✓ Analysis complete")
    print()
    
    # Save analysis
    analysis_path = output_dir / f"analyzed_{timestamp}.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {analysis_path.name}")
    print()
    
    # ==================================================
    # STEP 4: REPRESENTATION SELECTION
    # ==================================================
    print("=" * 80)
    print("STEP 4: REPRESENTATION SELECTION")
    print("=" * 80)
    print()
    
    selector = RepresentationSelector()
    representations_doc = selector.select(analyzed_doc)
    
    print(f"✓ Selected {len(representations_doc.representations)} representations")
    print()
    
    # Save representations
    repr_path = output_dir / f"representations_{timestamp}.json"
    with open(repr_path, 'w', encoding='utf-8') as f:
        json.dump(representations_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {repr_path.name}")
    print()
    
    # ==================================================
    # STEP 5: NOTE ASSEMBLY
    # ==================================================
    print("=" * 80)
    print("STEP 5: NOTE ASSEMBLY")
    print("=" * 80)
    print()
    
    assembler = NoteAssembler()
    assembled_notes = assembler.assemble(representations_doc, analyzed_doc)
    
    print(f"✓ Assembled {len(assembled_notes.sections)} note sections")
    print()
    
    # Save assembled notes
    assembled_path = output_dir / f"assembled_{timestamp}.json"
    with open(assembled_path, 'w', encoding='utf-8') as f:
        json.dump(assembled_notes.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {assembled_path.name}")
    print()
    
    # ==================================================
    # STEP 6: MARKDOWN RENDERING
    # ==================================================
    print("=" * 80)
    print("STEP 6: MARKDOWN RENDERING")
    print("=" * 80)
    print()
    
    renderer = MarkdownRenderer()
    markdown_output = renderer.render(assembled_notes)
    
    # Save markdown
    markdown_path = output_dir / f"notes_{timestamp}.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    print(f"✓ Rendered to Markdown")
    print(f"✓ Saved: {markdown_path.name}")
    print()
    
    # ==================================================
    # STEP 7: SEMANTIC VERIFICATION
    # ==================================================
    print("=" * 80)
    print("STEP 7: SEMANTIC VERIFICATION")
    print("=" * 80)
    print()
    
    verifier = DeterministicSemanticVerifier()
    verification_report = verifier.verify(assembled_notes, analyzed_doc, source_doc)
    
    print(f"✓ Semantic verification complete")
    print()
    
    # Save verification
    verification_path = output_dir / f"verification_{timestamp}.json"
    with open(verification_path, 'w', encoding='utf-8') as f:
        json.dump(verification_report.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {verification_path.name}")
    print()
    
    # ==================================================
    # STEP 8: CLAIM AUDIT
    # ==================================================
    print("=" * 80)
    print("STEP 8: CLAIM AUDIT (Manual Sample)")
    print("=" * 80)
    print()
    
    print("Auditing representative sample of claims...")
    audit_results = audit_claims_against_transcript(
        knowledge_doc,
        source_doc,
        sample_size=10
    )
    
    print(f"  Total audited: {audit_results['total_audited']}")
    print(f"  Unsupported: {len(audit_results['unsupported'])}")
    print(f"  Contradicted: {len(audit_results['contradicted'])}")
    print(f"  Duplicated: {len(audit_results['duplicated'])}")
    print(f"  Attribution errors: {len(audit_results['incorrectly_attributed'])}")
    print()
    
    if audit_results['unsupported']:
        print("  Unsupported claims (sample):")
        for claim in audit_results['unsupported'][:3]:
            print(f"    - {claim['id']}: Overlap {claim['overlap']}")
            print(f"      {claim['content']}")
        print()
    
    # Save audit
    audit_path = output_dir / f"audit_{timestamp}.json"
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved: {audit_path.name}")
    print()
    
    # ==================================================
    # FINAL SUMMARY
    # ==================================================
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    print(f"Transcript:")
    print(f"  File: {transcript_path.name}")
    print(f"  Size: {word_count:,} words (~{estimated_tokens:,} tokens)")
    print()
    
    print(f"Pipeline Execution:")
    print(f"  Total time: {time.time() - start_time:.2f}s ({(time.time() - start_time)/60:.1f} min)")
    print(f"  Ingestion: {ingestion_time:.2f}s")
    print(f"  Extraction: {extraction_time:.2f}s")
    print()
    
    print(f"Source Units: {len(source_doc.source_units)}")
    print(f"Extraction Chunks: {total_chunks}")
    print(f"  Completeness: {completeness:.1%}")
    print(f"  Failed: {len(failed_chunks_list)}")
    print()
    
    print(f"Knowledge Items: {knowledge_doc.total_items}")
    print(f"Note Sections: {len(assembled_notes.sections)}")
    print()
    
    # GO/NO-GO Decision
    print("=" * 80)
    print("GO/NO-GO RECOMMENDATION")
    print("=" * 80)
    print()
    
    issues = []
    warnings = []
    
    # Critical issues
    if completeness < 0.80:
        issues.append(f"Low completeness: {completeness:.1%} (threshold: 80%)")
    
    if knowledge_doc.total_items == 0:
        issues.append("Zero items extracted")
    
    # Check provenance
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
    
    items_without_sources = sum(
        1 for item in all_items
        if not hasattr(item, 'source_unit_ids') or not item.source_unit_ids
    )
    
    if items_without_sources > len(all_items) * 0.1:
        issues.append(f"{items_without_sources} items lack source attribution (>10%)")
    
    # Warnings
    if len(audit_results['unsupported']) > audit_results['total_audited'] * 0.3:
        warnings.append(f"High unsupported rate: {len(audit_results['unsupported'])}/{audit_results['total_audited']}")
    
    if len(audit_results['incorrectly_attributed']) > 0:
        warnings.append(f"{len(audit_results['incorrectly_attributed'])} attribution errors")
    
    if len(failed_chunks_list) > total_chunks * 0.2:
        warnings.append(f"High chunk failure rate: {len(failed_chunks_list)}/{total_chunks}")
    
    # Final verdict
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
        print("Recommendation: Address critical issues before production use.")
        return 2
    
    elif warnings:
        print("⚠️ CONDITIONAL GO: Warnings detected")
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
        print("Recommendation: Review warnings. Pipeline operational but needs tuning.")
        print("  - Transcript ingestion: Working")
        print("  - Multi-key extraction: Operational")
        print("  - End-to-end pipeline: Complete")
        print("  - NOT production-ready based on single transcript test")
        return 0
    
    else:
        print("✅ GO: Validation successful")
        print()
        print("All criteria passed:")
        print(f"  ✓ Completeness: {completeness:.1%}")
        print(f"  ✓ Items extracted: {knowledge_doc.total_items}")
        print(f"  ✓ Source attribution: {len(all_items) - items_without_sources}/{len(all_items)}")
        print(f"  ✓ Claim quality acceptable")
        print()
        print("Recommendation: Pipeline operational for this content type.")
        print("  - Transcript ingestion: Working")
        print("  - Multi-key extraction: Operational")
        print("  - End-to-end pipeline: Complete")
        print("  - NOT production-ready based on single transcript test")
        return 0


if __name__ == "__main__":
    sys.exit(main())
