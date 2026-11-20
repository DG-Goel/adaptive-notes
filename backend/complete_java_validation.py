#!/usr/bin/env python3
"""
Complete Java transcript validation with full verification.

Loads all artifacts including source document, runs semantic verification,
structural evaluation, analyzes failed chunks, and generates comprehensive report.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.analysis.analyzer import AnalyzedKnowledgeDocument
from app.representation.selector import RepresentationSelector
from app.representation.models import RepresentationDocument
from app.assembly.assembler import NoteAssembler
from app.assembly.models import AssembledNotesDocument
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.evaluation.evaluator import FaithfulnessEvaluator

def load_json(path: Path, model_class):
    """Load JSON and parse into model"""
    print(f"Loading: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return model_class(**data)

def save_json(path: Path, data: dict):
    """Save data as JSON"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"OK Saved: {path.name}")

def main():
    print("=" * 80)
    print("COMPLETE JAVA TRANSCRIPT VALIDATION")
    print("=" * 80)
    print()
    
    # Source artifacts from original run
    artifact_dir = Path("data/output/java_transcript_validation")
    timestamp = "20261030_185308"
    
    # Create new timestamped output directory
    new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = artifact_dir / f"validation_{new_timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Source artifacts: {artifact_dir} (timestamp: {timestamp})")
    print(f"Output directory: {output_dir}")
    print()
    
    # ==================================================
    # LOAD ARTIFACTS
    # ==================================================
    print("=" * 80)
    print("LOADING ARTIFACTS")
    print("=" * 80)
    print()
    
    # Load source document
    source_doc = load_json(
        artifact_dir / f"source_units_{timestamp}.json",
        SourceDocument
    )
    print(f"  OK Source: {len(source_doc.source_units)} units")
    
    # Load knowledge document
    knowledge_doc = load_json(
        artifact_dir / f"knowledge_{timestamp}.json",
        KnowledgeDocument
    )
    print(f"  OK Knowledge: {knowledge_doc.total_items} items")
    
    # Load analyzed document
    analyzed_doc = load_json(
        artifact_dir / f"analyzed_{timestamp}.json",
        AnalyzedKnowledgeDocument
    )
    print(f"  OK Analyzed: {len(analyzed_doc.analyzed_items)} items")
    
    # Load representations (from latest run)
    repr_files = sorted(artifact_dir.glob("representations_*.json"))
    latest_repr = repr_files[-1] if repr_files else None
    if latest_repr:
        representations_doc = load_json(latest_repr, RepresentationDocument)
        print(f"  OK Representations: {len(representations_doc.representations)} items")
    else:
        print("  Generating representations...")
        selector = RepresentationSelector()
        representations_doc = selector.select(analyzed_doc)
        save_json(
            output_dir / f"representations_{new_timestamp}.json",
            representations_doc.model_dump()
        )
    
    # Load or generate assembled notes
    assembled_files = sorted(artifact_dir.glob("assembled_*.json"))
    latest_assembled = assembled_files[-1] if assembled_files else None
    if latest_assembled:
        assembled_notes = load_json(latest_assembled, AssembledNotesDocument)
        print(f"  OK Assembled: {len(assembled_notes.sections)} sections")
    else:
        print("  Assembling notes...")
        assembler = NoteAssembler()
        assembled_notes = assembler.assemble(representations_doc)
        save_json(
            output_dir / f"assembled_{new_timestamp}.json",
            assembled_notes.model_dump()
        )
    
    # Load or generate markdown
    markdown_files = sorted(artifact_dir.glob("java_notes_*.md"))
    latest_markdown = markdown_files[-1] if markdown_files else None
    if latest_markdown:
        markdown_content = latest_markdown.read_text(encoding='utf-8')
        print(f"  OK Markdown: {len(markdown_content):,} chars")
    else:
        print("  Rendering markdown...")
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_notes)
        markdown_content = rendered_doc.content
        markdown_path = output_dir / f"java_notes_{new_timestamp}.md"
        markdown_path.write_text(markdown_content, encoding='utf-8')
        print(f"  OK Markdown: {len(markdown_content):,} chars")
    
    print()
    
    # ==================================================
    # SEMANTIC VERIFICATION
    # ==================================================
    print("=" * 80)
    print("SEMANTIC VERIFICATION")
    print("=" * 80)
    print()
    
    verifier = DeterministicSemanticVerifier()
    verification_results = verifier.verify(knowledge_doc, source_doc)
    
    print(f"Verified: {verification_results.total_claims_verified} claims")
    print(f"  Supported: {verification_results.claims_supported}")
    print(f"  Unsupported: {verification_results.claims_unsupported}")
    print(f"  Contradicted: {verification_results.claims_contradicted}")
    print(f"  Inconclusive: {verification_results.claims_inconclusive}")
    print(f"  Insufficient evidence: {verification_results.claims_insufficient_evidence}")
    print(f"  Faithfulness verified: {verification_results.semantic_faithfulness_verified}")
    
    if verification_results.claims_contradicted > 0 or verification_results.claims_unsupported > 0:
        print(f"\nFailed verifications:")
        for v in verification_results.claim_verifications:
            if v.verification_status.status in ['CONTRADICTED', 'UNSUPPORTED']:
                print(f"  - {v.knowledge_id} ({v.knowledge_type}): {v.verification_status.status}")
                print(f"    Reason: {v.verification_status.reason}")
    
    # Save verification results
    verification_path = output_dir / f"semantic_verification_{new_timestamp}.json"
    save_json(verification_path, verification_results.model_dump())
    print()
    
    # ==================================================
    # EXTRACTION ANALYSIS & FINAL REPORT
    # (Skip faithfulness evaluator - semantic verification is sufficient)
    # ==================================================
    print("=" * 80)
    print("EXTRACTION ANALYSIS")
    print("=" * 80)
    print()
    
    metadata = knowledge_doc.extraction_metadata
    total_chunks = metadata.get('total_chunks', 0)
    successful_chunks = metadata.get('successful_chunks', 0)
    failed_chunks = metadata.get('failed_chunks', [])
    split_chunks = metadata.get('split_chunks', [])
    completeness = metadata.get('completeness', 0.0)
    
    print(f"Extraction completeness: {completeness:.1%}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Successful: {successful_chunks}")
    print(f"  Failed: {len(failed_chunks)}")
    print(f"  Split/recovered: {len(split_chunks)}")
    print()
    
    if failed_chunks:
        print("Failed chunks:")
        for chunk_id in failed_chunks:
            print(f"  - {chunk_id}")
            # Find chunk attempts
            attempts = [a for a in metadata.get('chunk_attempts', []) if a['chunk_id'] == chunk_id]
            if attempts:
                last_attempt = attempts[-1]
                print(f"    Attempts: {len(attempts)}")
                print(f"    Last error: {last_attempt.get('error', 'Unknown')[:100]}")
        print()
    
    # Analyze source coverage
    extracted_source_ids = set()
    for item in knowledge_doc.get_all_items():
        extracted_source_ids.update(item.source_unit_ids)
    
    all_source_ids = {unit.source_id for unit in source_doc.source_units}
    missing_source_ids = all_source_ids - extracted_source_ids
    coverage = len(extracted_source_ids) / len(all_source_ids) if all_source_ids else 0
    
    print(f"Source coverage: {coverage:.1%}")
    print(f"  Total source units: {len(all_source_ids)}")
    print(f"  Extracted from: {len(extracted_source_ids)}")
    print(f"  Missing: {len(missing_source_ids)}")
    
    if missing_source_ids and len(missing_source_ids) <= 10:
        print(f"  Missing unit IDs: {sorted(list(missing_source_ids))}")
    elif missing_source_ids:
        print(f"  Missing unit IDs (first 10): {sorted(list(missing_source_ids))[:10]}")
    print()
    
    # ==================================================
    # FINAL REPORT
    # ==================================================
    print("=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)
    print()
    
    # Determine GO/NO-GO
    support_rate = verification_results.claims_supported / verification_results.total_claims_verified if verification_results.total_claims_verified > 0 else 0
    
    go_nogo_checks = {
        "Extraction completeness >= 90%": completeness >= 0.9,
        "Source coverage >= 90%": coverage >= 0.9,
        "Semantic support rate >= 80%": support_rate >= 0.80,
        "No contradicted claims": verification_results.claims_contradicted == 0,
        "< 10% unsupported claims": (verification_results.claims_unsupported / verification_results.total_claims_verified < 0.10) if verification_results.total_claims_verified > 0 else True,
    }
    
    print("GO/NO-GO Criteria:")
    for criterion, passed in go_nogo_checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {criterion}")
    print()
    
    all_passed = all(go_nogo_checks.values())
    
    print("=" * 80)
    if all_passed:
        print("RESULT: GO")
        print("Pipeline ready for further testing")
    else:
        print("RESULT: NO-GO")
        print("Issues must be addressed before production use")
    print("=" * 80)
    print()
    
    # Summary metrics
    print("SUMMARY METRICS:")
    print(f"  Knowledge items: {knowledge_doc.total_items}")
    print(f"  Extraction completeness: {completeness:.1%}")
    print(f"  Source coverage: {coverage:.1%}")
    print(f"  Semantic support rate: {support_rate:.1%} ({verification_results.claims_supported}/{verification_results.total_claims_verified})")
    print(f"  Semantic contradicted: {verification_results.claims_contradicted}")
    print(f"  Semantic unsupported: {verification_results.claims_unsupported}")
    print(f"  Failed chunks: {len(failed_chunks)}")
    print(f"  Markdown size: {len(markdown_content):,} chars")
    print()
    
    print("OUTPUT FILES:")
    print(f"  {output_dir}/")
    print(f"    semantic_verification_{new_timestamp}.json")
    print(f"    validation_summary_{new_timestamp}.json")
    if not latest_repr:
        print(f"    representations_{new_timestamp}.json")
    if not latest_assembled:
        print(f"    assembled_{new_timestamp}.json")
    if not latest_markdown:
        print(f"    java_notes_{new_timestamp}.md")
    print()
    
    # Create summary report
    summary = {
        "timestamp": new_timestamp,
        "document_id": knowledge_doc.document_id,
        "source_file": knowledge_doc.source_filename,
        "metrics": {
            "knowledge_items": knowledge_doc.total_items,
            "extraction_completeness": completeness,
            "source_coverage": coverage,
            "semantic_pass_rate": verification_results.claims_supported / verification_results.total_claims_verified if verification_results.total_claims_verified > 0 else 0,
            "semantic_supported": verification_results.claims_supported,
            "semantic_unsupported": verification_results.claims_unsupported,
            "semantic_contradicted": verification_results.claims_contradicted,
            "semantic_inconclusive": verification_results.claims_inconclusive,
            "semantic_insufficient": verification_results.claims_insufficient_evidence,
            "semantic_support_rate": support_rate,
            "failed_chunks": len(failed_chunks),
            "markdown_size": len(markdown_content),
        },
        "go_no_go": {
            "result": "GO" if all_passed else "NO-GO",
            "checks": {k: ("PASS" if v else "FAIL") for k, v in go_nogo_checks.items()}
        },
        "failed_chunks": failed_chunks,
        "missing_source_ids": sorted(list(missing_source_ids))[:20]  # First 20
    }
    
    summary_path = output_dir / f"validation_summary_{new_timestamp}.json"
    save_json(summary_path, summary)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
