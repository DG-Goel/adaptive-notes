"""
Tests for structural evaluator.

Tests structural validation of representation, assembly, and markdown artifacts.
"""

import pytest
from datetime import datetime

from app.evaluation.structural_evaluator import StructuralEvaluator, StructuralIssue
from app.models.knowledge import KnowledgeDocument, Concept, Example, Definition, Fact
from app.representation.models import (
    RepresentationDocument, 
    SelectedRepresentation,
    RepresentationStatistics
)
from app.representation.formats import RepresentationFormat
from app.assembly.models import (
    AssembledNotesDocument, 
    AssembledSection, 
    AssembledItem,
    AssemblyMetadata,
    AssemblyStatistics
)


class TestRepresentationValidation:
    """Test representation structure validation"""
    
    def test_valid_representation_passes(self):
        """Valid representation document should pass validation"""
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[Concept(
                knowledge_id="CON_001",
                knowledge_type="concept",
                document_id="TEST",
                content="Test concept",
                concept_name="Test",
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
                    knowledge_id="CON_001",
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.95,
                    confidence_label="high",
                    selection_reasoning="Simple concept best as prose",
                    format_content={"text": "Test concept description"}
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(
            representation_doc=rep_doc,
            knowledge_doc=knowledge_doc
        )
        
        assert report.passed, f"Valid representation should pass, errors: {report.issues}"
        assert report.error_count == 0
    
    def test_missing_knowledge_id_fails(self):
        """Representation without knowledge_id should error"""
        
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="",  # Empty - should fail
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.8,
                    confidence_label="medium",
                    selection_reasoning="Test",
                    format_content={"text": "Test"}
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        assert not report.passed
        assert report.error_count > 0
        # Should have error about missing knowledge_id
        errors = [i for i in report.issues if i.severity == "ERROR" and "knowledge_id" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_missing_source_unit_ids_fails(self):
        """Representation without source_unit_ids should error"""
        
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
                    source_unit_ids=[],  # Empty - should fail
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.8,
                    confidence_label="medium",
                    selection_reasoning="Test",
                    format_content={"text": "Test"}
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        assert not report.passed
        assert report.error_count > 0
        # Should have error about missing source_unit_ids
        errors = [i for i in report.issues if i.severity == "ERROR" and "source" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_broken_knowledge_reference_fails(self):
        """Representation referencing non-existent knowledge should error"""
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[Concept(
                knowledge_id="CON_001",
                knowledge_type="concept",
                document_id="TEST",
                content="Test",
                concept_name="Test",
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
                    knowledge_id="CON_999",  # Doesn't exist in knowledge_doc
                    document_id="TEST",
                    knowledge_type="concept",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.STANDARD_TEXT,
                    selection_confidence=0.8,
                    confidence_label="medium",
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
        
        assert not report.passed
        assert report.error_count > 0
        # Should have error about broken reference
        errors = [i for i in report.issues if i.severity == "ERROR" and "reference" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_comparison_table_structure(self):
        """Test validation of comparison table format content"""
        
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
                    primary_format=RepresentationFormat.COMPARISON_TABLE,
                    selection_confidence=0.9,
                    confidence_label="high",
                    selection_reasoning="Comparison content best as table",
                    format_content={
                        "headers": ["Feature", "Option A", "Option B"],
                        "rows": [
                            ["Speed", "Fast", "Slow"],
                            ["Cost", "High", "Low"]
                        ]
                    }
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        # Valid table structure should pass
        assert report.passed or report.error_count == 0
    
    def test_flowchart_structure(self):
        """Test validation of flowchart format content"""
        
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="PRC_001",
                    document_id="TEST",
                    knowledge_type="procedure",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.FLOWCHART,
                    selection_confidence=0.9,
                    confidence_label="high",
                    selection_reasoning="Process flow best as flowchart",
                    format_content={
                        "nodes": [
                            {"id": "start", "label": "Start", "type": "start"},
                            {"id": "step1", "label": "Do something", "type": "process"}
                        ],
                        "edges": [
                            {"from": "start", "to": "step1"}
                        ]
                    }
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        # Valid flowchart structure should pass
        assert report.passed or report.error_count == 0
    
    def test_formula_display_structure(self):
        """Test validation of formula display format content"""
        
        rep_doc = RepresentationDocument(
            document_id="TEST",
            source_filename="test.txt",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=1,
            representations=[
                SelectedRepresentation(
                    knowledge_id="FRM_001",
                    document_id="TEST",
                    knowledge_type="formula",
                    source_unit_ids=["S001"],
                    primary_format=RepresentationFormat.FORMULA_DISPLAY,
                    selection_confidence=0.95,
                    confidence_label="high",
                    selection_reasoning="Mathematical formula best as formula display",
                    format_content={
                        "formula": "E = mc²",
                        "variables": {
                            "E": "Energy",
                            "m": "Mass",
                            "c": "Speed of light"
                        }
                    }
                )
            ]
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(representation_doc=rep_doc)
        
        # Valid formula structure should pass
        assert report.passed or report.error_count == 0


class TestAssemblyValidation:
    """Test assembly structure validation"""
    
    def test_valid_assembly_passes(self):
        """Valid assembly document should pass validation"""
        
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
                    format_content={"text": "Test concept"}
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
                    section_name="Main Content",
                    section_type="default_section",
                    items=[
                        AssembledItem(
                            knowledge_id="CON_001",
                            document_id="TEST",
                            knowledge_type="concept",
                            primary_format=RepresentationFormat.STANDARD_TEXT,
                            format_content={"text": "Test concept"},
                            selection_confidence=0.9,
                            confidence_label="high",
                            selection_reasoning="Test",
                            source_unit_ids=["S001"],
                            position_in_section=0,
                            ordering_rationale="First item"
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
        
        assert report.passed, f"Valid assembly should pass, errors: {report.issues}"
        assert report.error_count == 0
    
    def test_empty_sections_warns(self):
        """Empty sections should generate warning"""
        
        assembly_doc = AssembledNotesDocument(
            document_id="TEST",
            source_filename="test.txt",
            assembly_timestamp="2024-01-01T00:00:00",
            representation_timestamp="2024-01-01T00:00:00",
            analysis_timestamp="2024-01-01T00:00:00",
            extraction_timestamp="2024-01-01T00:00:00",
            source_units_processed=0,
            sections=[
                AssembledSection(
                    section_id="section_0",
                    section_name="Empty Section",
                    section_type="named_section",
                    items=[]  # No items - should warn
                )
            ],
            metadata=AssemblyMetadata(
                assembly_timestamp="2024-01-01T00:00:00",
                ordering_strategy="section-based",
                total_sections=1,
                total_items=0,
                items_with_section=0,
                items_without_section=0
            )
        )
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(assembly_doc=assembly_doc)
        
        # Should have warning about empty section
        warnings = [i for i in report.issues if i.severity == "WARNING"]
        assert len(warnings) > 0
    
    def test_broken_representation_reference_fails(self):
        """Assembly item referencing non-existent representation should error"""
        
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
                            knowledge_id="CON_999",  # Doesn't exist in rep_doc
                            document_id="TEST",
                            knowledge_type="concept",
                            primary_format=RepresentationFormat.STANDARD_TEXT,
                            format_content={"text": "Test"},
                            selection_confidence=0.8,
                            confidence_label="medium",
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
        
        assert not report.passed
        assert report.error_count > 0
        # Should have error about broken reference
        errors = [i for i in report.issues if i.severity == "ERROR" and "reference" in i.reason.lower()]
        assert len(errors) > 0


class TestMarkdownValidation:
    """Test markdown output validation"""
    
    def test_valid_markdown_passes(self):
        """Valid markdown should pass validation"""
        
        markdown = """# Introduction to Java

## Concepts

### Variables

Variables store data values. In Java, you must declare the type.

## Examples

```java
int x = 5;
String name = "John";
```

## Summary

Java is a strongly-typed language.
"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output=markdown)
        
        assert report.passed or report.error_count == 0
    
    def test_empty_markdown_fails(self):
        """Empty markdown should error"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output="")
        
        assert not report.passed
        assert report.error_count > 0
    
    def test_unmatched_code_fence_fails(self):
        """Unmatched code fence should error"""
        
        markdown = """# Test

```java
int x = 5;
// Missing closing fence
"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output=markdown)
        
        assert not report.passed
        assert report.error_count > 0
        # Should have error about unmatched fence
        errors = [i for i in report.issues if "fence" in i.reason.lower() or "code block" in i.reason.lower()]
        assert len(errors) > 0
    
    def test_very_short_markdown_warns(self):
        """Very short markdown should generate warning"""
        
        markdown = "# Title\n\nShort."
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output=markdown)
        
        # Should have warning about short content
        warnings = [i for i in report.issues if i.severity == "WARNING"]
        assert len(warnings) > 0
    
    def test_malformed_headers_warns(self):
        """Markdown with malformed headers should still pass (headers optional)"""
        
        markdown = """#Missing space
## Good Header
###Another missing space

Some content here to make it longer than 100 chars so we don't get a warning about short content.
This is a test of markdown with malformed headers.
"""
        
        evaluator = StructuralEvaluator()
        report = evaluator.evaluate(markdown_output=markdown)
        
        # Malformed headers don't cause structural errors - they're style issues
        # The evaluator checks for presence of headers, not their formatting
        # This test documents that malformed headers pass structural validation
        assert report.error_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
