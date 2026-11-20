"""
Complete pipeline runner: Ingestion → Extraction → Analysis → Representation → Assembly → Rendering → Evaluation

Executes all stages in dependency order with proper error handling.
Uses actual classes and schemas from the codebase.

Exit codes:
  0: Success (all stages completed, evaluation PASS or WARNING)
  1: Stage failure or evaluation FAIL/INCOMPLETE
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import all pipeline stage classes
from app.ingestion.docling_parser import DoclingParser
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm_provider import MockLLMProvider
from app.analysis.analyzer import ContentAnalyzer
from app.analysis.characteristics import AnalyzedKnowledgeDocument
from app.representation.selector import RepresentationSelector
from app.representation.models import RepresentationDocument
from app.assembly.assembler import NoteAssembler
from app.assembly.models import AssembledNotesDocument
from app.rendering.renderer import MarkdownRenderer
from app.rendering.models import RenderedDocument
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.evaluation.structural_evaluator import StructuralEvaluator


# Configuration
DOCUMENT_ID = "TEST_DOC"
INPUT_PDF = "data/input/test.pdf"
OUTPUT_DIR = Path("data/output")

# Output files
SOURCE_UNITS_JSON = OUTPUT_DIR / "source_units.json"
KNOWLEDGE_JSON = OUTPUT_DIR / "knowledge_document.json"
ANALYZED_JSON = OUTPUT_DIR / "analyzed_knowledge.json"
REPRESENTATIONS_JSON = OUTPUT_DIR / "representations.json"
ASSEMBLED_JSON = OUTPUT_DIR / "assembled_notes.json"
RENDER_MANIFEST_JSON = OUTPUT_DIR / "render_manifest.json"
RENDERED_MD = OUTPUT_DIR / "rendered_notes.md"
EVALUATION_JSON = OUTPUT_DIR / "evaluation_report.json"
SEMANTIC_VERIFICATION_JSON = OUTPUT_DIR / "semantic_verification_report.json"
STRUCTURAL_EVAL_REPRESENTATION_JSON = OUTPUT_DIR / "structural_eval_representation.json"
STRUCTURAL_EVAL_ASSEMBLY_JSON = OUTPUT_DIR / "structural_eval_assembly.json"
STRUCTURAL_EVAL_MARKDOWN_JSON = OUTPUT_DIR / "structural_eval_markdown.json"


def print_stage_header(stage_name: str):
    """Print stage header"""
    print("\n" + "=" * 80)
    print(f"STAGE: {stage_name}")
    print("=" * 80)


def print_stage_success(stage_name: str, details: str = ""):
    """Print stage success"""
    print(f"[OK] {stage_name} completed successfully")
    if details:
        print(f"  {details}")


def print_stage_error(stage_name: str, error: str):
    """Print stage error and exit"""
    print(f"[ERROR] {stage_name} FAILED")
    print(f"  Error: {error}")
    sys.exit(1)


def create_mock_responses():
    """
    Create mock LLM responses for extraction.
    
    Based on actual content from test.pdf - these are NOT real LLM outputs,
    they are hand-crafted mocks for testing the pipeline without API costs.
    """
    mock_response_chunk_0 = json.dumps({
        "concepts": [
            {
                "concept_name": "dream interpretation",
                "aliases": ["dream reading", "oneiromancy"],
                "content": "The practice of assigning meaning to dreams",
                "source_unit_ids": ["S0022", "S0027"]
            }
        ],
        "definitions": [],
        "explanations": [
            {
                "topic": "dream seller's trade",
                "explanation_text": "The protagonist sold interpretations of dreams as her only trade. She learned to interpret dreams as a child and continued this practice, deciding what each person should do based on their dreams.",
                "explanation_type": "functional",
                "content": "The protagonist sold interpretations of dreams as her only trade, deciding what people should do based on their dreams.",
                "source_unit_ids": ["S0021", "S0022", "S0027"]
            }
        ],
        "examples": [
            {
                "exemplifies": "dream interpretation",
                "example_text": "When someone dreamed of drowning, she interpreted it to mean they shouldn't eat sweets, not that they would drown.",
                "example_type": "case_study",
                "content": "A dream about drowning was interpreted as a warning not to eat sweets.",
                "source_unit_ids": ["S0023"]
            }
        ],
        "facts": [
            {
                "fact_text": "The protagonist was the third of eleven children born to a prosperous shopkeeper in old Caldas.",
                "fact_type": "biographical",
                "content": "The protagonist was the third of eleven children born to a prosperous shopkeeper in old Caldas.",
                "source_unit_ids": ["S0022"]
            }
        ],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    mock_response_chunk_1 = json.dumps({
        "concepts": [
            {
                "concept_name": "prophetic dream",
                "aliases": ["premonition"],
                "content": "A dream believed to predict future events",
                "source_unit_ids": ["S0029", "S0030"]
            }
        ],
        "definitions": [],
        "explanations": [
            {
                "topic": "impact of prophetic dream",
                "explanation_text": "After the protagonist dreamed about the narrator, she warned him to leave Vienna immediately and not return for five years. The narrator followed this warning, considering himself a survivor of some disaster he never experienced.",
                "explanation_type": "causal",
                "content": "A prophetic dream led to a warning that caused the narrator to leave Vienna immediately.",
                "source_unit_ids": ["S0029", "S0030"]
            }
        ],
        "examples": [],
        "facts": [
            {
                "fact_text": "The narrator stayed in Vienna for more than a month, sharing straitened circumstances with other students while waiting for money that never arrived.",
                "fact_type": "biographical",
                "content": "The narrator stayed in Vienna for more than a month waiting for money that never arrived.",
                "source_unit_ids": ["S0028"]
            }
        ],
        "formulas": [],
        "procedures": [],
        "relationships": [
            {
                "relationship_type": "causes",
                "subject": "prophetic dream",
                "object": "departure from Vienna",
                "description": "The protagonist's dream about the narrator caused him to leave Vienna",
                "content": "The prophetic dream caused the narrator to leave Vienna immediately.",
                "source_unit_ids": ["S0029", "S0030"]
            }
        ]
    })
    
    default_response = json.dumps({
        "concepts": [],
        "definitions": [],
        "explanations": [],
        "examples": [],
        "facts": [],
        "formulas": [],
        "procedures": [],
        "relationships": []
    })
    
    return {
        "CHUNK_000": mock_response_chunk_0,
        "CHUNK_001": mock_response_chunk_1,
    }, default_response


def main():
    # Document ID - can be updated if loading existing source with different ID
    document_id = DOCUMENT_ID
    
    print("=" * 80)
    print("ADAPTIVE NOTES PIPELINE")
    print("=" * 80)
    print(f"Document ID: {document_id}")
    print(f"Input PDF: {INPUT_PDF}")
    print(f"Using MOCK extraction (no real LLM)")
    print("=" * 80)
    
    # ========================================================================
    # STAGE 1: INGESTION (Load existing source units)
    # ========================================================================
    print_stage_header("1. INGESTION")
    
    # Check if source units already exist
    if not SOURCE_UNITS_JSON.exists():
        print(f"Note: {SOURCE_UNITS_JSON} not found")
        print("Attempting to parse PDF with Docling...")
        print("WARNING: Docling may crash on Windows due to PyTorch/threading issues")
        
        try:
            parser = DoclingParser(verbose=False, enable_ocr=False)
            source_doc = parser.parse(str(INPUT_PDF), document_id=document_id)
            
            # Save source units
            with open(SOURCE_UNITS_JSON, 'w', encoding='utf-8') as f:
                json.dump(source_doc.model_dump(), f, indent=2, ensure_ascii=False)
            
            print_stage_success("Ingestion (parsed)", f"{len(source_doc.source_units)} source units")
        except Exception as e:
            print_stage_error("Ingestion", 
                            f"Docling parsing failed: {e}. "
                            f"On Windows, generate source_units.json on Linux/macOS or use pre-generated file.")
    else:
        # Load existing source units
        print(f"Loading existing: {SOURCE_UNITS_JSON}")
        try:
            source_doc = SourceDocument.model_validate_json(
                SOURCE_UNITS_JSON.read_text(encoding='utf-8')
            )
            
            # Verify document ID
            if source_doc.document_id != document_id:
                print(f"  NOTE: source_units.json has document_id={source_doc.document_id}")
                print(f"       Using existing ID to preserve provenance")
                document_id = source_doc.document_id  # Use existing ID for consistency
            
            print_stage_success("Ingestion (loaded)", f"{len(source_doc.source_units)} source units, document_id={source_doc.document_id}")
        except Exception as e:
            print_stage_error("Ingestion", f"Failed to load source units: {e}")
    
    # ========================================================================
    # STAGE 2: EXTRACTION
    # ========================================================================
    print_stage_header("2. EXTRACTION")
    print("Note: Using MOCK LLM provider (hand-crafted responses, NOT real AI)")
    
    try:
        # Create mock provider
        mock_responses, default = create_mock_responses()
        llm = MockLLMProvider(responses=mock_responses, default_response=default)
        
        # Extract knowledge
        extractor = KnowledgeExtractor(llm_provider=llm, max_tokens_per_chunk=2000, verbose=False)
        knowledge_doc = extractor.extract(source_doc)
        
        # Save
        with open(KNOWLEDGE_JSON, 'w', encoding='utf-8') as f:
            json.dump(knowledge_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print_stage_success("Extraction", f"{knowledge_doc.total_items} knowledge items extracted")
    except Exception as e:
        print_stage_error("Extraction", str(e))
    
    # ========================================================================
    # STAGE 3: ANALYSIS
    # ========================================================================
    print_stage_header("3. ANALYSIS")
    
    try:
        analyzer = ContentAnalyzer()
        analyzed_doc = analyzer.analyze(knowledge_doc)
        
        # Save
        with open(ANALYZED_JSON, 'w', encoding='utf-8') as f:
            json.dump(analyzed_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print_stage_success("Analysis", f"{len(analyzed_doc.analyzed_items)} items analyzed")
    except Exception as e:
        print_stage_error("Analysis", str(e))
    
    # ========================================================================
    # STAGE 4: REPRESENTATION
    # ========================================================================
    print_stage_header("4. REPRESENTATION")
    
    try:
        selector = RepresentationSelector(verbose=False)
        represented_doc = selector.select(analyzed_doc)
        
        # Save
        with open(REPRESENTATIONS_JSON, 'w', encoding='utf-8') as f:
            json.dump(represented_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print_stage_success("Representation", f"{len(represented_doc.representations)} formats selected")
        
        # STRUCTURAL EVALUATION: Representations
        print("\n  → Running structural evaluation on representations...")
        structural_evaluator = StructuralEvaluator(verbose=False)
        repr_structural_report = structural_evaluator.evaluate(
            representation_doc=represented_doc,
            knowledge_doc=knowledge_doc
        )
        
        # Save structural evaluation report
        with open(STRUCTURAL_EVAL_REPRESENTATION_JSON, 'w', encoding='utf-8') as f:
            json.dump(repr_structural_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"  → Structural evaluation: {'PASSED' if repr_structural_report.passed else 'FAILED'}")
        print(f"     Errors: {repr_structural_report.error_count}, Warnings: {repr_structural_report.warning_count}")
        
        if not repr_structural_report.passed:
            print("\n[ERROR] Representation structural validation FAILED")
            for issue in repr_structural_report.issues:
                if issue.severity == "ERROR":
                    print(f"  - {issue.category}: {issue.reason}")
            sys.exit(1)
            
    except Exception as e:
        print_stage_error("Representation", str(e))
    
    # ========================================================================
    # STAGE 5: ASSEMBLY
    # ========================================================================
    print_stage_header("5. ASSEMBLY")
    
    try:
        assembler = NoteAssembler()
        assembled_doc = assembler.assemble(represented_doc)
        
        # Save
        with open(ASSEMBLED_JSON, 'w', encoding='utf-8') as f:
            json.dump(assembled_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        print_stage_success("Assembly", f"{assembled_doc.statistics.total_items} items in {assembled_doc.statistics.total_sections} sections")
        
        # STRUCTURAL EVALUATION: Assembly
        print("\n  → Running structural evaluation on assembly...")
        assembly_structural_report = structural_evaluator.evaluate(
            assembly_doc=assembled_doc,
            representation_doc=represented_doc
        )
        
        # Save structural evaluation report
        with open(STRUCTURAL_EVAL_ASSEMBLY_JSON, 'w', encoding='utf-8') as f:
            json.dump(assembly_structural_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"  → Structural evaluation: {'PASSED' if assembly_structural_report.passed else 'FAILED'}")
        print(f"     Errors: {assembly_structural_report.error_count}, Warnings: {assembly_structural_report.warning_count}")
        
        if not assembly_structural_report.passed:
            print("\n[ERROR] Assembly structural validation FAILED")
            for issue in assembly_structural_report.issues:
                if issue.severity == "ERROR":
                    print(f"  - {issue.category}: {issue.reason}")
            sys.exit(1)
            
    except Exception as e:
        print_stage_error("Assembly", str(e))
    
    # ========================================================================
    # STAGE 6: RENDERING
    # ========================================================================
    print_stage_header("6. RENDERING")
    
    try:
        renderer = MarkdownRenderer(verbose=False)
        rendered_doc = renderer.render(assembled_doc)
        
        # Save manifest
        with open(RENDER_MANIFEST_JSON, 'w', encoding='utf-8') as f:
            json.dump(rendered_doc.manifest.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save markdown
        RENDERED_MD.write_text(rendered_doc.content, encoding='utf-8')
        
        print_stage_success("Rendering", 
                          f"{rendered_doc.manifest.total_items} items, "
                          f"{rendered_doc.manifest.markdown_length} chars, "
                          f"{rendered_doc.manifest.total_lines} lines")
        
        # STRUCTURAL EVALUATION: Markdown
        print("\n  → Running structural evaluation on markdown...")
        markdown_structural_report = structural_evaluator.evaluate(
            markdown_output=rendered_doc.content,
            assembly_doc=assembled_doc
        )
        
        # Save structural evaluation report
        with open(STRUCTURAL_EVAL_MARKDOWN_JSON, 'w', encoding='utf-8') as f:
            json.dump(markdown_structural_report.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"  → Structural evaluation: {'PASSED' if markdown_structural_report.passed else 'FAILED'}")
        print(f"     Errors: {markdown_structural_report.error_count}, Warnings: {markdown_structural_report.warning_count}")
        
        if not markdown_structural_report.passed:
            print("\n[ERROR] Markdown structural validation FAILED")
            for issue in markdown_structural_report.issues:
                if issue.severity == "ERROR":
                    print(f"  - {issue.category}: {issue.reason}")
            sys.exit(1)
            
    except Exception as e:
        print_stage_error("Rendering", str(e))
    
    # ========================================================================
    # STAGE 7: EVALUATION (Structural + Semantic)
    # ========================================================================
    print_stage_header("7. EVALUATION")
    
    try:
        # Part A: Structural Evaluation
        print("Part A: Structural Evaluation (coverage, provenance, representations)")
        evaluator = FaithfulnessEvaluator(verbose=True)
        structural_result = evaluator.evaluate(
            source_doc,
            knowledge_doc,
            analyzed_doc,
            represented_doc,
            assembled_doc,
            rendered_doc.manifest
        )
        
        print(f"\nStructural Status: {structural_result.status.status.upper()}")
        print(f"  Errors: {structural_result.status.total_errors}")
        print(f"  Warnings: {structural_result.status.total_warnings}")
        
        # Part B: Semantic Verification
        print("\nPart B: Semantic Verification (factual correctness)")
        semantic_verifier = DeterministicSemanticVerifier(verbose=True)
        semantic_result = semantic_verifier.verify(knowledge_doc, source_doc)
        
        # Integrate semantic results into structural report
        structural_result.semantic_verification_report = semantic_result.model_dump()
        structural_result.semantic_faithfulness_verified = semantic_result.semantic_faithfulness_verified
        
        if semantic_result.semantic_faithfulness_verified:
            structural_result.semantic_faithfulness_note = (
                f"Semantic verification PASSED: {semantic_result.claims_supported}/"
                f"{semantic_result.total_claims_verified} claims supported "
                f"({semantic_result.support_rate:.1%}), 0 contradicted"
            )
        else:
            structural_result.semantic_faithfulness_note = (
                f"Semantic verification NOT verified: {semantic_result.claims_supported}/"
                f"{semantic_result.total_claims_verified} claims supported "
                f"({semantic_result.support_rate:.1%}), "
                f"{semantic_result.claims_contradicted} contradicted, "
                f"{semantic_result.claims_unsupported} unsupported, "
                f"{semantic_result.claims_inconclusive} inconclusive"
            )
        
        # Save both reports
        with open(EVALUATION_JSON, 'w', encoding='utf-8') as f:
            json.dump(structural_result.model_dump(), f, indent=2, ensure_ascii=False)
        
        with open(SEMANTIC_VERIFICATION_JSON, 'w', encoding='utf-8') as f:
            json.dump(semantic_result.model_dump(), f, indent=2, ensure_ascii=False)
        
        print_stage_success("Evaluation", 
                          f"Structural: {structural_result.status.status.upper()}, "
                          f"Semantic: {'VERIFIED' if semantic_result.semantic_faithfulness_verified else 'NOT VERIFIED'}")
        
        # Print evaluation summary
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print("\nSTRUCTURAL EVALUATION:")
        print(f"  Status:             {structural_result.status.status.upper()}")
        print(f"  Errors:             {structural_result.status.total_errors}")
        print(f"  Warnings:           {structural_result.status.total_warnings}")
        print(f"  Pipeline complete:  {structural_result.status.pipeline_complete}")
        
        print("\nSEMANTIC VERIFICATION:")
        print(f"  Total claims:       {semantic_result.total_claims_verified}")
        print(f"  Supported:          {semantic_result.claims_supported} ({semantic_result.support_rate:.1%})")
        print(f"  Contradicted:       {semantic_result.claims_contradicted}")
        print(f"  Unsupported:        {semantic_result.claims_unsupported}")
        print(f"  Inconclusive:       {semantic_result.claims_inconclusive}")
        print(f"  Faithfulness:       {'VERIFIED' if semantic_result.semantic_faithfulness_verified else 'NOT VERIFIED'}")
        
        print("=" * 80)
        
        # Determine exit code based on BOTH evaluations
        if structural_result.status.status in ["fail", "incomplete"]:
            print("\n[ERROR] Pipeline completed with STRUCTURAL ERRORS")
            sys.exit(1)
        elif semantic_result.claims_contradicted > 0:
            print(f"\n[ERROR] Pipeline completed with {semantic_result.claims_contradicted} CONTRADICTED claims")
            print("  Contradictions indicate factual errors in extraction")
            sys.exit(1)
        elif structural_result.status.status == "warning":
            print("\n[WARNING] Pipeline completed with WARNINGS")
        elif not semantic_result.semantic_faithfulness_verified:
            print("\n[WARNING] Pipeline completed - structural PASS, semantic NOT VERIFIED")
            print(f"  Support rate {semantic_result.support_rate:.1%} below 80% threshold")
            print(f"  Review {semantic_result.claims_inconclusive} INCONCLUSIVE and {semantic_result.claims_unsupported} UNSUPPORTED claims")
        else:
            print("\n[OK] Pipeline completed SUCCESSFULLY")
            print("  Structural validation PASSED and semantic faithfulness VERIFIED")
        
        return 0
        
    except Exception as e:
        print_stage_error("Evaluation", str(e))


if __name__ == "__main__":
    sys.exit(main())
