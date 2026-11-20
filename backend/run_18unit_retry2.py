#!/usr/bin/env python3
"""
Second consecutive 18-unit validation to confirm extraction reliability.
Uses exact same source unit IDs as retry1: S0012, S0013, S0016, S0017, S0020, S0022, 
S0023, S0024, S0027, S0028, S0029, S0030, S0036, S0037, S0041, S0042, S0044, S0047
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
    output_dir = Path("data/output/real_llm_validation_15_20_retry2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_units_path = Path("data/output/fresh_ingestion_test/source_units.json")
    
    print("=" * 80)
    print("18-UNIT VALIDATION - RETRY 2 (reliability confirmation)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Output directory: {output_dir}")
    print(f"Python: {sys.version}")
    import groq
    print(f"Groq SDK: {groq.__version__}")
    print()
    
    # Load source units
    print("[1/7] Loading source units...")
    with open(source_units_path) as f:
        data = json.load(f)
    
    # Handle both list format and dict format
    if isinstance(data, list):
        all_units_raw = data
    elif isinstance(data, dict) and "source_units" in data:
        all_units_raw = data["source_units"]
    else:
        raise ValueError(f"Unexpected source_units format: {type(data)}")
    
    # Select EXACT same 18 units as retry1: indices 11-28 (S0012-S0047)
    # But we need to verify these are the correct IDs
    selected_indices = [11, 12, 15, 16, 19, 21, 22, 23, 26, 27, 28, 29, 35, 36, 40, 41, 43, 46]
    expected_ids = ["S0012", "S0013", "S0016", "S0017", "S0020", "S0022", "S0023", "S0024", 
                    "S0027", "S0028", "S0029", "S0030", "S0036", "S0037", "S0041", "S0042", "S0044", "S0047"]
    
    selected_units_raw = [all_units_raw[i] for i in selected_indices]
    actual_ids = [unit.get("source_id") for unit in selected_units_raw]
    
    print(f"  Expected IDs: {expected_ids}")
    print(f"  Actual IDs:   {actual_ids}")
    
    if actual_ids != expected_ids:
        print("  WARNING: Unit ID mismatch! Using indices 11-28 instead.")
        selected_units_raw = all_units_raw[11:29]
        actual_ids = [unit.get("source_id") for unit in selected_units_raw]
        print(f"  Fallback IDs: {actual_ids}")
    
    print(f"  Selected {len(selected_units_raw)} units")
    
    # Convert to SourceUnit objects
    source_units = [SourceUnit(**unit) for unit in selected_units_raw]
    
    # Create SourceDocument
    source_doc = SourceDocument(
        document_id="test_doc",
        filename="test.pdf",
        page_count=10,
        source_units=source_units
    )
    
    total_chars = sum(len(unit.text or "") for unit in source_units)
    print(f"  Total content: {total_chars:,} characters")
    print()
    
    # EXTRACTION with max_retries=2
    print("[2/7] Extracting knowledge (with retry logic, max_retries=2)...")
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        return 1
    
    provider = GroqProvider(
        model="openai/gpt-oss-120b",
        api_key=api_key
    )
    extractor = KnowledgeExtractor(
        llm_provider=provider,
        max_tokens_per_chunk=2048,
        max_retries=2  # Enable retry logic
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
    
    print(f"  Extracted {len(knowledge_doc.get_all_items())} items from {successful}/{total_chunks} chunks")
    print(f"  Completeness: {completeness:.1%}")
    if failed:
        print(f"  WARNING: Failed chunks: {failed}")
    
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
    
    # Check for GO/NO-GO
    if completeness < 0.95:
        print("NO-GO: Completeness below 95%")
        print(f"   Failed chunks ({len(failed)}): {failed}")
        return 1
    
    # ANALYSIS
    print("[3/7] Analyzing knowledge characteristics...")
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    analysis_path = output_dir / "analyzed_knowledge.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Count items with high/medium confidence (proxy for "supported")
    confident_count = sum(1 for item in analyzed_doc.analyzed_items 
                         if item.analysis_confidence in ("high", "medium"))
    print(f"  Analyzed {len(analyzed_doc.analyzed_items)} items, {confident_count} high/medium confidence ({confident_count/len(analyzed_doc.analyzed_items)*100:.1f}%)")
    print()
    
    # REPRESENTATION
    print("[4/7] Selecting representations...")
    selector = RepresentationSelector()
    representation = selector.select(analyzed_doc)
    
    repr_path = output_dir / "representation.json"
    with open(repr_path, "w", encoding="utf-8") as f:
        json.dump(representation.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Selected representations for {len(representation.representations)} items")
    print()
    
    # ASSEMBLY
    print("[5/7] Assembling notes...")
    assembler = NoteAssembler()
    assembled = assembler.assemble(representation)
    
    assembly_path = output_dir / "assembled_notes.json"
    with open(assembly_path, "w", encoding="utf-8") as f:
        json.dump(assembled.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Assembled {len(assembled.sections)} sections")
    print()
    
    # RENDERING
    print("[6/7] Rendering markdown...")
    renderer = MarkdownRenderer()
    rendered = renderer.render(assembled)
    
    markdown_path = output_dir / "rendered_notes.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(rendered.content)
    
    manifest_path = output_dir / "render_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(rendered.manifest.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"  Rendered {len(rendered.content)} characters")
    print(f"  Markdown saved to: {markdown_path}")
    print()
    
    # EVALUATION
    print("[7/7] Evaluating output quality...")
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
    
    print(f"  Errors: {evaluation.status.total_errors}")
    print(f"  Warnings: {evaluation.status.total_warnings}")
    print(f"  Coverage (end-to-end): {evaluation.coverage.end_to_end_coverage_ratio:.1%}")
    print(f"  Provenance valid: {evaluation.status.provenance_valid}")
    print()
    
    # SEMANTIC VERIFICATION
    print("[BONUS] Running semantic verification...")
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
    print()
    
    # Final summary
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"[CHECK] Extraction completeness: {completeness:.1%} ({successful}/{total_chunks} chunks)")
    print(f"[CHECK] Items extracted: {len(knowledge_doc.get_all_items())}")
    print(f"[CHECK] Items analyzed: {len(analyzed_doc.analyzed_items)} ({confident_count} high/medium confidence)")
    print(f"[CHECK] Evaluation status: {evaluation.status.status}")
    print(f"[CHECK] Coverage (end-to-end): {evaluation.coverage.end_to_end_coverage_ratio:.1%}")
    print(f"[CHECK] Semantic faithfulness: {verification.claims_supported}/{verification.total_claims_verified} supported ({verification.claims_supported/verification.total_claims_verified*100:.1f}%)")
    
    if completeness == 1.0 and evaluation.status.status in ("pass", "warning"):
        print()
        print("GO: Second validation successful")
        print(f"   All outputs saved to: {output_dir}")
        return 0
    else:
        print()
        print("CONDITIONAL: Review results before proceeding")
        return 0


if __name__ == "__main__":
    sys.exit(main())
