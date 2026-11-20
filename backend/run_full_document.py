#!/usr/bin/env python3
"""
Full-document validation: All 109 source units.
After successful 18-unit validation across 2 consecutive runs.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import GroqProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.models.source import SourceDocument, SourceUnit


def main():
    # Configuration
    output_dir = Path(f"data/output/full_document_109_units_with_splitting")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_units_path = Path("data/output/fresh_ingestion_test/source_units.json")
    
    print("=" * 80)
    print("FULL DOCUMENT VALIDATION - 109 SOURCE UNITS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Output directory: {output_dir}")
    print(f"Python: {sys.version}")
    import groq
    print(f"Groq SDK: {groq.__version__}")
    print()
    
    # Load source units
    print("[1/8] Loading source units...")
    with open(source_units_path) as f:
        data = json.load(f)
    
    # Handle both list format and dict format
    if isinstance(data, list):
        all_units_raw = data
    elif isinstance(data, dict) and "source_units" in data:
        all_units_raw = data["source_units"]
    else:
        raise ValueError(f"Unexpected source_units format: {type(data)}")
    
    # Use ALL 109 units
    print(f"  Total available units: {len(all_units_raw)}")
    
    # Verify we have 109 units
    if len(all_units_raw) != 109:
        print(f"  WARNING: Expected 109 units, found {len(all_units_raw)}")
    
    selected_units_raw = all_units_raw
    actual_ids = [unit.get("source_id") for unit in selected_units_raw]
    
    print(f"  Using all {len(selected_units_raw)} units")
    print(f"  ID range: {actual_ids[0]} to {actual_ids[-1]}")
    
    # Convert to SourceUnit objects
    source_units = [SourceUnit(**unit) for unit in selected_units_raw]
    
    # Create SourceDocument
    source_doc = SourceDocument(
        document_id="full_document",
        filename="test.pdf",
        page_count=10,
        source_units=source_units
    )
    
    total_chars = sum(len(unit.text or "") for unit in source_units)
    print(f"  Total content: {total_chars:,} characters")
    print()
    
    # EXTRACTION with max_retries=2
    print("[2/8] Extracting knowledge (with retry logic, max_retries=2)...")
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        return 1
    
    provider = GroqProvider(
        model="openai/gpt-oss-120b",
        api_key=api_key,
        tokens_per_minute=8000  # On-demand tier limit
    )
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2048,
        max_retries=2,
        verbose=True,  # Show detailed extraction progress
        min_output_tokens=500,
        preferred_output_tokens=4000
    )
    
    knowledge_doc = extractor.extract(source_doc)
    
    # Save extraction output
    extraction_path = output_dir / "knowledge_document.json"
    with open(extraction_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Report extraction completeness
    metadata = knowledge_doc.extraction_metadata or {}
    total_chunks = metadata.get("total_chunks", 0)
    successful = metadata.get("successful_chunks", 0)
    failed = metadata.get("failed_chunks", [])
    completeness = metadata.get("completeness", 0.0)
    
    print()
    print("=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"  Total chunks: {total_chunks}")
    print(f"  Successful chunks: {successful}")
    print(f"  Failed chunks: {len(failed)}")
    print(f"  Completeness: {completeness:.1%}")
    print(f"  Extracted items: {len(knowledge_doc.get_all_items())}")
    
    if failed:
        print(f"  WARNING: FAILED CHUNK IDs: {failed}")
    
    # Record chunk details
    chunk_details = {
        "total_chunks": total_chunks,
        "successful_chunks": successful,
        "failed_chunks": failed,
        "completeness": completeness,
        "attempts_per_chunk": {}
    }
    
    # Try to get attempt counts if available
    if hasattr(extractor, 'chunk_attempts'):
        chunk_details["attempts_per_chunk"] = extractor.chunk_attempts
    
    # Save chunk details
    chunk_details_path = output_dir / "extraction_chunk_details.json"
    with open(chunk_details_path, "w", encoding="utf-8") as f:
        json.dump(chunk_details, f, indent=2, ensure_ascii=False)
    
    print()
    
    # Check for INCOMPLETE extraction
    if completeness < 1.0:
        print("INCOMPLETE EXTRACTION")
        print(f"   {len(failed)} chunk(s) failed after retries")
        print(f"   The generated notes represent only {completeness:.1%} of the document")
        print(f"   DO NOT use this output as complete notes")
        
        # Still save what we have for diagnostics
        print()
        print("Saving partial results for diagnostic purposes...")
        
        # Continue pipeline with partial data but mark as INCOMPLETE
        incomplete_flag_path = output_dir / "INCOMPLETE_EXTRACTION.txt"
        with open(incomplete_flag_path, "w") as f:
            f.write(f"INCOMPLETE EXTRACTION\n")
            f.write(f"Completeness: {completeness:.1%}\n")
            f.write(f"Failed chunks: {len(failed)}\n")
            f.write(f"Failed chunk IDs: {failed}\n")
            f.write(f"\nDO NOT USE THIS OUTPUT AS COMPLETE NOTES\n")
    
    # ANALYSIS
    print("[3/8] Analyzing knowledge characteristics...")
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    analysis_path = output_dir / "analyzed_knowledge.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Count items with high/medium confidence
    confident_count = sum(1 for item in analyzed_doc.analyzed_items 
                         if item.analysis_confidence in ("high", "medium"))
    print(f"  Analyzed {len(analyzed_doc.analyzed_items)} items")
    
    if analyzed_doc.analyzed_items:
        confidence_pct = confident_count / len(analyzed_doc.analyzed_items) * 100
        print(f"  High/medium confidence: {confident_count} ({confidence_pct:.1f}%)")
    else:
        print(f"  High/medium confidence: 0 (no items to analyze)")
    
    print()
    
    # REPRESENTATION
    print("[4/8] Selecting representations...")
    selector = RepresentationSelector()
    representation = selector.select(analyzed_doc)
    
    repr_path = output_dir / "representation.json"
    with open(repr_path, "w", encoding="utf-8") as f:
        json.dump(representation.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Selected representations for {len(representation.representations)} items")
    print()
    
    # ASSEMBLY
    print("[5/8] Assembling notes...")
    assembler = NoteAssembler()
    assembled = assembler.assemble(representation)
    
    assembly_path = output_dir / "assembled_notes.json"
    with open(assembly_path, "w", encoding="utf-8") as f:
        json.dump(assembled.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Assembled {len(assembled.sections)} sections")
    print()
    
    # RENDERING
    print("[6/8] Rendering markdown...")
    renderer = MarkdownRenderer()
    rendered = renderer.render(assembled)
    
    markdown_path = output_dir / "rendered_notes.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(rendered.content)
    
    manifest_path = output_dir / "render_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(rendered.manifest.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Rendered {len(rendered.content):,} characters")
    print(f"  Markdown saved to: {markdown_path}")
    print()
    
    # EVALUATION
    print("[7/8] Evaluating output quality...")
    evaluator = FaithfulnessEvaluator()
    evaluation = evaluator.evaluate(
        source_doc=source_doc,
        knowledge_doc=knowledge_doc,
        analyzed_doc=analyzed_doc,
        represented_doc=representation,
        assembled_doc=assembled,
        render_manifest=rendered.manifest
    )
    
    eval_path = output_dir / "evaluation_report.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Status: {evaluation.status.status}")
    print(f"  Errors: {evaluation.status.total_errors}")
    print(f"  Warnings: {evaluation.status.total_warnings}")
    print(f"  Coverage (end-to-end): {evaluation.coverage.end_to_end_coverage_ratio:.1%}")
    print(f"  Provenance valid: {evaluation.status.provenance_valid}")
    print()
    
    # SEMANTIC VERIFICATION
    print("[8/8] Running semantic verification...")
    verifier = DeterministicSemanticVerifier()
    verification = verifier.verify(
        knowledge_doc=knowledge_doc,
        source_doc=source_doc
    )
    
    verify_path = output_dir / "semantic_verification.json"
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump(verification.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Verified {verification.total_claims_verified} claims")
    print(f"  Supported: {verification.claims_supported} ({verification.claims_supported/verification.total_claims_verified*100:.1f}%)")
    print(f"  Unsupported: {verification.claims_unsupported}")
    print(f"  Contradicted: {verification.claims_contradicted}")
    print(f"  Inconclusive: {verification.claims_inconclusive}")
    print()
    
    # Final summary
    print("=" * 80)
    print("FULL DOCUMENT VALIDATION COMPLETE")
    print("=" * 80)
    print(f"[CHECK] Source units processed: {len(source_units)}")
    print(f"[CHECK] Extraction completeness: {completeness:.1%} ({successful}/{total_chunks} chunks)")
    print(f"[CHECK] Items extracted: {len(knowledge_doc.get_all_items())}")
    print(f"[CHECK] Items analyzed: {len(analyzed_doc.analyzed_items)} ({confident_count} high/medium confidence)")
    print(f"[CHECK] Evaluation status: {evaluation.status.status}")
    print(f"[CHECK] Coverage (end-to-end): {evaluation.coverage.end_to_end_coverage_ratio:.1%}")
    print(f"[CHECK] Provenance valid: {evaluation.status.provenance_valid}")
    print(f"[CHECK] Semantic faithfulness: {verification.claims_supported}/{verification.total_claims_verified} supported ({verification.claims_supported/verification.total_claims_verified*100:.1f}%)")
    
    if completeness == 1.0 and evaluation.status.status in ("pass", "warning"):
        print()
        print("SUCCESS: Full document processed completely")
        print(f"   All outputs saved to: {output_dir}")
        return 0
    elif completeness < 1.0:
        print()
        print("INCOMPLETE: Some chunks failed extraction")
        print(f"   Partial results saved for diagnostics")
        print(f"   See: {output_dir}/INCOMPLETE_EXTRACTION.txt")
        return 1
    else:
        print()
        print("WARNING: Review evaluation errors before using")
        return 0


if __name__ == "__main__":
    sys.exit(main())
