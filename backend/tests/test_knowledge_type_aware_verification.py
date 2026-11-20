"""
Tests for knowledge-type-aware numeric verification.

Ensures that the verifier distinguishes between:
- Factual numeric claims (definitions, facts, concepts)
- Illustrative code examples (examples, procedures)
- Mathematical expressions (formulas)
"""

import pytest
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import (
    KnowledgeDocument, Concept, Definition, Example, 
    Procedure, Fact, Formula
)


class TestIllustrativeArraySizes:
    """Test that illustrative array sizes in code examples don't cause false contradictions"""
    
    def test_array_size_in_example_not_contradicted(self):
        """Array size used in teaching example should not be flagged as contradiction"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Arrays store multiple values. You can access elements by their index position.",
                    position=1
                )
            ]
        )
        
        example = Example(
            knowledge_id="EXM_001",
            knowledge_type="example",
            document_id="TEST",
            content="Example of creating and accessing an array",
            exemplifies="Array creation",
            example_text="int[] numbers = new int[5]; numbers[0] = 1; numbers[1] = 2;",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[example],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "EXM_001")
        
        # Should NOT be contradicted - these are illustrative values in code
        assert verification.verification_status.status != "CONTRADICTED", \
            f"Example with illustrative array size should not be contradicted, got: {verification.verification_status.status}"


class TestGenuineNumericErrors:
    """Test that genuine numeric errors in definitions/facts are still caught"""
    
    def test_wrong_numeric_limit_in_definition_contradicted(self):
        """Incorrect numeric limit in definition should be flagged"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The byte data type can store values from negative 128 to positive 127.",
                    position=1
                )
            ]
        )
        
        definition = Definition(
            knowledge_id="DEF_001",
            knowledge_type="definition",
            document_id="TEST",
            content="Range of byte data type from -256 to 255",  # Wrong values
            term="byte range",
            definition_text="byte data type stores values from -256 to 255",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[definition],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "DEF_001")
        
        # Should be CONTRADICTED or UNSUPPORTED - wrong numeric values
        assert verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"], \
            f"Definition with wrong numbers should be contradicted or unsupported, got: {verification.verification_status.status}"


class TestCommaFormattedNumbers:
    """Test that comma-formatted numbers match correctly"""
    
    def test_comma_thousands_matches_without_comma(self):
        """100,000 in source should match 100000 in claim"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The maximum loan amount is 100,000 dollars.",
                    position=1
                )
            ]
        )
        
        fact = Fact(
            knowledge_id="FCT_001",
            knowledge_type="fact",
            document_id="TEST",
            content="Maximum loan is 100000",
            fact_text="The loan limit is 100000 dollars",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[fact],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FCT_001")
        
        # Should be SUPPORTED - numeric formats normalized
        assert verification.verification_status.status == "SUPPORTED", \
            f"Fact with normalized number should be supported, got: {verification.verification_status.status}"


class TestIncorrectExampleValues:
    """Test that genuinely wrong values in examples are caught"""
    
    def test_wrong_calculation_result_in_example_flagged(self):
        """Example with incorrect calculation result should be flagged"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="When you add 5 and 3, you get 8 as the result.",
                    position=1
                )
            ]
        )
        
        example = Example(
            knowledge_id="EXM_001",
            knowledge_type="example",
            document_id="TEST",
            content="Addition example showing 5 plus 3 equals 10",  # Wrong result
            exemplifies="Addition",
            example_text="5 + 3 = 10",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[example],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "EXM_001")
        
        # Should be CONTRADICTED or UNSUPPORTED - wrong calculation result
        assert verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"], \
            f"Example with wrong result should be contradicted/unsupported, got: {verification.verification_status.status}"


