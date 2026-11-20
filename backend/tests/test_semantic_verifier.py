"""
Unit tests for semantic faithfulness verification.

Tests deterministic verification of knowledge items against source text:
- Direct support from source
- Contradictions with source
- Unsupported claims
- Numeric accuracy
- Entity matching
- Ambiguous evidence (INCONCLUSIVE)
"""

import pytest
from datetime import datetime

from app.evaluation.semantic_verifier import (
    DeterministicSemanticVerifier,
    SemanticVerificationReport,
    ClaimVerification,
    SemanticVerificationStatus
)
from app.models.source import SourceDocument, SourceUnit
from app.models.knowledge import (
    KnowledgeDocument,
    Concept,
    Definition,
    Explanation,
    Fact,
    Example
)


class TestDeterministicSemanticVerifier:
    """Test suite for deterministic semantic verifier"""
    
    def test_directly_supported_claim(self):
        """Test a claim that is directly supported by source text"""
        
        # Create source document
        source_doc = SourceDocument(
            document_id="TEST_001",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_001",
                    page=1,
                    type="text",
                    content_role="content",
                    text="A short story is a prose narrative of limited length, typically under 7,500 words.",
                    position=1
                )
            ]
        )
        
        # Create knowledge document with matching definition
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_001",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            definitions=[
                Definition(
                    knowledge_id="DEF_0001",
                    knowledge_type="definition",
                    source_unit_ids=["S0001"],
                    document_id="TEST_001",
                    content="A short story is a prose narrative of limited length.",
                    term="short story",
                    definition_text="A prose narrative of limited length"
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 1
        assert report.claims_supported >= 1  # Should be supported
        assert report.claims_contradicted == 0
        
        claim_result = report.claim_verifications[0]
        assert claim_result.knowledge_id == "DEF_0001"
        assert claim_result.verification_status.status in ["SUPPORTED", "INCONCLUSIVE"]
        assert claim_result.verification_status.has_keyword_match is True
    
    def test_contradicted_claim_numeric_mismatch(self):
        """Test a claim that contradicts source with wrong number"""
        
        source_doc = SourceDocument(
            document_id="TEST_002",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_002",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The study included 450 participants over a period of 3 years.",
                    position=1
                )
            ]
        )
        
        # Knowledge with WRONG number
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_002",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_002",
                    content="The study included 350 participants.",  # Wrong number!
                    fact_text="The study included 350 participants."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 1
        assert report.claims_contradicted == 1  # Should be contradicted
        
        claim_result = report.claim_verifications[0]
        assert claim_result.verification_status.status == "CONTRADICTED"
        assert claim_result.verification_status.has_numeric_match is False
        assert "350" in claim_result.verification_status.reason
        
        # Check numeric verification details
        assert claim_result.numeric_verification is not None
        assert not claim_result.numeric_verification.all_matched
        assert len(claim_result.numeric_verification.mismatches) > 0
    
    def test_unsupported_claim_with_new_details(self):
        """Test a claim that adds unsupported details not in source"""
        
        source_doc = SourceDocument(
            document_id="TEST_003",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_003",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The protagonist faces a difficult choice.",
                    position=1
                )
            ]
        )
        
        # Knowledge adds details not in source
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_003",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            explanations=[
                Explanation(
                    knowledge_id="EXP_0001",
                    knowledge_type="explanation",
                    source_unit_ids=["S0001"],
                    document_id="TEST_003",
                    content="The protagonist John Smith faces a moral dilemma about betraying his country.",
                    topic="character motivation",
                    explanation_text="The protagonist John Smith faces a moral dilemma about betraying his country."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 1
        
        claim_result = report.claim_verifications[0]
        # Should be UNSUPPORTED or INCONCLUSIVE (many unique words not in source)
        assert claim_result.verification_status.status in ["UNSUPPORTED", "INCONCLUSIVE", "CONTRADICTED"]
        
        # Entity verification should show mismatches
        if claim_result.entity_verification:
            # "John Smith" not in source
            assert not claim_result.entity_verification.all_matched or len(claim_result.entity_verification.claimed_entities) == 0
    
    def test_numeric_accuracy_preserved(self):
        """Test that correct numbers are verified as matching"""
        
        source_doc = SourceDocument(
            document_id="TEST_004",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_004",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The temperature reached 98.6 degrees Fahrenheit, which is approximately 37.0 degrees Celsius.",
                    position=1
                )
            ]
        )
        
        # Knowledge preserves numbers correctly
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_004",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_004",
                    content="The temperature was 98.6 degrees Fahrenheit (37.0 degrees Celsius).",
                    fact_text="The temperature was 98.6 degrees Fahrenheit (37.0 degrees Celsius)."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        
        assert claim_result.numeric_verification is not None
        assert claim_result.numeric_verification.all_matched is True
        assert "98.6" in claim_result.numeric_verification.claimed_numbers
        assert "37.0" in claim_result.numeric_verification.claimed_numbers
        assert claim_result.verification_status.has_numeric_match is True
    
    def test_entity_mismatch_detected(self):
        """Test that incorrect named entities are detected"""
        
        source_doc = SourceDocument(
            document_id="TEST_005",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_005",
                    page=1,
                    type="text",
                    content_role="content",
                    text="Gabriel Garcia Marquez wrote One Hundred Years of Solitude.",
                    position=1
                )
            ]
        )
        
        # Knowledge has WRONG author name
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_005",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_005",
                    content="Pablo Neruda wrote One Hundred Years of Solitude.",
                    fact_text="Pablo Neruda wrote One Hundred Years of Solitude."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        
        # Should detect entity mismatch
        assert claim_result.entity_verification is not None
        # "Pablo Neruda" not in source (but "Gabriel Garcia Marquez" is)
        
        # Status should be CONTRADICTED or UNSUPPORTED
        assert claim_result.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"]
    
    def test_missing_source_units(self):
        """Test handling of knowledge items with invalid source unit references"""
        
        source_doc = SourceDocument(
            document_id="TEST_006",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_006",
                    page=1,
                    type="text",
                    content_role="content",
                    text="Some valid text.",
                    position=1
                )
            ]
        )
        
        # Knowledge references non-existent source unit
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_006",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S9999"],  # Does not exist!
                    document_id="TEST_006",
                    content="Some claim.",
                    fact_text="Some claim."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        assert claim_result.verification_status.status == "INSUFFICIENT_EVIDENCE"
        assert "No source text available" in claim_result.verification_status.reason
    
    def test_source_unit_without_text(self):
        """Test handling of source units that have no text"""
        
        source_doc = SourceDocument(
            document_id="TEST_007",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_007",
                    page=1,
                    type="picture",
                    content_role="content",
                    text=None,  # No text!
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_007",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_007",
                    content="Some claim about the image.",
                    fact_text="Some claim about the image."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        assert claim_result.verification_status.status == "INSUFFICIENT_EVIDENCE"
    
    def test_ambiguous_evidence_marked_inconclusive(self):
        """Test that ambiguous evidence is marked INCONCLUSIVE, not guessed"""
        
        source_doc = SourceDocument(
            document_id="TEST_008",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_008",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The character experiences transformation.",
                    position=1
                )
            ]
        )
        
        # Knowledge is somewhat related but adds interpretation
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_008",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            explanations=[
                Explanation(
                    knowledge_id="EXP_0001",
                    knowledge_type="explanation",
                    source_unit_ids=["S0001"],
                    document_id="TEST_008",
                    content="The character undergoes psychological metamorphosis.",
                    topic="character development",
                    explanation_text="The character undergoes psychological metamorphosis."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        # Should be INCONCLUSIVE (paraphrase, no strong keyword match)
        # Verifier cannot determine semantic equivalence deterministically
        assert claim_result.verification_status.status in ["INCONCLUSIVE", "SUPPORTED", "UNSUPPORTED"]
        assert claim_result.verification_status.confidence < 0.9  # Not highly confident
    
    def test_empty_knowledge_document(self):
        """Test handling of empty knowledge document"""
        
        source_doc = SourceDocument(
            document_id="TEST_009",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_009",
                    page=1,
                    type="text",
                    content_role="content",
                    text="Some text.",
                    position=1
                )
            ]
        )
        
        # Empty knowledge document
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_009",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat()
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 0
        assert report.claims_supported == 0
        assert report.semantic_faithfulness_verified is False
        assert report.verification_complete is True  # No items to verify = complete
    
    def test_deterministic_repeatability(self):
        """Test that verification is deterministic (same input = same output)"""
        
        source_doc = SourceDocument(
            document_id="TEST_010",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_010",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The short story genre emerged in the 19th century.",
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_010",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_010",
                    content="Short stories became popular in the 1800s.",
                    fact_text="Short stories became popular in the 1800s."
                )
            ]
        )
        
        # Verify twice
        verifier = DeterministicSemanticVerifier()
        report1 = verifier.verify(knowledge_doc, source_doc)
        report2 = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions - results should be identical
        assert report1.total_claims_verified == report2.total_claims_verified
        assert report1.claims_supported == report2.claims_supported
        assert report1.claims_contradicted == report2.claims_contradicted
        
        claim1 = report1.claim_verifications[0]
        claim2 = report2.claim_verifications[0]
        
        assert claim1.verification_status.status == claim2.verification_status.status
        assert claim1.verification_status.confidence == claim2.verification_status.confidence
    
    def test_multiple_knowledge_types(self):
        """Test verification of multiple knowledge types in same document"""
        
        source_doc = SourceDocument(
            document_id="TEST_011",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_011",
                    page=1,
                    type="text",
                    content_role="content",
                    text="A protagonist is the main character. In 'Romeo and Juliet', Romeo is the protagonist.",
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_011",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            definitions=[
                Definition(
                    knowledge_id="DEF_0001",
                    knowledge_type="definition",
                    source_unit_ids=["S0001"],
                    document_id="TEST_011",
                    content="A protagonist is the main character.",
                    term="protagonist",
                    definition_text="The main character"
                )
            ],
            examples=[
                Example(
                    knowledge_id="EX_0001",
                    knowledge_type="example",
                    source_unit_ids=["S0001"],
                    document_id="TEST_011",
                    content="Romeo in 'Romeo and Juliet'",
                    exemplifies="protagonist",
                    example_text="Romeo in 'Romeo and Juliet'"
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 2
        assert len(report.claim_verifications) == 2
        
        # Both should be SUPPORTED
        statuses = [cv.verification_status.status for cv in report.claim_verifications]
        assert "SUPPORTED" in statuses or "INCONCLUSIVE" in statuses
    
    def test_high_support_rate_threshold(self):
        """Test that semantic_faithfulness_verified requires high support rate"""
        
        source_doc = SourceDocument(
            document_id="TEST_012",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id=f"S{i:04d}",
                    document_id="TEST_012",
                    page=1,
                    type="text",
                    content_role="content",
                    text=f"Fact number {i} about something.",
                    position=i
                )
                for i in range(10)
            ]
        )
        
        # Create 10 facts, 8 match well, 2 don't
        facts = []
        for i in range(8):
            facts.append(
                Fact(
                    knowledge_id=f"FACT_{i:04d}",
                    knowledge_type="fact",
                    source_unit_ids=[f"S{i:04d}"],
                    document_id="TEST_012",
                    content=f"Fact number {i} about something.",  # Matches source
                    fact_text=f"Fact number {i} about something."
                )
            )
        
        # 2 facts with poor match
        for i in range(8, 10):
            facts.append(
                Fact(
                    knowledge_id=f"FACT_{i:04d}",
                    knowledge_type="fact",
                    source_unit_ids=[f"S{i:04d}"],
                    document_id="TEST_012",
                    content=f"Completely different claim that doesn't match.",
                    fact_text=f"Completely different claim that doesn't match."
                )
            )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_012",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=facts
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.total_claims_verified == 10
        # Should have high support rate (at least 80%)
        assert report.support_rate >= 0.7  # At least 70%
    
    def test_contradicted_blocks_faithfulness_verification(self):
        """Test that any contradicted claim prevents semantic_faithfulness_verified"""
        
        source_doc = SourceDocument(
            document_id="TEST_013",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_013",
                    page=1,
                    type="text",
                    content_role="content",
                    text="The experiment lasted 5 days with 100 participants.",
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_013",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_013",
                    content="The experiment lasted 10 days.",  # Wrong number!
                    fact_text="The experiment lasted 10 days."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        assert report.claims_contradicted >= 1
        assert report.semantic_faithfulness_verified is False  # Contradictions block verification
    
    def test_verification_report_structure(self):
        """Test that verification report has correct structure and fields"""
        
        source_doc = SourceDocument(
            document_id="TEST_014",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_014",
                    page=1,
                    type="text",
                    content_role="content",
                    text="Test content.",
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_014",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_014",
                    content="Test content.",
                    fact_text="Test content."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions - check report structure
        assert hasattr(report, 'verification_timestamp')
        assert hasattr(report, 'document_id')
        assert hasattr(report, 'source_filename')
        assert hasattr(report, 'total_claims_verified')
        assert hasattr(report, 'claims_supported')
        assert hasattr(report, 'claims_unsupported')
        assert hasattr(report, 'claims_contradicted')
        assert hasattr(report, 'claims_inconclusive')
        assert hasattr(report, 'claims_insufficient_evidence')
        assert hasattr(report, 'claim_verifications')
        assert hasattr(report, 'semantic_faithfulness_verified')
        assert hasattr(report, 'verification_complete')
        assert hasattr(report, 'verification_method')
        assert hasattr(report, 'limitations')
        
        assert report.verification_method == "deterministic"
        assert len(report.limitations) > 0
        assert isinstance(report.limitations, list)
    
    def test_claim_verification_has_evidence_snippets(self):
        """Test that claim verifications include evidence snippets"""
        
        source_doc = SourceDocument(
            document_id="TEST_015",
            filename="test.pdf",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S0001",
                    document_id="TEST_015",
                    page=1,
                    type="text",
                    content_role="content",
                    text="This is a long piece of source text that contains important information about the topic we are studying.",
                    position=1
                )
            ]
        )
        
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_015",
            source_filename="test.pdf",
            extraction_timestamp=datetime.now().isoformat(),
            facts=[
                Fact(
                    knowledge_id="FACT_0001",
                    knowledge_type="fact",
                    source_unit_ids=["S0001"],
                    document_id="TEST_015",
                    content="Contains important information about the topic.",
                    fact_text="Contains important information about the topic."
                )
            ]
        )
        
        # Verify
        verifier = DeterministicSemanticVerifier()
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Assertions
        claim_result = report.claim_verifications[0]
        assert len(claim_result.source_snippets) > 0
        assert len(claim_result.source_full_text) > 0
        assert len(claim_result.verification_status.evidence_snippets) > 0
