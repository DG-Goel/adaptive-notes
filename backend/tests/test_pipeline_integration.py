"""
Integration tests for structural evaluator in the pipeline.

Tests that invalid artifacts are detected during actual pipeline execution.
"""

import pytest
from pathlib import Path
import json

from app.models.knowledge import KnowledgeDocument, Concept
from app.representation.models import RepresentationDocument, SelectedRepresentation
from app.representation.formats import RepresentationFormat
from app.assembly.models import AssembledNotesDocument, AssembledSection, AssembledItem, AssemblyMetadata
from app.evaluation.structural_evaluator import StructuralEvaluator


class TestRepresentationIntegration:
    """Test structural evaluation catches representation errors in pipeline"""
    
    def test_invalid_representation_caught(self):
        """Pipeline should catch representations with missing required fields"""
        
        # Create representation with missing source_unit_ids
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="CON_001",
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=[],  # INVALID: empty
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.9,
                    confidence_label="high",
                    selection_reasoning="Test",
                    format_content={"text": "Test"}
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        # Should fail validation
        assert not report.passed
        assert report.error_count > 0
        
        # Should have specific error about missing source_unit_ids
        errors = [i for i in report.issues if "source" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_broken_reference_caught(self):
        """Pipeline should catch representations referencing non-existent knowledge"""
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[Concept(
                knowledge_id="CON_001",
                knowledge_type="concept",
                document_id="TEST",
                content="Real concept",
                concept_name="Real",
                source_unit_ids=["S001"]
            )],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="CON_999",  # INVALID: doesn't exist
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.9,
                    confidence_label="high",
                    selection_reasoning="Test",
                    format_content={"text": "Test"}
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(
            representation_doc=rep_doc,
            knowledge_doc=knowledge_doc
        )
        
        # Should fail validation
        assert not report.passed
        assert report.error_count > 0
        
        # Should have error about broken reference
        errors = [i for i in report.issues if "reference" in i.reason.lower()]
        assert len(errors) > 0


class TestAssemblyIntegration:
    """Test structural evaluation catches assembly errors in pipeline"""
    
    def test_broken_assembly_reference_caught(self):
        """Pipeline should catch assembly items referencing non-existent representations"""
        
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="CON_001",
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.9,
                    confidence_label="high",
                    selection_reasoning="Test",
                    format_content={"text": "Test"}
                )
            ]
        )
        
        assembly_doc = AssembledNotesDocument(
            document_id="TEST",
            source_filename="test.txt",
            assembly_timestamp="2024-01-01T00:00:00",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            sections=[
                AssembledSection(
                    section_id="section_0",
                    section_name="Main",
                    section_type="default_section",
                    items=[
                        AssembledItem(
                            knowledge_id="CON_999",  # INVALID: doesn't exist in rep_doc
                            document_id="TEST",
                            knowledge_type="concept",
                            primary_format=RepresentationFormat.STANDARD_TEXT,
                            format_content={"text": "Test"},
                            selection_confidence=0.9,
                            confidence_label="high",
                            selection_reasoning="Test",
                            source_unit_ids=["S001"],
                            position_in_section=0,
                            ordering_rationale="Test"
                        )
                    ]
                )
            ],
            metadata=AssemblyMetadata(
                assembly_timestamp="2024-01-01T00:00:00",
                ordering_strategy="section-based",
                total_sections=1,
                total_items=1,
                items_with_section=1,
                items_without_section=0
            )
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(
            assembly_doc=assembly_doc,
            representation_doc=rep_doc
        )
        
        # Should fail validation
        assert not report.passed
        assert report.error_count > 0
        
        # Should have error about broken reference
        errors = [i for i in report.issues if "reference" in i.reason.lower()]
        assert len(errors) > 0


class TestMarkdownIntegration:
    """Test structural evaluation catches markdown errors in pipeline"""
    
    def test_empty_markdown_caught(self):
        """Pipeline should catch empty markdown output"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output="")
        
        # Should fail validation
        assert not report.passed
        assert report.error_count > 0
        
        # Should have error about empty content
        errors = [i for i in report.issues if "empty" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_malformed_markdown_caught(self):
        """Pipeline should catch malformed markdown (unmatched code fences)"""
        
        markdown = """# Test

```python
def test():
    pass
# Missing closing fence
"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output=markdown)
        
        # Should fail validation
        assert not report.passed
        assert report.error_count > 0
        
        # Should have error about unmatched fence
        errors = [i for i in report.issues if "fence" in i.reason.lower() or "code" in i.reason.lower()]
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
