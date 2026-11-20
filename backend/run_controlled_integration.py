#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlled Integration Test Runner

Runs the complete pipeline with a controlled fixture and configured MockLLMProvider.
This validates that the pipeline produces actual output (not zero-extraction).

Output goes to data/output/controlled_integration_test/
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
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


def main():
    """Run controlled integration test."""
    print(f"\n{'#'*80}")
    print(f"# CONTROLLED INTEGRATION TEST")
    print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")
    
    # Setup paths
    base_dir = Path(__file__).parent
    fixture_dir = base_dir / "tests" / "fixtures"
    output_dir = base_dir / "data" / "output" / "controlled_integration_test"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load controlled source
    source_path = fixture_dir / "controlled_source.json"
    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    source_doc = SourceDocument.model_validate(source_data)
    
    print(f"\nLoaded controlled source: {source_doc.document_id}")
    print(f"  - Source units: {len(source_doc.source_units)}")
    print(f"  - Units with text: {sum(1 for u in source_doc.source_units if u.text)}")
    
    # Load controlled mock response
    response_path = fixture_dir / "controlled_mock_response.json"
    with open(response_path, 'r', encoding='utf-8') as f:
        mock_response = json.load(f)
    
    # Configure mock provider
    mock_provider = MockLLMProvider(
        responses={},
        default_response=json.dumps(mock_response)
    )
    
    overall_start = time.time()
    
    try:
        # Step 1: Extract knowledge
        print(f"\n{'='*80}")
        print(f"STEP 1: EXTRACT KNOWLEDGE (Configured MockLLMProvider)")
        print(f"{'='*80}")
        
        extractor = KnowledgeExtractor(mock_provider, verbose=True)
        knowledge_doc = extractor.extract(source_doc)
        
        # Save
        knowledge_path = output_dir / "knowledge_document.json"
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Extracted {knowledge_doc.total_items} knowledge items")
        print(f"  - Output: {knowledge_path}")
        
        # Step 2: Analyze
        print(f"\n{'='*80}")
        print(f"STEP 2: ANALYZE KNOWLEDGE")
        print(f"{'='*80}")
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        analyzed_path = output_dir / "analyzed_knowledge.json"
        with open(analyzed_path, 'w', encoding='utf-8') as f:
            json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Analyzed {len(analyzed_doc.analyzed_items)} items")
        
        # Step 3: Select representation
        print(f"\n{'='*80}")
        print(f"STEP 3: SELECT REPRESENTATION")
        print(f"{'='*80}")
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        repr_path = output_dir / "representation.json"
        with open(repr_path, 'w', encoding='utf-8') as f:
            json.dump(represented_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Selected {len(represented_doc.representations)} representations")
        
        # Step 4: Assemble
        print(f"\n{'='*80}")
        print(f"STEP 4: ASSEMBLE NOTES")
        print(f"{'='*80}")
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        assembled_path = output_dir / "assembled_notes.json"
        with open(assembled_path, 'w', encoding='utf-8') as f:
            json.dump(assembled_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        total_assembled = sum(len(s.items) for s in assembled_doc.sections)
        print(f"✓ Assembled {len(assembled_doc.sections)} sections with {total_assembled} items")
        
        # Step 5: Render
        print(f"\n{'='*80}")
        print(f"STEP 5: RENDER MARKDOWN")
        print(f"{'='*80}")
        
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_doc)
        
        markdown_path = output_dir / "rendered_notes.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(rendered_doc.content)
        
        manifest_path = output_dir / "render_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(rendered_doc.manifest.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"✓ Rendered {len(rendered_doc.content)} characters")
        print(f"  - Manifest tracked {len(rendered_doc.manifest.items)} items")
        
        # Step 6: Evaluate
        print(f"\n{'='*80}")
        print(f"STEP 6: EVALUATE FAITHFULNESS")
        print(f"{'='*80}")
        
        evaluator = FaithfulnessEvaluator(verbose=True)
        evaluation = evaluator.evaluate(
            source_doc=source_doc,
            knowledge_doc=knowledge_doc,
            analyzed_doc=analyzed_doc,
            represented_doc=represented_doc,
            assembled_doc=assembled_doc,
            render_manifest=rendered_doc.manifest
        )
        
        eval_path = output_dir / "evaluation_report.json"
        with open(eval_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Evaluation complete")
        print(f"  - Status: {evaluation.status.status.upper()}")
        print(f"  - Pipeline complete: {evaluation.status.pipeline_complete}")
        print(f"  - End-to-end coverage: {evaluation.coverage.end_to_end_coverage_ratio:.1%}")
        
        # Step 7: Semantic verification
        print(f"\n{'='*80}")
        print(f"STEP 7: SEMANTIC VERIFICATION")
        print(f"{'='*80}")
        
        verifier = DeterministicSemanticVerifier(verbose=True)
        semantic_report = verifier.verify(knowledge_doc, source_doc)
        
        semantic_path = output_dir / "semantic_verification.json"
        with open(semantic_path, 'w', encoding='utf-8') as f:
            json.dump(semantic_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        supported = sum(
            1 for c in semantic_report.claim_verifications
            if c.verification_status.status == "SUPPORTED"
        )
        total = len(semantic_report.claim_verifications)
        
        print(f"\n✓ Semantic verification complete")
        print(f"  - Total claims: {total}")
        support_rate = (supported/total*100) if total > 0 else 0
        print(f"  - Supported: {supported} ({support_rate:.1f}%)")
        
        overall_elapsed = time.time() - overall_start
        
        # Summary
        print(f"\n{'#'*80}")
        print(f"# CONTROLLED INTEGRATION TEST COMPLETE")
        print(f"# Total time: {overall_elapsed:.2f}s")
        print(f"# Evaluation Status: {evaluation.status.status.upper()}")
        print(f"# Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")
        
        print(f"\n📁 All artifacts saved to: {output_dir}")
        
        # Print markdown preview
        print(f"\n{'='*80}")
        print(f"RENDERED MARKDOWN PREVIEW (first 500 chars)")
        print(f"{'='*80}")
        preview = rendered_doc.content[:500]
        print(preview)
        if len(rendered_doc.content) > 500:
            print(f"... ({len(rendered_doc.content) - 500} more characters)")
        
        # Exit code based on evaluation status
        if evaluation.status.status == "incomplete":
            return 2
        elif evaluation.status.status == "fail":
            return 1
        else:
            return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: Integration test failed")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