class TestFormulaConstants:
    """Test that formulas with constants are verified appropriately"""
    
    def test_formula_with_constant_supported(self):
        """Formula containing mathematical constant should be supported"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The area of a circle is calculated by multiplying pi times the radius squared. Pi is approximately 3.14.",
                    position=1
                )
            ]
        )
        
        formula = Formula(
            knowledge_id="FRM_001",
            knowledge_type="formula",
            document_id="TEST",
            content="Formula for circle area using pi and radius",
            formula_text="area = pi * radius² (pi ≈ 3.14)",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[formula],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FRM_001")
        
        # Should be SUPPORTED - 3.14 is an illustrative constant in formula
        # The formula structure and content match the source
        assert verification.verification_status.status in ["SUPPORTED", "INCONCLUSIVE"], \
            f"Formula with constant should be supported, got: {verification.verification_status.status}, reason: {verification.verification_status.reason}"
    
    def test_formula_semantic_paraphrase(self):
        """Formula should recognize semantic paraphrase without identical wording
        
        KNOWN LIMITATION: The deterministic verifier cannot recognize semantic
        equivalence between symbolic formula (A = πr²) and prose description
        ("area = pi * radius squared"). This would require LLM-based semantic
        verification.
        
        This test documents the limitation for future improvement.
        """
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="A circle's area is calculated using pi multiplied by the square of its radius.",
                    position=1
                )
            ]
        )
        
        formula = Formula(
            knowledge_id="FRM_002",
            knowledge_type="formula",
            document_id="TEST",
            content="Circle area formula",
            formula_text="A = πr²",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[formula],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FRM_002")
        
        # CURRENT BEHAVIOR: Deterministic verifier sees 0% keyword overlap
        # because "A = πr²" has no words in common with prose description
        # FUTURE IMPROVEMENT: Use LLM-based semantic verification for formulas
        # to recognize "A = πr²" ≡ "area = pi * radius²"
        
        # For now, document that this is UNSUPPORTED (not CONTRADICTED)
        assert verification.verification_status.status in ["UNSUPPORTED", "INCONCLUSIVE"], \
            f"Formula paraphrase should be UNSUPPORTED (not CONTRADICTED) with deterministic verifier, got: {verification.verification_status.status}"


class TestFormulaIncorrect:
    """Test that incorrect formulas are properly flagged"""
    
    def test_incorrect_formula_contradicted(self):
        """Formula with wrong mathematical relationship should be flagged"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The area of a circle is calculated by multiplying pi times the radius squared.",
                    position=1
                )
            ]
        )
        
        formula = Formula(
            knowledge_id="FRM_003",
            knowledge_type="formula",
            document_id="TEST",
            content="Incorrect circle area formula",
            formula_text="area = 2 * pi * radius",  # Wrong - this is circumference, not area
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[formula],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FRM_003")
        
        # Should be CONTRADICTED or UNSUPPORTED - wrong formula structure
        assert verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"], \
            f"Incorrect formula should be contradicted/unsupported, got: {verification.verification_status.status}"


class TestFormulaEquivalentNotation:
    """Test that formulas with equivalent mathematical notation are recognized
    
    KNOWN LIMITATION: The deterministic verifier has limited ability to match
    symbolic formulas with prose descriptions due to different vocabularies.
    This would benefit from LLM-based semantic verification.
    """
    
    def test_equivalent_notation_documented_limitation(self):
        """Document that symbolic vs prose formula matching has limitations"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The quadratic formula is x equals negative b plus or minus the square root of b squared minus 4ac, all divided by 2a.",
                    position=1
                )
            ]
        )
        
        formula = Formula(
            knowledge_id="FRM_004",
            knowledge_type="formula",
            document_id="TEST",
            content="Quadratic formula",
            formula_text="x = (-b ± √(b² - 4ac)) / (2a)",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[formula],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FRM_004")
        
        # CURRENT BEHAVIOR: Symbolic notation has low keyword overlap with prose
        # FUTURE IMPROVEMENT: Use LLM-based semantic verification for formulas
        # For now, document that symbolic formulas are UNSUPPORTED (not CONTRADICTED)
        assert verification.verification_status.status in ["UNSUPPORTED", "INCONCLUSIVE"], \
            f"Symbolic formula vs prose should be UNSUPPORTED (not CONTRADICTED), got: {verification.verification_status.status}"
    
    def test_matching_notation_supported(self):
        """Formula with matching notation style should be supported"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="The formula for calculating simple interest is: interest = principal * rate * time",
                    position=1
                )
            ]
        )
        
        formula = Formula(
            knowledge_id="FRM_005",
            knowledge_type="formula",
            document_id="TEST",
            content="Simple interest formula",
            formula_text="interest = principal * rate * time",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[formula],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "FRM_005")
        
        # Should be SUPPORTED - notation style matches exactly
        assert verification.verification_status.status == "SUPPORTED", \
            f"Formula with matching notation should be supported, got: {verification.verification_status.status}"


class TestArrayIndexInProcedure:
    """Test that array indices in procedure steps don't cause contradictions"""
    
    def test_array_index_in_procedure_step_not_contradicted(self):
        """Array index used in procedure step should not be flagged"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="To iterate through an array, you access each element by its index starting from the first position.",
                    position=1
                )
            ]
        )
        
        procedure = Procedure(
            knowledge_id="PRC_001",
            knowledge_type="procedure",
            document_id="TEST",
            content="Steps to iterate through array",
            procedure_name="Array iteration",
            steps=[
                "Start at index 0",
                "Access element at current index",
                "Move to next index",
                "Repeat until end"
            ],
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[procedure],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "PRC_001")
        
        # Should NOT be contradicted - "0" is illustrative starting index
        assert verification.verification_status.status != "CONTRADICTED", \
            f"Procedure with index should not be contradicted, got: {verification.verification_status.status}"


class TestConceptWithIllustrativeNumber:
    """Test that concepts with illustrative examples are handled correctly"""
    
    def test_concept_with_example_value_supported(self):
        """Concept with illustrative value should be supported if content matches"""
        
        source_doc = SourceDocument(
            document_id="TEST",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST",
                    type="paragraph",
                    content_role="content",
                    text="Type casting converts a value from one data type to another, such as converting an integer to a double.",
                    position=1
                )
            ]
        )
        
        concept = Concept(
            knowledge_id="CON_001",
            knowledge_type="concept",
            document_id="TEST",
            content="Explicit type conversion, e.g., (double) 5 converts integer to double",
            concept_name="Type casting",
            source_unit_ids=["S001"]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST",
            source_filename="test.txt",
            extraction_timestamp="2024-01-01T00:00:00",
            total_items=1,
            concepts=[concept],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[],
            relationships=[],
            extraction_metadata={}
        )
        
        verifier = DeterministicSemanticVerifier()
        results = verifier.verify(knowledge_doc, source_doc)
        
        verification = next(v for v in results.claim_verifications if v.knowledge_id == "CON_001")
        
        # Should be SUPPORTED or INCONCLUSIVE - "5" is illustrative, concept is correct
        # NOT contradicted because concept explains the general principle
        assert verification.verification_status.status != "CONTRADICTED", \
            f"Concept with example should not be contradicted if principle matches, got: {verification.verification_status.status}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
