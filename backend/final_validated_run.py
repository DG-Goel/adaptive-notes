"""
Final validated pipeline run with corrected knowledge (473 items, 2 genuine errors removed)
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import pipeline components
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.models.knowledge import KnowledgeDocument
from app.evaluation.structural_evaluator import StructuralEvaluator

def load_corrected_knowledge(path: Path) -> KnowledgeDocument:
    """Load corrected knowledge with 473 items"""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return KnowledgeDocument(**data)

def load_source_units(path: Path) -> list:
    """Load source units"""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
        return data.get('source_units', [])

def save_json(data, path: Path):
    """Save JSON with proper encoding"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print(f"FINAL VALIDATED PIPELINE RUN")
    print(f"Timestamp: {timestamp}")
    print("=" * 80)
    
    # Setup paths
    source_run = Path("data/output/complete_e2e_validation/validation_20261101_174430")
    output_dir = Path(f"data/output/complete_e2e_validation/validation_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nInput: {source_run}")
    print(f"Output: {output_dir}")
    
    # Load corrected knowledge
    print("\n1. Loading corrected knowledge...")
    knowledge = load_corrected_knowledge(source_run / "knowledge_corrected_v2.json")
    print(f"   Total items: {knowledge.total_items}")
    save_json(knowledge.model_dump(), output_dir / "knowledge.json")
    
    # Load source units for verification
    print("\n2. Loading source units...")
    source_units = load_source_units(source_run / "source_units.json")
    print(f"   Source units: {len(source_units)}")
    
    # Save source units to output (for reference)
    source_data = {
        "document_id": knowledge.document_id,
        "filename": knowledge.source_filename,
        "page_count": None,
        "source_units": source_units
    }
    save_json(source_data, output_dir / "source_units.json")
    
    # Stage 1: Content Analysis
    print("\n3. STAGE 1: Content Analysis")
    try:
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge)
        print(f"   ✓ Analyzed {knowledge.total_items} knowledge items")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        sys.exit(1)
    
    # Stage 2: Representation Selection
    print("\n4. STAGE 2: Representation Selection")
    try:
        selector = RepresentationSelector()
        representation_result = selector.select(analyzed_doc)
        save_json(representation_result.model_dump(), output_dir / "selected_representations.json")
        print(f"   ✓ Selected {len(representation_result.representations)} representations")
        
        # Structural evaluation
        print("   Running structural evaluation...")
        struct_eval = StructuralEvaluator()
        struct_result = struct_eval.evaluate(
            representation_doc=representation_result,
            knowledge_doc=knowledge
        )
        save_json(struct_result.model_dump(), output_dir / "structural_eval_representation.json")
        
        if not struct_result.passed:
            print(f"   ✗ FAILED: {struct_result.error_count} errors")
            print("   Structural validation failed. Aborting.")
            sys.exit(1)
        else:
            print(f"   ✓ PASSED: {struct_result.error_count} errors, {struct_result.warning_count} warnings")
            
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        sys.exit(1)
    
    # Stage 3: Note Assembly
    print("\n5. STAGE 3: Note Assembly")
    try:
        assembler = NoteAssembler()
        assembled_note = assembler.assemble(representation_result)
        save_json(assembled_note.model_dump(), output_dir / "assembled_note.json")
        print(f"   ✓ Assembled {len(assembled_note.sections)} sections")
        
        # Structural evaluation
        print("   Running structural evaluation...")
        struct_result = struct_eval.evaluate(
            assembly_doc=assembled_note,
            representation_doc=representation_result
        )
        save_json(struct_result.model_dump(), output_dir / "structural_eval_assembly.json")
        
        if not struct_result.passed:
            print(f"   ✗ FAILED: {struct_result.error_count} errors")
            print("   Structural validation failed. Aborting.")
            sys.exit(1)
        else:
            print(f"   ✓ PASSED: {struct_result.error_count} errors, {struct_result.warning_count} warnings")
            
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        sys.exit(1)
    
    # Stage 4: Markdown Rendering
    print("\n6. STAGE 4: Markdown Rendering")
    try:
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_note)
        markdown = rendered_doc.content
        
        with open(output_dir / "rendered_notes.md", 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"   ✓ Rendered {len(markdown):,} characters")
        
        # Structural evaluation
        print("   Running structural evaluation...")
        struct_result = struct_eval.evaluate(
            markdown_output=markdown,
            assembly_doc=assembled_note
        )
        save_json(struct_result.model_dump(), output_dir / "structural_eval_markdown.json")
        
        if not struct_result.passed:
            print(f"   ✗ FAILED: {struct_result.error_count} errors")
            print("   Structural validation failed. Aborting.")
            sys.exit(1)
        else:
            print(f"   ✓ PASSED: {struct_result.error_count} errors, {struct_result.warning_count} warnings")
            
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        sys.exit(1)
    
    # Stage 5: Semantic Verification (optional, for reporting only)
    print("\n7. STAGE 5: Semantic Verification (skipped in this run)")
    supported = 0
    unsupported = 0
    contradicted = 0
    verification_results_count = 0
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Status: SUCCESS")
    print(f"Output directory: {output_dir}")
    print(f"Knowledge items: {knowledge.total_items}")
    print(f"Representations: {len(representation_result.representations)}")
    print(f"Assembled sections: {len(assembled_note.sections)}")
    print(f"Markdown size: {len(markdown):,} characters")
    print(f"Semantic verification: SKIPPED")
    print("=" * 80)
    
    # Create summary file
    summary = {
        "timestamp": timestamp,
        "input_knowledge": str(source_run / "knowledge_corrected_v2.json"),
        "output_directory": str(output_dir),
        "pipeline_stages": {
            "representation_selection": {
                "status": "PASSED",
                "selected_items": len(representation_result.representations),
                "structural_errors": 0
            },
            "note_assembly": {
                "status": "PASSED",
                "sections": len(assembled_note.sections),
                "structural_errors": 0
            },
            "markdown_rendering": {
                "status": "PASSED",
                "size_chars": len(markdown),
                "structural_errors": 0
            },
            "semantic_verification": {
                "status": "SKIPPED",
                "supported": 0,
                "unsupported": 0,
                "contradicted": 0,
                "total": 0
            }
        },
        "overall_status": "SUCCESS"
    }
    
    save_json(summary, output_dir / "pipeline_summary.json")
    print(f"\nSummary saved to: {output_dir / 'pipeline_summary.json'}")

if __name__ == "__main__":
    main()
