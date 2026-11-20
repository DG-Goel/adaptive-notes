"""
Unit tests for the evaluation module.

Tests coverage, provenance integrity, representation validity, and content integrity checks.
"""

import pytest
from datetime import datetime
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.models import CoverageMetrics
from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import KnowledgeDocument, Concept, Fact, Explanation
from app.analysis.characteristics import (
    AnalyzedKnowledgeDocument, 
    AnalyzedKnowledge,
    ContentCharacteristic
)
from app.representation.models import RepresentationDocument, SelectedRepresentation
from app.assembly.models import (
    AssembledNotesDocument, 
    AssembledSection, 
    AssembledItem,
    AssemblyMetadata,
    AssemblyStatistics
)
from app.rendering.models import RenderManifest, RenderedItem
from app.representation.formats import RepresentationFormat


def create_test_source_doc(num_units=10):
    """Create a test source document."""
    units = [
        SourceUnit(
            source_id=f"S{i:04d}",
            document_id="TEST_DOC",
            page=1,
            type="text",
            content_role="content",
            text=f"Test content {i}",
            position=i
        )
        for i in range(num_units)
    ]
    
    return SourceDocument(
        document_id="TEST_DOC",
        filename="test.pdf",
        page_count=1,
        source_units=units
    )


def create_test_knowledge_doc(num_items=5):
    """Create a test knowledge document."""
    concepts = [
        Concept(
            knowledge_id=f"CON_{i:04d}",
            knowledge_type="concept",
            source_unit_ids=[f"S{i:04d}"],
            document_id="TEST_DOC",
            content=f"Concept {i}",
            concept_name=f"concept_{i}",
            aliases=[]
        )
        for i in range(num_items)
    ]
    
    return KnowledgeDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        extraction_timestamp=datetime.now().isoformat(),
        concepts=concepts,
        definitions=[],
        explanations=[],
        examples=[],
        facts=[],
        formulas=[],
        procedures=[],
        relationships=[]
    )


def create_test_analyzed_doc(knowledge_ids):
    """Create a test analyzed document."""
    from app.analysis.characteristics import ContentCharacteristic
    
    items = []
    for kid in knowledge_ids:
        # Create a concept (KnowledgeItem)
        concept = Concept(
            knowledge_id=kid,
            knowledge_type="concept",
            source_unit_ids=[f"S0000"],
            document_id="TEST_DOC",
            content="Test",
            concept_name="test_concept",
            aliases=[]
        )
        
        # Wrap in AnalyzedKnowledge
        analyzed = AnalyzedKnowledge(
            knowledge_item=concept,
            characteristics=[ContentCharacteristic.DEFINITION],
            analysis_confidence="high",
            analysis_reasoning="Test"
        )
        items.append(analyzed)
    
    from app.analysis.characteristics import AnalysisStatistics
    return AnalyzedKnowledgeDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        analysis_timestamp=datetime.now().isoformat(),
        extraction_timestamp=datetime.now().isoformat(),
        source_units_processed=10,
        analyzed_items=items,
        statistics=AnalysisStatistics()
    )


def create_test_represented_doc(knowledge_ids):
    """Create a test represented document."""
    items = [
        SelectedRepresentation(
            knowledge_id=kid,
            knowledge_type="concept",
            document_id="TEST_DOC",
            source_unit_ids=[f"S0000"],
            primary_format=RepresentationFormat.STANDARD_TEXT,
            format_content={"content": "Test content"},
            selection_confidence=0.9,
            confidence_label="high",
            selection_reasoning="Test"
        )
        for kid in knowledge_ids
    ]
    
    from app.representation.models import RepresentationStatistics
    return RepresentationDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        representation_timestamp=datetime.now().isoformat(),
        analysis_timestamp=datetime.now().isoformat(),
        extraction_timestamp=datetime.now().isoformat(),
        source_units_processed=10,
        representations=items,
        statistics=RepresentationStatistics()
    )


