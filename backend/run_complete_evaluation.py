"""
Run complete evaluation: structural + semantic verification.

This script runs both the structural evaluator (coverage, provenance, representations)
and the semantic verifier (factual correctness) on pipeline output.

Usage:
    python run_complete_evaluation.py
"""

import json
from pathlib import Path
from datetime import datetime

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.analysis.characteristics import AnalyzedKnowledgeDocument
from app.representation.models import RepresentationDocument
from app.assembly.models import AssembledNotesDocument
from app.rendering.models import RenderManifest
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier


def load_json(path: Path, model_class):
    """Load JSON file into Pydantic model."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return model_class(**data)


def save_json(data, path: Path):
    """Save Pydantic model or dict to JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        if hasattr(data, 'model_dump'):
            json.dump(data.model_dump(), f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    """Run complete evaluation."""
    
    print_section("COMPLETE EVALUATION: STRUCTURAL + SEMANTIC")
    
    # Define paths
    data_dir = Path("data/output")
    
    paths = {
        "source_units": data_dir / "source_units.json",
        "knowledge_doc": data_dir / "knowledge_document.json",
        "analyzed_doc": data_dir / "analyzed_knowledge.json",
        "represented_doc": data_dir / "representations.json",
        "assembled_doc": data_dir / "assembled_notes.json",
        "render_manifest": data_dir / "render_manifest.json",
        "output": data_dir / "complete_evaluation_report.json"
    }
    
    # Check all files exist
    missing = [name for name, path in paths.items() if name != "output" and not path.exists()]
    if missing:
        print(f"\n✗ Error: Missing files: {', '.join(missing)}")
        print("  Run the pipeline first to generate all artifacts.")
        return False
    
    print("\n✓ All pipeline artifacts found")
    
    # Load documents
    print("\nLoading pipeline artifacts...")
    try:
        source_doc = load_json(paths["source_units"], SourceDocument)
        knowledge_doc = load_json(paths["knowledge_doc"], KnowledgeDocument)
        analyzed_doc = load_json(paths["analyzed_doc"], AnalyzedKnowledgeDocument)
        represented_doc = load_json(paths["represented_doc"], RepresentationDocument)
        assembled_doc = load_json(paths["assembled_doc"], AssembledNotesDocument)
        render_manifest = load_json(paths["render_manifest"], RenderManifest)
        
        print(f"  ✓ Source units: {len(source_doc.source_units)}")
        print(f"  ✓ Knowledge items: {len(knowledge_doc.get_all_items())}")
        print(f"  ✓ Analyzed items: {len(analyzed_doc.analyzed_items)}")
        print(f"  ✓ Representations: {len(represented_doc.representations)}")
        print(f"  ✓ Assembled sections: {len(assembled_doc.sections)}")
        print(f"  ✓ Rendered items: {len(render_manifest.items)}")
    except Exception as e:
        print(f"\n✗ Error loading documents: {e}")
        return False
    
    # Run structural evaluation
    print_section("PHASE 1: STRUCTURAL EVALUATION")
    print("Running FaithfulnessEvaluator...")
    print()
    
    structural_evaluator = FaithfulnessEvaluator(verbose=True)
    structural_report = structural_evaluator.evaluate(
        source_doc,
        knowledge_doc,
        analyzed_doc,
        represented_doc,
        assembled_doc,
        render_manifest
    )
    
    print(f"\nStructural Status: {structural_report.status.status.upper()}")
    print(f"  Errors: {structural_report.status.total_errors}")
    print(f"  Warnings: {structural_report.status.total_warnings}")
    
    # Run semantic verification
    print_section("PHASE 2: SEMANTIC VERIFICATION")
    print("Running DeterministicSemanticVerifier...")
    print()
    
    semantic_verifier = DeterministicSemanticVerifier(verbose=True)
    semantic_report = semantic_verifier.verify(knowledge_doc, source_doc)
    
    # Integrate semantic results into structural report
    structural_report.semantic_verification_report = semantic_report.model_dump()
    structural_report.semantic_faithfulness_verified = semantic_report.semantic_faithfulness_verified
    
    if semantic_report.semantic_faithfulness_verified:
        structural_report.semantic_faithfulness_note = (
            f"Semantic verification PASSED: {semantic_report.claims_supported}/"
            f"{semantic_report.total_claims_verified} claims supported "
            f"({semantic_report.support_rate:.1%}), 0 contradicted"
        )
    else:
        structural_report.semantic_faithfulness_note = (
            f"Semantic verification NOT verified: {semantic_report.claims_supported}/"
            f"{semantic_report.total_claims_verified} claims supported "
            f"({semantic_report.support_rate:.1%}), "
            f"{semantic_report.claims_contradicted} contradicted, "
            f"{semantic_report.claims_unsupported} unsupported, "
            f"{semantic_report.claims_inconclusive} inconclusive"
        )
    
    # Save complete report
    save_json(structural_report, paths["output"])
    print(f"\n✓ Complete evaluation report saved: {paths['output']}")
    
    # Print summary
    print_section("COMPLETE EVALUATION SUMMARY")
    
    print("\nSTRUCTURAL EVALUATION:")
    print(f"  Status: {structural_report.status.status.upper()}")
    print(f"  Coverage (end-to-end): {structural_report.coverage.end_to_end_coverage_ratio:.1%}")
    print(f"  Provenance errors: {structural_report.status.provenance_errors}")
    print(f"  Representation errors: {structural_report.status.representation_errors}")
    print(f"  Content warnings: {structural_report.status.content_warnings}")
    
    print("\nSEMATIC VERIFICATION:")
    print(f"  Total claims: {semantic_report.total_claims_verified}")
    print(f"  ✓ Supported: {semantic_report.claims_supported} ({semantic_report.support_rate:.1%})")
    print(f"  ✗ Contradicted: {semantic_report.claims_contradicted}")
    print(f"  ? Unsupported: {semantic_report.claims_unsupported}")
    print(f"  ~ Inconclusive: {semantic_report.claims_inconclusive}")
    print(f"  ! Insufficient: {semantic_report.claims_insufficient_evidence}")
    
    print("\nOVERALL ASSESSMENT:")
    print(f"  Structural validation: {'PASS' if structural_report.status.status == 'pass' else 'FAIL'}")
    print(f"  Semantic faithfulness: {'VERIFIED' if semantic_report.semantic_faithfulness_verified else 'NOT VERIFIED'}")
    
    if structural_report.status.status == "pass" and semantic_report.semantic_faithfulness_verified:
        print("\n✓ COMPLETE EVALUATION PASSED")
        print("  The pipeline output is structurally valid and semantically faithful.")
        return True
    elif structural_report.status.status == "pass":
        print("\n⚠ STRUCTURAL VALIDATION PASSED, SEMANTIC VERIFICATION INCOMPLETE")
        print("  The pipeline output is structurally valid but semantic faithfulness is not verified.")
        print("  This may indicate paraphrasing or abstractions that require manual review.")
        return False
    else:
        print("\n✗ STRUCTURAL VALIDATION FAILED")
        print("  Fix structural issues before semantic verification is meaningful.")
        return False


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 80)
    exit(0 if success else 1)
