#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Pipeline Validation Script

Runs the complete Adaptive Notes pipeline on freshly ingested data:
1. Load fresh source_units.json (from fresh_ingestion_test)
2. Extract knowledge (using MockLLMProvider - NO REAL LLM)
3. Analyze knowledge characteristics and rules
4. Select representation format
5. Assemble notes sections
6. Render final output
7. Evaluate semantic faithfulness

All outputs go to data/output/fresh_e2e_test/ to avoid contaminating existing artifacts.

IMPORTANT: This uses MockLLMProvider, which returns canned/empty responses.
This validates pipeline MECHANICS, not real-world LLM performance.
"""

import json
import sys
import time
import os
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator


def load_fresh_source_document(path: Path) -> SourceDocument:
    """Load the freshly ingested source document."""
    print(f"\n{'='*80}")
    print(f"STEP 1: LOAD FRESH SOURCE DOCUMENT")
    print(f"{'='*80}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    source_doc = SourceDocument.model_validate(data)
    
    print(f"✓ Loaded source document: {source_doc.document_id}")
    print(f"  - Source units: {len(source_doc.source_units)}")
    print(f"  - File: {path}")
    
    return source_doc


def extract_knowledge(source_doc: SourceDocument, output_dir: Path) -> KnowledgeDocument:
    """Extract knowledge using MockLLMProvider."""
    print(f"\n{'='*80}")
    print(f"STEP 2: EXTRACT KNOWLEDGE (MOCK LLM - NOT REAL)")
    print(f"{'='*80}")
    print(f"⚠️  WARNING: Using MockLLMProvider (canned responses)")
    print(f"⚠️  This validates pipeline mechanics, NOT real LLM performance")
    
    start_time = time.time()
    
    # Use mock provider
    llm_provider = MockLLMProvider()
    extractor = KnowledgeExtractor(llm_provider)
    
    knowledge_doc = extractor.extract(source_doc)
    
    elapsed = time.time() - start_time
    
    # Save output
    output_path = output_dir / "knowledge_document.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Extraction complete in {elapsed:.2f}s")
    print(f"  - Knowledge items: {knowledge_doc.total_items}")
    print(f"  - Output: {output_path}")
    print(f"  - Provider: MockLLMProvider (NOT OpenAI)")
    
    return knowledge_doc


def analyze_knowledge(knowledge_doc: KnowledgeDocument, output_dir: Path):
    """Analyze knowledge characteristics and rules."""
    print(f"\n{'='*80}")
    print(f"STEP 3: ANALYZE KNOWLEDGE")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    elapsed = time.time() - start_time
    
    # Save output
    output_path = output_dir / "analyzed_knowledge.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Analysis complete in {elapsed:.2f}s")
    print(f"  - Analyzed items: {len(analyzed_doc.analyzed_items)}")
    print(f"  - Output: {output_path}")
    
    return analyzed_doc


def select_representation(analyzed_doc, output_dir: Path):
    """Select representation format."""
    print(f"\n{'='*80}")
    print(f"STEP 4: SELECT REPRESENTATION")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    selector = RepresentationSelector()
    representation_doc = selector.select(analyzed_doc)
    
    elapsed = time.time() - start_time
    
    # Save output
    output_path = output_dir / "representation.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(representation_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Representation selection complete in {elapsed:.2f}s")
    print(f"  - Representations: {len(representation_doc.representations)}")
    print(f"  - Output: {output_path}")
    
    return representation_doc


def assemble_notes(representation_doc, output_dir: Path):
    """Assemble notes sections."""
    print(f"\n{'='*80}")
    print(f"STEP 5: ASSEMBLE NOTES")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    assembler = NoteAssembler()
    assembled_doc = assembler.assemble(representation_doc)
    
    elapsed = time.time() - start_time
    
    # Save output
    output_path = output_dir / "assembled_notes.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(assembled_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    sections_count = len(assembled_doc.sections)
    
    print(f"✓ Assembly complete in {elapsed:.2f}s")
    print(f"  - Sections: {sections_count}")
    print(f"  - Output: {output_path}")
    
    return assembled_doc


def render_notes(assembled_doc, output_dir: Path):
    """Render final notes."""
    print(f"\n{'='*80}")
    print(f"STEP 6: RENDER NOTES")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    renderer = MarkdownRenderer()
    rendered_doc = renderer.render(assembled_doc)
    
    elapsed = time.time() - start_time
    
    # Save markdown output
    markdown_path = output_dir / "rendered_notes.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(rendered_doc.content)
    
    # Save manifest
    manifest_path = output_dir / "render_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(rendered_doc.manifest.model_dump(), f, indent=2, ensure_ascii=False)
    
    lines_count = rendered_doc.content.count('\n') + 1
    chars_count = len(rendered_doc.content)
    
    print(f"✓ Rendering complete in {elapsed:.2f}s")
    print(f"  - Lines: {lines_count}")
    print(f"  - Characters: {chars_count}")
    print(f"  - Markdown: {markdown_path}")
    print(f"  - Manifest: {manifest_path}")
    
    return rendered_doc


def evaluate_faithfulness(source_doc: SourceDocument, knowledge_doc: KnowledgeDocument, 
                         analyzed_doc, represented_doc, assembled_doc, rendered_doc, 
                         output_dir: Path) -> dict:
    """Evaluate semantic faithfulness."""
    print(f"\n{'='*80}")
    print(f"STEP 7: EVALUATE FAITHFULNESS")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    evaluator = FaithfulnessEvaluator()
    evaluation_result = evaluator.evaluate(
        source_doc=source_doc,
        knowledge_doc=knowledge_doc,
        analyzed_doc=analyzed_doc,
        represented_doc=represented_doc,
        assembled_doc=assembled_doc,
        render_manifest=rendered_doc.manifest
    )
    
    elapsed = time.time() - start_time
    
    # Save output
    output_path = output_dir / "evaluation_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation_result.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Extract key metrics
    coverage = evaluation_result.coverage
    
    print(f"✓ Evaluation complete in {elapsed:.2f}s")
    print(f"  - End-to-end coverage: {coverage.end_to_end_coverage_ratio:.1%}")
    print(f"  - Items extracted: {coverage.total_knowledge_items_extracted}")
    print(f"  - Items rendered: {coverage.total_items_rendered}")
    print(f"  - Output: {output_path}")
    
    return evaluation_result


def verify_no_artifact_reuse(output_dir: Path, fresh_ingestion_dir: Path):
    """Verify that all artifacts are fresh (not reused from old runs)."""
    print(f"\n{'='*80}")
    print(f"ARTIFACT FRESHNESS VERIFICATION")
    print(f"{'='*80}")
    
    expected_files = [
        "knowledge_document.json",
        "analyzed_knowledge.json",
        "representation.json",
        "assembled_notes.json",
        "rendered_notes.md",
        "render_manifest.json",
        "evaluation_report.json"
    ]
    
    # Check source units are from fresh ingestion
    source_path = fresh_ingestion_dir / "source_units.json"
    if source_path.exists():
        source_stat = source_path.stat()
        print(f"✓ Source artifact: {source_path}")
        print(f"  - Created: {datetime.fromtimestamp(source_stat.st_ctime)}")
        print(f"  - Size: {source_stat.st_size:,} bytes")
    
    # Check all output artifacts
    all_fresh = True
    for filename in expected_files:
        file_path = output_dir / filename
        if file_path.exists():
            stat = file_path.stat()
            age_seconds = time.time() - stat.st_mtime
            is_fresh = age_seconds < 300  # Less than 5 minutes old
            
            status = "✓ FRESH" if is_fresh else "⚠ OLD"
            print(f"{status}: {filename}")
            print(f"  - Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            print(f"  - Age: {age_seconds:.1f}s ago")
            
            if not is_fresh:
                all_fresh = False
        else:
            print(f"✗ MISSING: {filename}")
            all_fresh = False
    
    if all_fresh:
        print(f"\n✓ All artifacts are fresh (created during this run)")
    else:
        print(f"\n⚠ Some artifacts are old or missing")
    
    return all_fresh


def main():
    """Run complete end-to-end validation."""
    print(f"\n{'#'*80}")
    print(f"# END-TO-END PIPELINE VALIDATION (MOCK LLM)")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # Setup paths
    base_dir = Path(__file__).parent
    fresh_ingestion_dir = base_dir / "data" / "output" / "fresh_ingestion_test"
    output_dir = base_dir / "data" / "output" / "fresh_e2e_test"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Input path
    source_path = fresh_ingestion_dir / "source_units.json"
    
    if not source_path.exists():
        print(f"✗ ERROR: Fresh source document not found at {source_path}")
        print(f"  Run validate_fresh_ingestion.py first to generate fresh artifacts")
        return 1
    
    overall_start = time.time()
    
    try:
        # Step 1: Load fresh source document
        source_doc = load_fresh_source_document(source_path)
        
        # Step 2: Extract knowledge (MOCK)
        knowledge_doc = extract_knowledge(source_doc, output_dir)
        
        # Step 3: Analyze knowledge
        analyzed_doc = analyze_knowledge(knowledge_doc, output_dir)
        
        # Step 4: Select representation
        represented_doc = select_representation(analyzed_doc, output_dir)
        
        # Step 5: Assemble notes
        assembled_doc = assemble_notes(represented_doc, output_dir)
        
        # Step 6: Render notes
        rendered_doc = render_notes(assembled_doc, output_dir)
        
        # Step 7: Evaluate faithfulness
        evaluation_result = evaluate_faithfulness(
            source_doc, knowledge_doc, analyzed_doc, represented_doc, 
            assembled_doc, rendered_doc, output_dir
        )
        
        # Verify artifact freshness
        verify_no_artifact_reuse(output_dir, fresh_ingestion_dir)
        
        overall_elapsed = time.time() - overall_start
        
        print(f"\n{'#'*80}")
        print(f"# END-TO-END VALIDATION COMPLETE")
        print(f"# Total time: {overall_elapsed:.2f}s")
        print(f"# Evaluation Status: {evaluation_result.status.status.upper()}")
        print(f"# Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")
        
        print(f"\n📁 All artifacts saved to: {output_dir}")
        
        # Report evaluation status
        print(f"\n{'='*80}")
        print(f"EVALUATION SUMMARY")
        print(f"{'='*80}")
        print(f"Status: {evaluation_result.status.status.upper()}")
        print(f"Message: {evaluation_result.status.summary_message}")
        print(f"Pipeline Complete: {evaluation_result.status.pipeline_complete}")
        print(f"Coverage Acceptable: {evaluation_result.status.coverage_acceptable}")
        print(f"Errors: {evaluation_result.status.total_errors}")
        print(f"Warnings: {evaluation_result.status.total_warnings}")
        print(f"{'='*80}")
        
        print(f"\n⚠️  IMPORTANT REMINDER:")
        print(f"   This validation used MockLLMProvider (canned responses)")
        print(f"   Results validate pipeline MECHANICS, not real-world LLM performance")
        print(f"   For real validation, set OPENAI_API_KEY and use OpenAIProvider")
        
        # Return appropriate exit code based on status
        if evaluation_result.status.status == "incomplete":
            return 2  # Distinct exit code for incomplete pipeline
        elif evaluation_result.status.status == "fail":
            return 1
        else:
            return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: Pipeline validation failed")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