def create_test_assembled_doc(knowledge_ids):
    """Create a test assembled document."""
    items = [
        AssembledItem(
            knowledge_id=kid,
            document_id="TEST_DOC",
            knowledge_type="concept",
            primary_format=RepresentationFormat.STANDARD_TEXT,
            format_content={"content": "Test content"},
            selection_confidence=0.9,
            confidence_label="high",
            selection_reasoning="Test",
            source_unit_ids=[f"S0000"],
            position_in_section=i,
            ordering_rationale="Test"
        )
        for i, kid in enumerate(knowledge_ids)
    ]
    
    section = AssembledSection(
        section_id="section_0",
        section_name="Main",
        section_type="default_section",
        items=items
    )
    
    return AssembledNotesDocument(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        assembly_timestamp=datetime.now().isoformat(),
        representation_timestamp=datetime.now().isoformat(),
        analysis_timestamp=datetime.now().isoformat(),
        extraction_timestamp=datetime.now().isoformat(),
        source_units_processed=10,
        sections=[section],
        metadata=AssemblyMetadata(
            assembly_timestamp=datetime.now().isoformat(),
            ordering_strategy="source-order",
            total_sections=1,
            total_items=len(knowledge_ids),
            items_with_section=len(knowledge_ids),
            items_without_section=0
        ),
        statistics=AssemblyStatistics()
    )


def create_test_render_manifest(knowledge_ids):
    """Create a test render manifest."""
    items = [
        RenderedItem(
            knowledge_id=kid,
            source_unit_ids=[f"S0000"],
            format_used=RepresentationFormat.STANDARD_TEXT,
            start_line=i*5,
            end_line=i*5+3,
            status="complete",
            used_fallback=False
        )
        for i, kid in enumerate(knowledge_ids)
    ]
    
    return RenderManifest(
        document_id="TEST_DOC",
        source_filename="test.pdf",
        render_timestamp=datetime.now().isoformat(),
        assembly_timestamp=datetime.now().isoformat(),
        representation_timestamp=datetime.now().isoformat(),
        analysis_timestamp=datetime.now().isoformat(),
        extraction_timestamp=datetime.now().isoformat(),
        markdown_length=1000,
        total_lines=50,
        items=items,
        warnings=[],
        total_items=len(knowledge_ids)
    )


