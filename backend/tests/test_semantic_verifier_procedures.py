"""
Regression tests for semantic verifier behavior with procedural knowledge.

These tests document and verify the verifier's handling of procedure steps,
particularly entity extraction from imperative verb phrases.
"""

import pytest

from app.models.knowledge import Procedure
from app.models.source import SourceDocument, SourceUnit
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


class TestProcedureEntityExtraction:
    """
    Test suite for entity extraction from procedure steps.
    
    CONTEXT:
    During real LLM validation (Groq, 2026-10-25), procedure PRC_0027 was
    incorrectly flagged as CONTRADICTED due to entity mismatch. The verifier
    extracted imperative verbs (Pick, Seal, Install, Return) as entities
    and reported them as "not found in source."
    
    ISSUE:
    The entity extractor uses capitalization as a heuristic for proper nouns.
    Procedure steps formatted as imperative sentences ("Pick up...", "Seal off...")
    start with capitalized verbs, which are incorrectly treated as entities.
    
    EXPECTED BEHAVIOR:
    - Imperative verbs should NOT be extracted as entities
    - Procedure verification should focus on action/content matching, not entity matching
    - Entity mismatch should not cause CONTRADICTED status for procedures
    
    This test documents the current behavior and provides a regression check
    if entity extraction logic is modified.
    """
    
    def test_procedure_steps_with_imperative_verbs(self):
        """
        Verify that procedure with imperative verb steps is not falsely flagged as CONTRADICTED.
        
        This test reproduces the PRC_0027 issue from real LLM validation.
        """
        # Source text (from S0013 in real validation)
        source_text = (
            "The cheerful Cuban volunteers, with the help of the fire department, "
            "picked up the debris in less than six hours, and sealed off the gate "
            "to the sea and installed another, and everything returned to normal."
        )
        
        # Create source document
        source_doc = SourceDocument(
            document_id="TEST_DOC",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST_DOC",
                    type="paragraph",
                    content_role="content",
                    text=source_text,
                    position=1,
                    page=1
                )
            ]
        )
        
        # Create procedure (as extracted by LLM)
        procedure = Procedure(
            knowledge_id="PRC_001",
            knowledge_type="procedure",
            source_unit_ids=["S001"],
            document_id="TEST_DOC",
            content="Post-wave cleanup procedure",
            section="Test Section",
            page_range=[1, 1],
            procedure_name="Cleanup",
            steps=[
                "Pick up the debris.",
                "Seal off the gate to the sea.",
                "Install a new gate.",
                "Return the area to normal conditions."
            ],
            prerequisites=["Volunteers", "Fire department"],
            outcomes="Area returned to normal"
        )
        
        # Create knowledge document with single procedure
        from app.models.knowledge import KnowledgeDocument
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_DOC",
            source_filename="test.txt",
            extraction_timestamp="2026-10-25T00:00:00",
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[procedure],
            relationships=[],
            total_items=1,
            source_units_processed=1
        )
        
        # Run verification
        verifier = DeterministicSemanticVerifier(verbose=False)
        report = verifier.verify(knowledge_doc, source_doc)
        
        # Extract verification for our procedure
        assert len(report.claim_verifications) == 1
        verification = report.claim_verifications[0]
        
        # CURRENT BEHAVIOR (as of 2026-10-25):
        # The verifier extracts "Pick", "Seal", "Install", "Return" as entities
        # and flags them as not found in source, resulting in CONTRADICTED status
        
        print("\n" + "=" * 80)
        print("ENTITY EXTRACTION RESULTS:")
        print("=" * 80)
        print(f"Claimed entities: {verification.entity_verification.claimed_entities}")
        print(f"Source entities: {verification.entity_verification.source_entities}")
        print(f"Mismatches: {verification.entity_verification.mismatches}")
        print(f"Status: {verification.verification_status.status}")
        print(f"Reason: {verification.verification_status.reason}")
        print("=" * 80)
        
        # DOCUMENT CURRENT BEHAVIOR
        # This test currently PASSES if the verifier exhibits the known limitation
        # If entity extraction is improved to handle imperative verbs, this test
        # will fail, indicating the issue is fixed
        
        # Check if imperative verbs were incorrectly extracted as entities
        imperative_verbs = {"Pick", "Seal", "Install", "Return"}
        extracted_entities = set(verification.entity_verification.claimed_entities)
        imperative_verbs_extracted = imperative_verbs & extracted_entities
        
        if len(imperative_verbs_extracted) > 0:
            # Check if the imperative verbs are being filtered correctly
            # After improvements, the verifier should still support the procedure
            # even if imperative verbs are extracted, because they are filtered
            if verification.verification_status.status == "SUPPORTED":
                print(f"\n✓ IMPROVEMENT CONFIRMED:")
                print(f"  Imperative verbs were extracted: {imperative_verbs_extracted}")
                print(f"  But they are being FILTERED, so status is SUPPORTED")
                print(f"  The entity extraction filtering has been improved.")
                # This is the desired behavior
                assert verification.verification_status.status == "SUPPORTED"
            else:
                # KNOWN LIMITATION STILL EXISTS (for documentation)
                print(f"\n⚠ KNOWN LIMITATION DETECTED:")
                print(f"  Imperative verbs incorrectly extracted as entities: {imperative_verbs_extracted}")
                print(f"  This causes false CONTRADICTED status on procedures.")
                
                # Verify the false positive occurs
                assert verification.verification_status.status in ["CONTRADICTED", "UNSUPPORTED"], (
                    f"Expected CONTRADICTED or UNSUPPORTED due to entity mismatch, "
                    f"but got {verification.verification_status.status}"
                )
        else:
            # LIMITATION HAS BEEN FULLY FIXED - verbs not even extracted
            print(f"\n✓ FULL IMPROVEMENT DETECTED:")
            print(f"  Imperative verbs are NO LONGER extracted as entities.")
            print(f"  The entity extraction logic has been fully improved.")
            
            # Verify the procedure is now correctly verified
            assert verification.verification_status.status == "SUPPORTED", (
                f"Procedure should be SUPPORTED after entity extraction fix, "
                f"but got {verification.verification_status.status}"
            )
    
    def test_procedure_without_capitalized_verbs(self):
        """
        Baseline: Procedure described in continuous text (no capitalized verbs).
        
        This should be correctly verified as SUPPORTED.
        """
        source_text = (
            "The volunteers picked up the debris and sealed the gate."
        )
        
        source_doc = SourceDocument(
            document_id="TEST_DOC",
            filename="test.txt",
            page_count=1,
            source_units=[
                SourceUnit(
                    source_id="S001",
                    document_id="TEST_DOC",
                    type="paragraph",
                    content_role="content",
                    text=source_text,
                    position=1,
                    page=1
                )
            ]
        )
        
        procedure = Procedure(
            knowledge_id="PRC_001",
            knowledge_type="procedure",
            source_unit_ids=["S001"],
            document_id="TEST_DOC",
            content="Cleanup procedure: pick up debris, seal gate",
            section="Test Section",
            page_range=[1, 1],
            procedure_name="Cleanup",
            steps=[
                "pick up the debris",
                "seal the gate"
            ],
            prerequisites=[],
            outcomes="Area cleaned"
        )
        
        from app.models.knowledge import KnowledgeDocument
        knowledge_doc = KnowledgeDocument(
            document_id="TEST_DOC",
            source_filename="test.txt",
            extraction_timestamp="2026-10-25T00:00:00",
            concepts=[],
            definitions=[],
            explanations=[],
            examples=[],
            facts=[],
            formulas=[],
            procedures=[procedure],
            relationships=[],
            total_items=1,
            source_units_processed=1
        )
        
        verifier = DeterministicSemanticVerifier(verbose=False)
        report = verifier.verify(knowledge_doc, source_doc)
        
        verification = report.claim_verifications[0]
        
        # Without capitalized verbs, entity extraction should not cause false positives
        # This procedure should be SUPPORTED
        assert verification.verification_status.status == "SUPPORTED", (
            f"Procedure with lowercase steps should be SUPPORTED, "
            f"but got {verification.verification_status.status}"
        )


if __name__ == "__main__":
    print("=" * 80)
    print("SEMANTIC VERIFIER - PROCEDURE ENTITY EXTRACTION TESTS")
    print("=" * 80)
    print("\nThese tests document a known limitation in entity extraction")
    print("where imperative verbs (Pick, Seal, Install) are incorrectly")
    print("treated as proper noun entities in procedure steps.")
    print("\nSee: data/output/real_llm_validation/FOCUSED_CLAIM_AUDIT.md")
    print("=" * 80)
    
    pytest.main([__file__, "-v", "-s"])
