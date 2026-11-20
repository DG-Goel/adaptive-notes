"""
Regression tests for semantic verifier improvements.

Tests cover confirmed false positive categories from Java validation:
- Imperative verbs in procedures
- Numeric format normalization
- Java/programming keywords
- Case-insensitive entity matching
"""

import pytest
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import KnowledgeDocument, Concept, Procedure, Example


class TestImperativeVerbFiltering:
    """Test that imperative verbs in procedures are not flagged as missing entities"""
    
    def test_procedure_with_imperative_verbs_not_contradicted(self):
        """Procedures with imperative verbs should not be flagged for entity mismatch"""
        
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
                    text="First, download the installer from the website. Then click the install button and enter your password.",
                    position=1
                )
            ]
        )
        
        procedure = Procedure(
            knowledge_id="PRC_001",
            knowledge_type="procedure",
            document_id="TEST",
            content="Installation procedure: Download and install software",
            procedure_name="Installation Steps",
            steps=["Download installer from website", "Click install button", "Enter password"],
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
        
        # Should NOT be contradicted due to imperative verbs
        proc_verification = next(v for v in results.claim_verifications if v.knowledge_id == "PRC_001")
        assert proc_verification.verification_status.status != "CONTRADICTED" or \
               "Entity mismatch" not in proc_verification.verification_status.reason


class TestNumericFormatNormalization:
    """Test that numeric format differences are normalized"""
    
    def test_comma_thousands_separator_normalized(self):
        """Numbers with comma separators should match numbers without"""
        
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
                    text="The maximum value is 100,000 dollars.",
                    position=1
                )
            ]
        )
        
        example = Example(
            knowledge_id="EXM_001",
            knowledge_type="example",
            document_id="TEST",
            content="Example code checking value against maximum",
            exemplifies="Maximum Value",
            example_text="if (value > 100000) { // check if over max }",
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
        
        # Should be SUPPORTED or at least not CONTRADICTED for numeric reasons
        exm_verification = next(v for v in results.claim_verifications if v.knowledge_id == "EXM_001")
        assert exm_verification.verification_status.status != "CONTRADICTED" or \
               "Numeric contradiction" not in exm_verification.verification_status.reason


class TestProgrammingKeywordFiltering:
    """Test that Java/programming keywords are not flagged as missing entities"""
    
    def test_java_keywords_not_flagged(self):
        """Java keywords like String, Scanner should not cause entity mismatches"""
        
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
                    text="We use the string class to store text and the scanner class to read input from the user.",
                    position=1
                )
            ]
        )
        
        concept = Concept(
            knowledge_id="CON_001",
            document_id="TEST",
            concept_name="Input Reading",
            content="String and Scanner classes are used for text storage and user input.",
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
        
        # Should NOT be contradicted for String/Scanner entity mismatch
        con_verification = next(v for v in results.claim_verifications if v.knowledge_id == "CON_001")
        assert con_verification.verification_status.status != "CONTRADICTED" or \
               "Entity mismatch" not in con_verification.verification_status.reason


class TestCaseInsensitiveMatching:
    """Test that case differences don't cause false entity mismatches"""
    
    def test_case_insensitive_entity_match(self):
        """Entities should match case-insensitively"""
        
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
                    text="The java runtime environment is required to run applications.",
                    position=1
                )
            ]
        )
        
        concept = Concept(
            knowledge_id="CON_001",
            document_id="TEST",
            concept_name="Runtime Environment",
            content="Java Runtime Environment is needed for execution.",
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
        
        # Should NOT be contradicted due to case differences
        con_verification = next(v for v in results.claim_verifications if v.knowledge_id == "CON_001")
        assert con_verification.verification_status.status != "CONTRADICTED" or \
               "Entity mismatch" not in con_verification.verification_status.reason


class TestGenuineContradictionsStillDetected:
    """Ensure genuine contradictions are still caught after improvements"""
    
    def test_wrong_number_still_contradicted(self):
        """Actually wrong numbers should still be flagged"""
        
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
                    text="The array has 5 elements.",
                    position=1
                )
            ]
        )
        
        concept = Concept(
            knowledge_id="CON_001",
            document_id="TEST",
            concept_name="Array Size",
            content="The array contains 10 elements.",
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
        
        # Should be CONTRADICTED or UNSUPPORTED
        con_verification = next(v for v in results.claim_verifications if v.knowledge_id == "CON_001")
        assert con_verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"]
    
    def test_wrong_entity_still_detected_via_low_keyword_overlap(self):
        """Entity mismatches should be caught via low keyword overlap if not entity filtering"""
        
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
                    text="The algorithm requires at least 50 iterations to converge properly.",
                    position=1
                )
            ]
        )
        
        concept = Concept(
            knowledge_id="CON_001",
            document_id="TEST",
            concept_name="Iteration Count",
            content="The algorithm needs 10 iterations.",  # Wrong number
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
        
        # Should be CONTRADICTED or UNSUPPORTED (10 vs 50)
        con_verification = next(v for v in results.claim_verifications if v.knowledge_id == "CON_001")
        assert con_verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"]