class TestFaithfulnessEvaluator:
    """Test suite for FaithfulnessEvaluator."""
    
    def test_complete_coverage(self):
        """Test evaluation with complete coverage (all items through pipeline)."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Check coverage
        assert result.coverage.total_knowledge_items_extracted == 5
        assert result.coverage.total_items_assembled == 5
        assert result.coverage.total_items_rendered == 5
        assert result.coverage.assembly_coverage_ratio == 1.0
        assert result.coverage.rendering_coverage_ratio == 1.0
        assert result.coverage.end_to_end_coverage_ratio == 1.0
        
        # Should have no errors
        assert len(result.provenance_errors) == 0
        assert len(result.representation_errors) == 0
        assert result.status.status == "pass"
    
    def test_missing_rendered_item(self):
        """Test detection of missing rendered item."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        
        # Render only 4 items (missing one)
        render_manifest = create_test_render_manifest(knowledge_ids[:4])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Check coverage
        assert result.coverage.total_items_assembled == 5
        assert result.coverage.total_items_rendered == 4
        assert result.coverage.rendering_coverage_ratio == 0.8
        assert len(result.coverage.knowledge_ids_not_rendered) == 1
        
        # Should have content warning
        assert len(result.content_warnings) >= 1
        assert any(w.warning_type == "missing_rendered_item" for w in result.content_warnings)
        assert result.status.status in ["warning", "pass"]
    
    def test_unknown_knowledge_id(self):
        """Test detection of unknown knowledge ID in assembly."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        
        # Add an unknown ID to assembly
        assembled_ids = knowledge_ids + ["UNKNOWN_ID"]
        assembled_doc = create_test_assembled_doc(assembled_ids)
        render_manifest = create_test_render_manifest(assembled_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should have provenance errors
        assert len(result.provenance_errors) >= 1
        assert any(e.error_type == "unknown_knowledge_id" for e in result.provenance_errors)
        assert any("UNKNOWN_ID" in e.knowledge_id for e in result.provenance_errors)
        assert result.status.status == "fail"
        assert not result.status.provenance_valid
    
    def test_unknown_source_unit_id(self):
        """Test detection of unknown source unit ID."""
        source_doc = create_test_source_doc(10)  # Has S0000-S0009
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        
        # Create assembly with invalid source unit ID
        items = [
            AssembledItem(
                knowledge_id=knowledge_ids[0],
                document_id="TEST_DOC",
                knowledge_type="concept",
                primary_format=RepresentationFormat.STANDARD_TEXT,
                format_content={"content": "Test"},
                selection_confidence=0.9,
                confidence_label="high",
                selection_reasoning="Test",
                source_unit_ids=["INVALID_SOURCE"],  # Invalid
                position_in_section=0,
                ordering_rationale="Test"
            )
        ]
        
        section = AssembledSection(
            section_id="section_0",
            section_name="Main",
            section_type="default_section",
            items=items
        )
        
        assembled_doc = AssembledNotesDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            assembly_timestamp=datetime.now().isoformat(),
            representation_timestamp=datetime.now().isoformat(),
            analysis_timestamp=datetime.now().isoformat(),
            extraction_timestamp=datetime.now().isoformat(),
            source_units_processed=10,
            sections=[section],
            metadata=AssemblyMetadata(
                assembly_timestamp=datetime.now().isoformat(),
                ordering_strategy="source-order",
                total_sections=1,
                total_items=1,
                items_with_section=1,
                items_without_section=0
            ),
            statistics=AssemblyStatistics()
        )
        
        render_manifest = create_test_render_manifest([knowledge_ids[0]])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should have provenance errors
        assert len(result.provenance_errors) >= 1
        assert any(e.error_type == "unknown_source_unit_id" for e in result.provenance_errors)
        assert result.status.status == "fail"
    
    def test_duplicate_knowledge_id(self):
        """Test detection of duplicate knowledge IDs."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        
        # Create assembly with duplicate ID
        duplicate_ids = knowledge_ids + [knowledge_ids[0]]  # Duplicate first ID
        assembled_doc = create_test_assembled_doc(duplicate_ids)
        render_manifest = create_test_render_manifest(duplicate_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should have provenance error for duplicate
        assert len(result.provenance_errors) >= 1
        assert any(e.error_type == "duplicate_knowledge_id" for e in result.provenance_errors)
        assert result.status.status == "fail"
    
    def test_malformed_representation_payload(self):
        """Test detection of malformed representation payload."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        
        # Create assembly with missing required field
        items = [
            AssembledItem(
                knowledge_id=knowledge_ids[0],
                document_id="TEST_DOC",
                knowledge_type="concept",
                primary_format=RepresentationFormat.DEFINITION_BOX,
                format_content={"term": "Test"},  # Missing 'definition' field
                selection_confidence=0.9,
                confidence_label="high",
                selection_reasoning="Test",
                source_unit_ids=["S0000"],
                position_in_section=0,
                ordering_rationale="Test"
            )
        ]
        
        section = AssembledSection(
            section_id="section_0",
            section_name="Main",
            section_type="default_section",
            items=items
        )
        
        assembled_doc = AssembledNotesDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            assembly_timestamp=datetime.now().isoformat(),
            representation_timestamp=datetime.now().isoformat(),
            analysis_timestamp=datetime.now().isoformat(),
            extraction_timestamp=datetime.now().isoformat(),
            source_units_processed=10,
            sections=[section],
            metadata=AssemblyMetadata(
                assembly_timestamp=datetime.now().isoformat(),
                ordering_strategy="source-order",
                total_sections=1,
                total_items=1,
                items_with_section=1,
                items_without_section=0
            ),
            statistics=AssemblyStatistics()
        )
        
        render_manifest = create_test_render_manifest([knowledge_ids[0]])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should have representation error
        assert len(result.representation_errors) >= 1
        assert any(e.error_type == "missing_required_field" for e in result.representation_errors)
        assert "definition" in result.representation_errors[0].missing_fields
        assert result.status.status == "fail"
    
    def test_empty_document(self):
        """Test evaluation with empty document."""
        source_doc = create_test_source_doc(10)
        
        # Empty knowledge document
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[]
        )
        
        analyzed_doc = create_test_analyzed_doc([])
        represented_doc = create_test_represented_doc([])
        assembled_doc = create_test_assembled_doc([])
        render_manifest = create_test_render_manifest([])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should handle empty gracefully BUT mark as incomplete
        # since zero extraction from content-bearing source is a failure
        assert result.coverage.total_knowledge_items_extracted == 0
        assert result.coverage.total_items_assembled == 0
        assert result.coverage.total_items_rendered == 0
        assert result.status.status == "incomplete"
        assert result.status.pipeline_complete is False
        assert "zero items extracted" in result.status.summary_message
    
    def test_deterministic_evaluation(self):
        """Test that evaluation is deterministic."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        
        # Run twice
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
        assert len(result1.provenance_errors) == len(result2.provenance_errors)
        assert len(result1.representation_errors) == len(result2.representation_errors)
        assert len(result1.content_warnings) == len(result2.content_warnings)
    
    def test_accurate_coverage_denominators(self):
        """Test that coverage metrics use correct denominators."""
        source_doc = create_test_source_doc(10)  # 10 source units
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]  # 5 extracted
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids[:4])  # 4 analyzed
        represented_doc = create_test_represented_doc(knowledge_ids[:4])  # 4 represented
        assembled_doc = create_test_assembled_doc(knowledge_ids[:3])  # 3 assembled
        render_manifest = create_test_render_manifest(knowledge_ids[:3])  # 3 rendered
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Check explicit denominators
        assert result.coverage.total_source_units == 10
        assert result.coverage.total_knowledge_items_extracted == 5
        assert result.coverage.total_items_analyzed == 4
        assert result.coverage.total_items_assembled == 3
        assert result.coverage.total_items_rendered == 3
        
        # Check ratios
        assert result.coverage.analysis_coverage_ratio == 4/5  # analyzed / extracted
        assert result.coverage.assembly_coverage_ratio == 3/4  # assembled / analyzed
        assert result.coverage.rendering_coverage_ratio == 3/3  # rendered / assembled
        assert result.coverage.end_to_end_coverage_ratio == 3/5  # rendered / extracted
    
    def test_valid_json_serialization(self):
        """Test that evaluation result can be serialized to JSON."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should serialize without error
        json_str = result.model_dump_json(indent=2)
        assert len(json_str) > 0
        assert "evaluation_timestamp" in json_str
        assert "coverage" in json_str
        assert "status" in json_str
    
    def test_semantic_faithfulness_not_verified(self):
        """Test that evaluation explicitly states semantic faithfulness is NOT verified."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should explicitly state semantic faithfulness was NOT verified
        assert result.semantic_faithfulness_verified is False
        assert "NOT verified" in result.semantic_faithfulness_note
        
        # Should be in recommendations
        assert any("semantic faithfulness" in rec.lower() for rec in result.recommendations)
    
    def test_empty_collection_detection(self):
        """Test detection of empty collections in specific formats."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(2)]
        knowledge_doc = create_test_knowledge_doc(2)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        
        # Create flowchart with insufficient steps
        items = [
            AssembledItem(
                knowledge_id=knowledge_ids[0],
                document_id="TEST_DOC",
                knowledge_type="procedure",
                primary_format=RepresentationFormat.FLOWCHART,
                format_content={"steps": ["One step"]},  # Only 1 step, needs 2+
                selection_confidence=0.9,
                confidence_label="high",
                selection_reasoning="Test",
                source_unit_ids=["S0000"],
                position_in_section=0,
                ordering_rationale="Test"
            ),
            AssembledItem(
                knowledge_id=knowledge_ids[1],
                document_id="TEST_DOC",
                knowledge_type="concept",
                primary_format=RepresentationFormat.TIMELINE,
                format_content={"events": []},  # Empty events
                selection_confidence=0.9,
                confidence_label="high",
                selection_reasoning="Test",
                source_unit_ids=["S0000"],
                position_in_section=1,
                ordering_rationale="Test"
            )
        ]
        
        section = AssembledSection(
            section_id="section_0",
            section_name="Main",
            section_type="default_section",
            items=items
        )
        
        assembled_doc = AssembledNotesDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            assembly_timestamp=datetime.now().isoformat(),
            representation_timestamp=datetime.now().isoformat(),
            analysis_timestamp=datetime.now().isoformat(),
            extraction_timestamp=datetime.now().isoformat(),
            source_units_processed=10,
            sections=[section],
            metadata=AssemblyMetadata(
                assembly_timestamp=datetime.now().isoformat(),
                ordering_strategy="source-order",
                total_sections=1,
                total_items=2,
                items_with_section=2,
                items_without_section=0
            ),
            statistics=AssemblyStatistics()
        )
        
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect empty collection errors
        assert len(result.representation_errors) >= 2
        assert any(e.error_type == "empty_collection" for e in result.representation_errors)


    def test_zero_analyzed_with_nonzero_extracted(self):
        """Test detection of zero analyzed items when extraction produced items."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        
        # No analyzed items (empty)
        from app.analysis.characteristics import AnalysisStatistics
        analyzed_doc = AnalyzedKnowledgeDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            analysis_timestamp=datetime.now().isoformat(),
            extraction_timestamp=datetime.now().isoformat(),
            source_units_processed=10,
            analyzed_items=[],
            statistics=AnalysisStatistics()
        )
        
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect missing analyzed items
        assert len(result.provenance_errors) >= 5
        assert any(e.error_type == "missing_analyzed_item" for e in result.provenance_errors)
        assert result.status.status == "incomplete"
        assert not result.status.pipeline_complete
        assert result.coverage.total_items_analyzed == 0
        assert result.coverage.total_knowledge_items_extracted == 5
    
    def test_partial_analysis_coverage(self):
        """Test detection of partial analysis coverage."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        
        # Only 3 out of 5 analyzed
        analyzed_doc = create_test_analyzed_doc(knowledge_ids[:3])
        represented_doc = create_test_represented_doc(knowledge_ids[:3])
        assembled_doc = create_test_assembled_doc(knowledge_ids[:3])
        render_manifest = create_test_render_manifest(knowledge_ids[:3])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect 2 missing analyzed items
        missing_analyzed_errors = [e for e in result.provenance_errors if e.error_type == "missing_analyzed_item"]
        assert len(missing_analyzed_errors) == 2
        assert result.coverage.analysis_coverage_ratio == 0.6  # 3/5
        assert len(result.coverage.knowledge_ids_not_analyzed) == 2
        assert result.status.status == "incomplete"
    
    def test_complete_analysis_coverage(self):
        """Test that complete analysis coverage passes."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(5)]
        knowledge_doc = create_test_knowledge_doc(5)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should have no missing analyzed items
        assert not any(e.error_type == "missing_analyzed_item" for e in result.provenance_errors)
        assert result.coverage.analysis_coverage_ratio == 1.0
        assert len(result.coverage.knowledge_ids_not_analyzed) == 0
        assert result.status.pipeline_complete
        assert result.status.status == "pass"
    
    def test_unexpected_analyzed_ids(self):
        """Test detection of unexpected analyzed IDs."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        
        # Analyzed doc contains extra ID not in extraction
        analyzed_ids = knowledge_ids + ["CON_9999"]
        analyzed_doc = create_test_analyzed_doc(analyzed_ids)
        
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect unexpected ID
        unexpected_errors = [e for e in result.provenance_errors if e.error_type == "unexpected_analyzed_id"]
        assert len(unexpected_errors) >= 1
        assert any("CON_9999" in e.knowledge_id for e in unexpected_errors)
        assert result.status.status == "incomplete"
    
    def test_document_id_mismatch(self):
        """Test detection of mismatched document IDs across stages."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        
        # Create docs with mismatched IDs
        knowledge_doc = KnowledgeDocument(
            document_id="WRONG_DOC",  # Different ID
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            concepts=[
                Concept(
                    knowledge_id=kid,
                    knowledge_type="concept",
                    source_unit_ids=["S0000"],
                    document_id="WRONG_DOC",
                    content="Test",
                    concept_name="test",
                    aliases=[]
                )
                for kid in knowledge_ids
            ],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[]
        )
        
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect document ID mismatch
        mismatch_errors = [e for e in result.provenance_errors if e.error_type == "document_id_mismatch"]
        assert len(mismatch_errors) >= 1
        assert result.status.status == "incomplete"
        assert not result.status.pipeline_complete
    
    def test_legitimately_empty_document(self):
        """Test that zero extraction from content-bearing source is marked incomplete."""
        source_doc = create_test_source_doc(10)
        
        # All stages empty but source has text (extraction failure)
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_DOC",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[]
        )
        
        analyzed_doc = create_test_analyzed_doc([])
        represented_doc = create_test_represented_doc([])
        assembled_doc = create_test_assembled_doc([])
        render_manifest = create_test_render_manifest([])
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Zero extraction from content is incomplete (extraction failure)
        assert result.coverage.total_knowledge_items_extracted == 0
        assert result.coverage.total_items_analyzed == 0
        assert result.coverage.total_items_assembled == 0
        assert result.coverage.total_items_rendered == 0
        assert not result.status.pipeline_complete  # Extraction failed
        assert result.status.status == "incomplete"
        assert "zero items extracted" in result.status.summary_message
    
    def test_stale_artifacts_detected(self):
        """Test detection of stale/invalid artifacts through inconsistency."""
        source_doc = create_test_source_doc(10)
        knowledge_ids_v1 = [f"CON_{i:04d}" for i in range(3)]
        knowledge_ids_v2 = [f"CON_{i:04d}" for i in range(5, 8)]  # Different IDs
        
        # Knowledge doc with one set of IDs
        knowledge_doc = create_test_knowledge_doc(3)
        
        # Analyzed doc with completely different IDs (stale)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids_v2)
        
        represented_doc = create_test_represented_doc(knowledge_ids_v1)
        assembled_doc = create_test_assembled_doc(knowledge_ids_v1)
        render_manifest = create_test_render_manifest(knowledge_ids_v1)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Should detect inconsistencies
        assert len(result.provenance_errors) > 0
        # Should have missing analyzed (v1 IDs not analyzed)
        assert any(e.error_type == "missing_analyzed_item" for e in result.provenance_errors)
        # Should have unexpected IDs (v2 IDs appear in analysis)
        assert any(e.error_type == "unexpected_analyzed_id" for e in result.provenance_errors)
        assert result.status.status == "incomplete"
    
    def test_extraction_coverage_is_labeled_as_proxy(self):
        """Test that extraction coverage is properly labeled as a structural proxy."""
        source_doc = create_test_source_doc(10)
        knowledge_ids = [f"CON_{i:04d}" for i in range(3)]
        knowledge_doc = create_test_knowledge_doc(3)
        analyzed_doc = create_test_analyzed_doc(knowledge_ids)
        represented_doc = create_test_represented_doc(knowledge_ids)
        assembled_doc = create_test_assembled_doc(knowledge_ids)
        render_manifest = create_test_render_manifest(knowledge_ids)
        
        evaluator = FaithfulnessEvaluator()
        result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            render_manifest
        )
        
        # Check that coverage model has the disclaimer
        assert "structural proxy" in CoverageMetrics.__doc__.lower()
        assert "not a definitive measure" in CoverageMetrics.__doc__.lower()
        
        # The ratio should be present with clear naming
        assert hasattr(result.coverage, 'extraction_coverage_ratio')
        assert result.coverage.extraction_coverage_ratio > 0


    def test_document_id_consistency_enforced(self):
        """Verify evaluator detects document ID mismatches across pipeline stages"""
        
        # Source with DOC001  (mismatch!)
        source_doc = SourceDocument(
            document_id="DOC001",  # Different from others!
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(source_id="S0000", document_id="DOC001", type="paragraph", 
                          content_role="content", text="Source text", position=1, page=1)
            ]
        )
        
        # All other stages use TEST_DOC (created by helpers)
        knowledge_doc = create_test_knowledge_doc(num_items=1)
        analyzed_doc = create_test_analyzed_doc(["CON_0000"])
        represented_doc = create_test_represented_doc(["CON_0000"])
        assembled_doc = create_test_assembled_doc(["CON_0000"])
        render_manifest = create_test_render_manifest(["CON_0000"])
        
        # Evaluate
        evaluator = FaithfulnessEvaluator(verbose=False)
        result = evaluator.evaluate(
            source_doc, knowledge_doc, analyzed_doc, 
            represented_doc, assembled_doc, render_manifest
        )
        
        # Should detect document_id_mismatch error
        doc_id_errors = [e for e in result.provenance_errors 
                        if e.error_type == "document_id_mismatch"]
        assert len(doc_id_errors) > 0, "Should detect document ID mismatch"
        
        # Should mark as incomplete
        assert result.status.status == "incomplete", \
            "Document ID mismatch should result in 'incomplete' status"
        assert not result.status.pipeline_complete, \
            "pipeline_complete should be False when document IDs mismatch"
    
    def test_document_id_consistency_passes_when_consistent(self):
        """Verify evaluator passes when all document IDs match"""
        
        # All stages use TEST_DOC (created by helpers)
        source_doc = create_test_source_doc(num_units=1)
        knowledge_doc = create_test_knowledge_doc(num_items=1)
        analyzed_doc = create_test_analyzed_doc(["CON_0000"])
        represented_doc = create_test_represented_doc(["CON_0000"])
        assembled_doc = create_test_assembled_doc(["CON_0000"])
        render_manifest = create_test_render_manifest(["CON_0000"])
        
        # Evaluate
        evaluator = FaithfulnessEvaluator(verbose=False)
        result = evaluator.evaluate(
            source_doc, knowledge_doc, analyzed_doc, 
            represented_doc, assembled_doc, render_manifest
        )
        
        # Should NOT have document_id_mismatch errors
        doc_id_errors = [e for e in result.provenance_errors 
                        if e.error_type == "document_id_mismatch"]
        assert len(doc_id_errors) == 0, "Should not have document ID mismatch errors"
        
        # Should have pipeline_complete = True
        assert result.status.pipeline_complete, \
            "pipeline_complete should be True when document IDs match"
        
        # Should pass (no errors)
        assert result.status.status == "pass", \
            "Should pass when document IDs are consistent"
