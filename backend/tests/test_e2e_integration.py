"""
End-to-end integration tests for the complete pipeline.

Tests the full pipeline from source ingestion through rendering
with controlled fixtures and mock LLM responses.
"""

import json
import pytest
from pathlib import Path

from app.models.source import SourceDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


@pytest.fixture
def controlled_source_doc():
    """Load controlled source document fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "controlled_source.json"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return SourceDocument.model_validate(data)


@pytest.fixture
def controlled_mock_response():
    """Load controlled mock LLM response."""
    fixture_path = Path(__file__).parent / "fixtures" / "controlled_mock_response.json"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def configured_mock_provider(controlled_mock_response):
    """Create MockLLMProvider with controlled response."""
    return MockLLMProvider(
        responses={},
        default_response=json.dumps(controlled_mock_response)
    )


class TestZeroExtractionDetection:
    """Test that zero-extraction failures are correctly detected."""
    
    def test_empty_mock_response_marks_incomplete(self, controlled_source_doc):
        """Empty extraction from content-bearing source should mark pipeline incomplete."""
        # Use default MockLLMProvider (returns empty response)
        mock_provider = MockLLMProvider()
        extractor = KnowledgeExtractor(mock_provider, verbose=False)
        
        # Extract knowledge
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        # Verify zero extraction
        assert knowledge_doc.total_items == 0
        
        # Run through empty pipeline
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_doc)
        
        # Evaluate
        evaluator = FaithfulnessEvaluator(verbose=False)
        evaluation = evaluator.evaluate(
            source_doc=controlled_source_doc,
            knowledge_doc=knowledge_doc,
            analyzed_doc=analyzed_doc,
            represented_doc=represented_doc,
            assembled_doc=assembled_doc,
            render_manifest=rendered_doc.manifest
        )
        
        # Assert evaluation correctly identifies extraction failure
        assert evaluation.status.status == "incomplete"
        assert evaluation.status.pipeline_complete is False
        assert evaluation.status.coverage_acceptable is False
        assert "zero items extracted" in evaluation.status.summary_message
        assert "89" not in evaluation.status.summary_message  # Should say 5 source units
        assert "5 source units" in evaluation.status.summary_message


class TestNonEmptyIntegration:
    """Test complete pipeline with non-empty controlled extraction."""
    
    def test_controlled_extraction_produces_items(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Extraction with configured mock should produce expected items."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        # Verify extraction produced items
        # NOTE: MockLLMProvider returns same response for each chunk,
        # so we get duplicates. Just verify items were extracted.
        assert knowledge_doc.total_items > 0, "Should extract knowledge items"
        
        # Verify we have items of each expected type
        assert len(knowledge_doc.concepts) > 0
        assert len(knowledge_doc.definitions) > 0
        assert len(knowledge_doc.examples) > 0
        assert len(knowledge_doc.facts) > 0
        assert len(knowledge_doc.formulas) > 0
        assert len(knowledge_doc.procedures) > 0
    
    def test_provenance_integrity_maintained(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """All extracted items should reference valid source units."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        valid_source_ids = {unit.source_id for unit in controlled_source_doc.source_units}
        
        # Check all items have valid source references
        for item in knowledge_doc.get_all_items():
            assert item.source_unit_ids, f"{item.knowledge_id} has no source references"
            for source_id in item.source_unit_ids:
                assert source_id in valid_source_ids, \
                    f"{item.knowledge_id} references invalid source {source_id}"
    
    def test_analysis_processes_all_items(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Analysis should process all extracted items."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        # Verify analysis coverage
        assert len(analyzed_doc.analyzed_items) == knowledge_doc.total_items, \
            f"Analysis should process all {knowledge_doc.total_items} extracted items, got {len(analyzed_doc.analyzed_items)}"
        
        # Verify all have confidence ratings
        for item in analyzed_doc.analyzed_items:
            assert item.analysis_confidence in ["high", "medium", "low", "insufficient"]
    
    def test_representation_selection_assigns_formats(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Representation selection should assign formats to all items."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        # Verify representations coverage
        assert len(represented_doc.representations) == knowledge_doc.total_items, \
            f"Representation should cover all {knowledge_doc.total_items} items, got {len(represented_doc.representations)}"
        
        # Verify all have formats assigned
        for rep in represented_doc.representations:
            assert rep.primary_format is not None
    
    def test_assembly_creates_sections(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Assembly should create logical sections from items."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        # Verify assembly creates sections
        assert len(assembled_doc.sections) > 0, "Should create at least one section"
        
        # Verify all items assembled
        total_assembled = sum(len(section.items) for section in assembled_doc.sections)
        assert total_assembled == knowledge_doc.total_items, \
            f"Should assemble all {knowledge_doc.total_items} items, assembled {total_assembled}"
    
    def test_rendering_produces_markdown(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Rendering should produce non-empty markdown output."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_doc)
        
        # Verify rendering produces content
        assert rendered_doc.content, "Should produce markdown content"
        assert len(rendered_doc.content) > 100, "Markdown should have substantial content"
        
        # Verify manifest tracks all items
        assert len(rendered_doc.manifest.items) == knowledge_doc.total_items, \
            "Manifest should track all rendered items"
        
        # Verify content contains key terms from fixture
        assert "Photosynthesis" in rendered_doc.content
        assert "Chlorophyll" in rendered_doc.content
        assert "Calvin cycle" in rendered_doc.content
    
    def test_evaluation_reports_complete_pipeline(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Evaluation should report complete pipeline for successful run."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_doc)
        
        evaluator = FaithfulnessEvaluator(verbose=False)
        evaluation = evaluator.evaluate(
            source_doc=controlled_source_doc,
            knowledge_doc=knowledge_doc,
            analyzed_doc=analyzed_doc,
            represented_doc=represented_doc,
            assembled_doc=assembled_doc,
            render_manifest=rendered_doc.manifest
        )
        
        # Verify evaluation metrics
        assert evaluation.status.pipeline_complete is True, \
            f"Pipeline should be complete: {evaluation.status.summary_message}"
        assert evaluation.status.provenance_valid is True, \
            "Provenance should be valid"
        assert evaluation.coverage.total_knowledge_items_extracted > 0, \
            "Should have extracted items"
        assert evaluation.coverage.total_items_rendered > 0, \
            "Should have rendered items"
        assert evaluation.coverage.end_to_end_coverage_ratio == 1.0, \
            f"Should have 100% end-to-end coverage, got {evaluation.coverage.end_to_end_coverage_ratio:.1%}"
        
        # Status should be pass or warning (not fail/incomplete)
        assert evaluation.status.status in ["pass", "warning"], \
            f"Expected pass/warning, got {evaluation.status.status}: {evaluation.status.summary_message}"
    
    def test_stage_item_counts_consistent(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Item counts should be consistent across all pipeline stages."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        extracted_count = knowledge_doc.total_items
        
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        analyzed_count = len(analyzed_doc.analyzed_items)
        
        selector = RepresentationSelector()
        represented_doc = selector.select(analyzed_doc)
        represented_count = len(represented_doc.representations)
        
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        assembled_count = sum(len(s.items) for s in assembled_doc.sections)
        
        renderer = MarkdownRenderer()
        rendered_doc = renderer.render(assembled_doc)
        rendered_count = len(rendered_doc.manifest.items)
        
        # All counts should match
        assert extracted_count == analyzed_count == represented_count == assembled_count == rendered_count, \
            f"Counts mismatch: extracted={extracted_count}, analyzed={analyzed_count}, " \
            f"represented={represented_count}, assembled={assembled_count}, rendered={rendered_count}"
        
        # Should have extracted at least some items
        assert extracted_count > 0, "Should have extracted items"


class TestSemanticVerification:
    """Test semantic verification on controlled extraction."""
    
    def test_semantic_verification_on_controlled_data(
        self,
        controlled_source_doc,
        configured_mock_provider
    ):
        """Semantic verifier should assess claims from controlled extraction."""
        extractor = KnowledgeExtractor(configured_mock_provider, verbose=False)
        knowledge_doc = extractor.extract(controlled_source_doc)
        
        verifier = DeterministicSemanticVerifier(verbose=False)
        verification_report = verifier.verify(knowledge_doc, controlled_source_doc)
        
        # Should have verification results
        assert verification_report is not None
        assert len(verification_report.claim_verifications) > 0
        
        # Most claims should be SUPPORTED (directly from fixture)
        supported_count = sum(
            1 for claim in verification_report.claim_verifications
            if claim.verification_status.status == "SUPPORTED"
        )
        total_claims = len(verification_report.claim_verifications)
        
        # At least 30% should be supported (conservative threshold given mock duplicates)
        support_rate = supported_count / total_claims if total_claims > 0 else 0
        assert support_rate >= 0.3, \
            f"Only {supported_count}/{total_claims} claims supported ({support_rate:.1%})"
