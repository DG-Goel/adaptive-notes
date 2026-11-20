"""
End-to-end evaluation tests using real pipeline output.
"""

import json
from pathlib import Path
import pytest
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.analysis.characteristics import AnalyzedKnowledgeDocument
from app.representation.models import RepresentationDocument
from app.assembly.models import AssembledNotesDocument
from app.rendering.models import RenderManifest


class TestEvaluationE2E:
    """End-to-end evaluation tests."""
    
    def test_evaluate_real_pipeline_output(self):
        """Evaluate the real pipeline output files."""
        
        # Check if all files exist
        required_files = [
            'data/output/source_units.json',
            'data/output/knowledge_document.json',
            'data/output/analyzed_knowledge.json',
            'data/output/representations.json',
            'data/output/assembled_notes.json',
            'data/output/render_manifest.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                pytest.skip(f"{file_path} not found")
        
        # Load all documents
        with open('data/output/source_units.json', 'r', encoding='utf-8') as f:
            source_doc = SourceDocument(**json.load(f))
        
        with open('data/output/knowledge_document.json', 'r', encoding='utf-8') as f:
            knowledge_doc = KnowledgeDocument(**json.load(f))
        
        with open('data/output/analyzed_knowledge.json', 'r', encoding='utf-8') as f:
            analyzed_doc = AnalyzedKnowledgeDocument(**json.load(f))
        
        with open('data/output/representations.json', 'r', encoding='utf-8') as f:
            represented_doc = RepresentationDocument(**json.load(f))
        
        with open('data/output/assembled_notes.json', 'r', encoding='utf-8') as f:
            assembled_doc = AssembledNotesDocument(**json.load(f))
        
        with open('data/output/render_manifest.json', 'r', encoding='utf-8') as f:
            render_manifest = RenderManifest(**json.load(f))
        
        # Evaluate
        evaluator = FaithfulnessEvaluator(verbose=True)
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Validate result structure
        assert result is not None
        assert result.evaluation_timestamp is not None
        assert result.document_id == source_doc.document_id
        assert result.source_filename == source_doc.filename
        
        # Check coverage metrics
        assert result.coverage.total_source_units == len(source_doc.source_units)
        assert result.coverage.total_knowledge_items_extracted > 0
        assert result.coverage.total_items_assembled >= 0
        assert result.coverage.total_items_rendered >= 0
        
        # Check coverage ratios are valid
        assert 0.0 <= result.coverage.extraction_coverage_ratio <= 1.0
        assert 0.0 <= result.coverage.assembly_coverage_ratio <= 1.0
        assert 0.0 <= result.coverage.rendering_coverage_ratio <= 1.0
        assert 0.0 <= result.coverage.end_to_end_coverage_ratio <= 1.0
        
        # Check status
        assert result.status.status in ["pass", "warning", "fail", "incomplete"]
        assert result.status.total_errors >= 0
        assert result.status.total_warnings >= 0
        
        # Check per-item findings
        assert len(result.item_findings) == result.coverage.total_knowledge_items_extracted
        
        # Verify semantic faithfulness NOT claimed
        assert result.semantic_faithfulness_verified is False
        
        # Print summary
        print(f"\n=== Evaluation Summary ===")
        print(f"Status: {result.status.status.upper()}")
        print(f"Total errors: {result.status.total_errors}")
        print(f"Total warnings: {result.status.total_warnings}")
        print(f"\nCoverage:")
        print(f"  Extracted: {result.coverage.total_knowledge_items_extracted}")
        print(f"  Assembled: {result.coverage.total_items_assembled}")
        print(f"  Rendered: {result.coverage.total_items_rendered}")
        print(f"  Assembly coverage: {result.coverage.assembly_coverage_ratio:.1%}")
        print(f"  Rendering coverage: {result.coverage.rendering_coverage_ratio:.1%}")
        print(f"  End-to-end: {result.coverage.end_to_end_coverage_ratio:.1%}")
        
        if result.provenance_errors:
            print(f"\nProvenance errors: {len(result.provenance_errors)}")
            for err in result.provenance_errors[:3]:
                print(f"  - {err.error_type}: {err.message[:80]}")
        
        if result.representation_errors:
            print(f"\nRepresentation errors: {len(result.representation_errors)}")
            for err in result.representation_errors[:3]:
                print(f"  - {err.error_type}: {err.message[:80]}")
        
        if result.content_warnings:
            print(f"\nContent warnings: {len(result.content_warnings)}")
            for warn in result.content_warnings[:3]:
                print(f"  - {warn.warning_type}: {warn.message[:80]}")
    
    def test_save_evaluation_report(self, tmp_path):
        """Test saving evaluation report to file."""
        
        required_files = [
            'data/output/source_units.json',
            'data/output/knowledge_document.json',
            'data/output/analyzed_knowledge.json',
            'data/output/representations.json',
            'data/output/assembled_notes.json',
            'data/output/render_manifest.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                pytest.skip(f"{file_path} not found")
        
        # Load documents
        with open('data/output/source_units.json', 'r', encoding='utf-8') as f:
            source_doc = SourceDocument(**json.load(f))
        
        with open('data/output/knowledge_document.json', 'r', encoding='utf-8') as f:
            knowledge_doc = KnowledgeDocument(**json.load(f))
        
        with open('data/output/analyzed_knowledge.json', 'r', encoding='utf-8') as f:
            analyzed_doc = AnalyzedKnowledgeDocument(**json.load(f))
        
        with open('data/output/representations.json', 'r', encoding='utf-8') as f:
            represented_doc = RepresentationDocument(**json.load(f))
        
        with open('data/output/assembled_notes.json', 'r', encoding='utf-8') as f:
            assembled_doc = AssembledNotesDocument(**json.load(f))
        
        with open('data/output/render_manifest.json', 'r', encoding='utf-8') as f:
            render_manifest = RenderManifest(**json.load(f))
        
        # Evaluate
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Save report
        report_path = tmp_path / "evaluation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))
        
        # Verify file created
        assert report_path.exists()
        assert report_path.stat().st_size > 0
        
        # Verify can be loaded back
        with open(report_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['document_id'] == result.document_id
        assert loaded_data['status']['status'] == result.status.status
        
        print(f"\n✓ Evaluation report saved to {report_path} ({report_path.stat().st_size} bytes)")
    
    def test_deterministic_evaluation_on_real_data(self):
        """Test that evaluation on real data is deterministic."""
        
        required_files = [
            'data/output/source_units.json',
            'data/output/knowledge_document.json',
            'data/output/analyzed_knowledge.json',
            'data/output/representations.json',
            'data/output/assembled_notes.json',
            'data/output/render_manifest.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                pytest.skip(f"{file_path} not found")
        
        # Load documents
        with open('data/output/source_units.json', 'r', encoding='utf-8') as f:
            source_doc = SourceDocument(**json.load(f))
        
        with open('data/output/knowledge_document.json', 'r', encoding='utf-8') as f:
            knowledge_doc = KnowledgeDocument(**json.load(f))
        
        with open('data/output/analyzed_knowledge.json', 'r', encoding='utf-8') as f:
            analyzed_doc = AnalyzedKnowledgeDocument(**json.load(f))
        
        with open('data/output/representations.json', 'r', encoding='utf-8') as f:
            represented_doc = RepresentationDocument(**json.load(f))
        
        with open('data/output/assembled_notes.json', 'r', encoding='utf-8') as f:
            assembled_doc = AssembledNotesDocument(**json.load(f))
        
        with open('data/output/render_manifest.json', 'r', encoding='utf-8') as f:
            render_manifest = RenderManifest(**json.load(f))
        
        # Evaluate twice
        evaluator = FaithfulnessEvaluator()
        
        result1 = evaluator.evaluate(
            source_doc, knowledge_doc, analyzed_doc,
            represented_doc, assembled_doc, render_manifest
        )
        
        result2 = evaluator.evaluate(
            source_doc, knowledge_doc, analyzed_doc,
            represented_doc, assembled_doc, render_manifest
        )
        
        # Compare results (ignore timestamps)
        assert result1.status.status == result2.status.status
        assert result1.coverage.total_knowledge_items_extracted == result2.coverage.total_knowledge_items_extracted
        assert result1.coverage.assembly_coverage_ratio == result2.coverage.assembly_coverage_ratio
        assert result1.coverage.rendering_coverage_ratio == result2.coverage.rendering_coverage_ratio
        assert len(result1.provenance_errors) == len(result2.provenance_errors)
        assert len(result1.representation_errors) == len(result2.representation_errors)
        assert len(result1.content_warnings) == len(result2.content_warnings)
        assert len(result1.item_findings) == len(result2.item_findings)
        
        print("\n✓ Evaluation is deterministic on real data")
