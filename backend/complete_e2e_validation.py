#!/usr/bin/env python3
"""
Complete End-to-End Validation with Structural Evaluation.

Full pipeline execution:
1. Load source document
2. Extract knowledge (use existing + recovered data)
3. Apply provenance corrections
4. Semantic verification
5. Representation selection + structural validation
6. Note assembly + structural validation
7. Markdown rendering + structural validation
8. Generate final report
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.evaluation.structural_evaluator import StructuralEvaluator
from app.analysis.analyzer import ContentAnalyzer
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer


def print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_header("COMPLETE END-TO-END VALIDATION")
    
    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("data/output/complete_e2e_validation") / f"validation_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nTimestamp: {timestamp}")
    print(f"Output directory: {output_dir}")
    
    # =======================================================================
    # STEP 1: Load Source Document
    # =======================================================================
    print_header("STEP 1: Load Source Document")
    
    source_path = Path("data/output/java_transcript_validation/source_units_20261030_185308.json")
    
    if not source_path.exists():
        print(f"❌ Error: Source file not found: {source_path}")
        return 1
    
    print(f"Loading: {source_path}")
    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    source_doc = SourceDocument(**source_data)
    print(f"✓ Loaded {len(source_doc.source_units)} source units")
    
    # Save source reference
    with open(output_dir / "source_units.json", 'w', encoding='utf-8') as f:
        json.dump(source_data, f, indent=2, ensure_ascii=False)
    
    # =======================================================================
    # STEP 2: Load and Merge Knowledge
    # =======================================================================
    print_header("STEP 2: Load Knowledge Extraction")
    
    # Load base extraction
    knowledge_path = Path("data/output/java_transcript_validation/knowledge_20261030_185308.json")
    
    if not knowledge_path.exists():
        print(f"❌ Error: Knowledge file not found: {knowledge_path}")
        return 1
    
    print(f"Loading base extraction: {knowledge_path}")
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
    
    knowledge_doc = KnowledgeDocument(**knowledge_data)
    
    initial_counts = {
        'concepts': len(knowledge_doc.concepts),
        'definitions': len(knowledge_doc.definitions),
        'examples': len(knowledge_doc.examples),
        'facts': len(knowledge_doc.facts),
        'total': knowledge_doc.total_items
    }
    
    print(f"✓ Base extraction loaded:")
    print(f"  - Concepts: {initial_counts['concepts']}")
    print(f"  - Definitions: {initial_counts['definitions']}")
    print(f"  - Examples: {initial_counts['examples']}")
    print(f"  - Facts: {initial_counts['facts']}")
    print(f"  - Total: {initial_counts['total']}")
    
    # Merge recovered T0016 data
    t0016_path = Path("data/output/java_transcript_validation/validation_20261101_143618/recovered_T0016_20261101_155351.json")
    
    if t0016_path.exists():
        print(f"\nMerging recovered T0016 data: {t0016_path}")
        with open(t0016_path, 'r', encoding='utf-8') as f:
            t0016_data = json.load(f)
        
        # Add recovered items to knowledge doc
        for concept in t0016_data.get('concepts', []):
            knowledge_doc.concepts.append(type(knowledge_doc.concepts[0])(**concept))
        for definition in t0016_data.get('definitions', []):
            knowledge_doc.definitions.append(type(knowledge_doc.definitions[0])(**definition) if knowledge_doc.definitions else None)
        for example in t0016_data.get('examples', []):
            knowledge_doc.examples.append(type(knowledge_doc.examples[0])(**example))
        
        # Update total
        knowledge_doc.total_items = len(knowledge_doc.get_all_items())
        
        print(f"✓ Merged T0016 items (added {knowledge_doc.total_items - initial_counts['total']} items)")
    else:
        print(f"⚠ Warning: T0016 recovery file not found: {t0016_path}")
    
    # =======================================================================
    # STEP 3: Apply Provenance Corrections
    # =======================================================================
    print_header("STEP 3: Apply Provenance Corrections")
    
    corrections_applied = 0
    
    # Correction 1: EXP_0303 - Add T0033
    for exp in knowledge_doc.explanations:
        if exp.knowledge_id == 'EXP_0303':
            if 'T0033' not in exp.source_unit_ids:
                old_sources = exp.source_unit_ids.copy()
                exp.source_unit_ids.append('T0033')
                exp.source_unit_ids.sort()
                print(f"✓ EXP_0303: {old_sources} → {exp.source_unit_ids}")
                corrections_applied += 1
            else:
                print(f"  EXP_0303: Already corrected")
    
    # Correction 2: EXM_0215 - Change T0022 to T0024
    for exm in knowledge_doc.examples:
        if exm.knowledge_id == 'EXM_0215':
            if 'T0022' in exm.source_unit_ids:
                old_sources = exm.source_unit_ids.copy()
                exm.source_unit_ids = ['T0024' if sid == 'T0022' else sid 
                                        for sid in exm.source_unit_ids]
                print(f"✓ EXM_0215: {old_sources} → {exm.source_unit_ids}")
                corrections_applied += 1
            else:
                print(f"  EXM_0215: Already corrected or not found")
    
    print(f"\n✓ Applied {corrections_applied} provenance corrections")
    
    # Save corrected knowledge
    with open(output_dir / "knowledge_corrected.json", 'w', encoding='utf-8') as f:
        json.dump(knowledge_doc.dict(), f, indent=2, ensure_ascii=False)
    
    # =======================================================================
    # STEP 4: Semantic Verification
    # =======================================================================
    print_header("STEP 4: Semantic Verification")
    
    print("Running semantic verification...")
    verifier = DeterministicSemanticVerifier()
    verification_results = verifier.verify(knowledge_doc, source_doc)
    
    supported = sum(1 for v in verification_results.claim_verifications 
                    if v.verification_status.status == "SUPPORTED")
    unsupported = sum(1 for v in verification_results.claim_verifications 
                      if v.verification_status.status == "UNSUPPORTED")
    contradicted = sum(1 for v in verification_results.claim_verifications 
                       if v.verification_status.status == "CONTRADICTED")
    total = len(verification_results.claim_verifications)
    
    print(f"\n✓ Semantic verification complete:")
    print(f"  - Total claims: {total}")
    print(f"  - SUPPORTED: {supported} ({supported/total*100:.1f}%)")
    print(f"  - UNSUPPORTED: {unsupported} ({unsupported/total*100:.1f}%)")
    print(f"  - CONTRADICTED: {contradicted} ({contradicted/total*100:.1f}%)")
    
    with open(output_dir / "semantic_verification.json", 'w', encoding='utf-8') as f:
        json.dump(verification_results.dict(), f, indent=2, ensure_ascii=False)
    
    # =======================================================================
    # STEP 5: Analysis
    # =======================================================================
    print_header("STEP 5: Content Analysis")
    
    print("Running content analysis...")
    analyzer = ContentAnalyzer()
    analyzed_doc = analyzer.analyze(knowledge_doc)
    
    print(f"✓ Analysis complete: {len(analyzed_doc.analyzed_items)} items analyzed")
    
    with open(output_dir / "analyzed_knowledge.json", 'w', encoding='utf-8') as f:
        json.dump(analyzed_doc.dict(), f, indent=2, ensure_ascii=False)
    
    # =======================================================================
    # STEP 6: Representation Selection + Structural Validation
    # =======================================================================
    print_header("STEP 6: Representation Selection")
    
    print("Selecting representations...")
    selector = RepresentationSelector(verbose=False)
    represented_doc = selector.select(analyzed_doc)
    
    print(f"✓ Representation selection complete: {len(represented_doc.representations)} formats selected")
    
    with open(output_dir / "representations.json", 'w', encoding='utf-8') as f:
        json.dump(represented_doc.dict(), f, indent=2, ensure_ascii=False)
    
    # STRUCTURAL VALIDATION: Representations
    print("\n→ Running structural validation on representations...")
    structural_evaluator = StructuralEvaluator(verbose=False)
    repr_structural_report = structural_evaluator.evaluate(
        representation_doc=represented_doc,
        knowledge_doc=knowledge_doc
    )
    
    with open(output_dir / "structural_eval_representation.json", 'w', encoding='utf-8') as f:
        json.dump(repr_structural_report.dict(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structural validation: {'PASSED' if repr_structural_report.passed else 'FAILED'}")
    print(f"  Errors: {repr_structural_report.error_count}, Warnings: {repr_structural_report.warning_count}")
    
    if not repr_structural_report.passed:
        print("\n❌ Representation structural validation FAILED:")
        for issue in repr_structural_report.issues:
            if issue.severity == "ERROR":
                print(f"  - {issue.category}: {issue.reason}")
        return 1
    
    # =======================================================================
    # STEP 7: Note Assembly + Structural Validation
    # =======================================================================
    print_header("STEP 7: Note Assembly")
    
    print("Assembling notes...")
    assembler = NoteAssembler()
    assembled_doc = assembler.assemble(represented_doc)
    
    print(f"✓ Assembly complete: {assembled_doc.statistics.total_items} items in {assembled_doc.statistics.total_sections} sections")
    
    with open(output_dir / "assembled_notes.json", 'w', encoding='utf-8') as f:
        json.dump(assembled_doc.dict(), f, indent=2, ensure_ascii=False)
    
    # STRUCTURAL VALIDATION: Assembly
    print("\n→ Running structural validation on assembly...")
    assembly_structural_report = structural_evaluator.evaluate(
        assembly_doc=assembled_doc,
        representation_doc=represented_doc
    )
    
    with open(output_dir / "structural_eval_assembly.json", 'w', encoding='utf-8') as f:
        json.dump(assembly_structural_report.dict(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structural validation: {'PASSED' if assembly_structural_report.passed else 'FAILED'}")
    print(f"  Errors: {assembly_structural_report.error_count}, Warnings: {assembly_structural_report.warning_count}")
    
    if not assembly_structural_report.passed:
        print("\n❌ Assembly structural validation FAILED:")
        for issue in assembly_structural_report.issues:
            if issue.severity == "ERROR":
                print(f"  - {issue.category}: {issue.reason}")
        return 1
    
    # =======================================================================
    # STEP 8: Markdown Rendering + Structural Validation
    # =======================================================================
    print_header("STEP 8: Markdown Rendering")
    
    print("Rendering markdown...")
    renderer = MarkdownRenderer(verbose=False)
    rendered_doc = renderer.render(assembled_doc)
    
    print(f"✓ Rendering complete:")
    print(f"  - Items: {rendered_doc.manifest.total_items}")
    print(f"  - Length: {rendered_doc.manifest.markdown_length} chars")
    print(f"  - Lines: {rendered_doc.manifest.total_lines}")
    
    with open(output_dir / "rendered_notes.md", 'w', encoding='utf-8') as f:
        f.write(rendered_doc.content)
    
    with open(output_dir / "render_manifest.json", 'w', encoding='utf-8') as f:
        json.dump(rendered_doc.manifest.dict(), f, indent=2, ensure_ascii=False)
    
    # STRUCTURAL VALIDATION: Markdown
    print("\n→ Running structural validation on markdown...")
    markdown_structural_report = structural_evaluator.evaluate(
        markdown_output=rendered_doc.content,
        assembly_doc=assembled_doc
    )
    
    with open(output_dir / "structural_eval_markdown.json", 'w', encoding='utf-8') as f:
        json.dump(markdown_structural_report.dict(), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Structural validation: {'PASSED' if markdown_structural_report.passed else 'FAILED'}")
    print(f"  Errors: {markdown_structural_report.error_count}, Warnings: {markdown_structural_report.warning_count}")
    
    if not markdown_structural_report.passed:
        print("\n❌ Markdown structural validation FAILED:")
        for issue in markdown_structural_report.issues:
            if issue.severity == "ERROR":
                print(f"  - {issue.category}: {issue.reason}")
        return 1
    
    # =======================================================================
    # STEP 9: Generate Final Report
    # =======================================================================
    print_header("STEP 9: Final Report")
    
    # Calculate source coverage
    all_source_ids = {unit.source_id for unit in source_doc.source_units}
    referenced_source_ids = set()
    for item in knowledge_doc.get_all_items():
        referenced_source_ids.update(item.source_unit_ids)
    
    coverage = len(referenced_source_ids) / len(all_source_ids) * 100
    missing_sources = all_source_ids - referenced_source_ids
    
    final_report = {
        'timestamp': timestamp,
        'output_directory': str(output_dir),
        'pipeline_status': 'SUCCESS',
        
        'extraction': {
            'total_items': knowledge_doc.total_items,
            'concepts': len(knowledge_doc.concepts),
            'definitions': len(knowledge_doc.definitions),
            'examples': len(knowledge_doc.examples),
            'facts': len(knowledge_doc.facts),
            'formulas': len(knowledge_doc.formulas),
            'procedures': len(knowledge_doc.procedures),
            'explanations': len(knowledge_doc.explanations),
            'relationships': len(knowledge_doc.relationships),
        },
        
        'source_coverage': {
            'total_source_units': len(all_source_ids),
            'referenced_units': len(referenced_source_ids),
            'coverage_percentage': round(coverage, 2),
            'missing_units': sorted(list(missing_sources))
        },
        
        'provenance_corrections': {
            'corrections_applied': corrections_applied,
            'EXP_0303': 'Added T0033 to source_unit_ids',
            'EXM_0215': 'Changed T0022 to T0024'
        },
        
        'semantic_verification': {
            'total_claims': total,
            'supported': supported,
            'unsupported': unsupported,
            'contradicted': contradicted,
            'support_rate': round(supported/total*100, 1)
        },
        
        'structural_validation': {
            'representation': {
                'passed': repr_structural_report.passed,
                'errors': repr_structural_report.error_count,
                'warnings': repr_structural_report.warning_count
            },
            'assembly': {
                'passed': assembly_structural_report.passed,
                'errors': assembly_structural_report.error_count,
                'warnings': assembly_structural_report.warning_count
            },
            'markdown': {
                'passed': markdown_structural_report.passed,
                'errors': markdown_structural_report.error_count,
                'warnings': markdown_structural_report.warning_count
            }
        },
        
        'artifacts': {
            'source': str(output_dir / "source_units.json"),
            'knowledge': str(output_dir / "knowledge_corrected.json"),
            'analyzed': str(output_dir / "analyzed_knowledge.json"),
            'representations': str(output_dir / "representations.json"),
            'assembly': str(output_dir / "assembled_notes.json"),
            'markdown': str(output_dir / "rendered_notes.md"),
            'semantic_verification': str(output_dir / "semantic_verification.json"),
            'structural_eval_representation': str(output_dir / "structural_eval_representation.json"),
            'structural_eval_assembly': str(output_dir / "structural_eval_assembly.json"),
            'structural_eval_markdown': str(output_dir / "structural_eval_markdown.json")
        }
    }
    
    with open(output_dir / "final_report.json", 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print("\n✓ Final report generated")
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"\n✓ Pipeline Status: SUCCESS")
    print(f"\nExtraction: {knowledge_doc.total_items} items")
    print(f"Source Coverage: {coverage:.1f}% ({len(referenced_source_ids)}/{len(all_source_ids)} units)")
    print(f"Semantic Support: {supported/total*100:.1f}% ({supported}/{total})")
    print(f"Contradictions: {contradicted}")
    print(f"\nStructural Validation:")
    print(f"  - Representation: {'PASSED' if repr_structural_report.passed else 'FAILED'}")
    print(f"  - Assembly: {'PASSED' if assembly_structural_report.passed else 'FAILED'}")
    print(f"  - Markdown: {'PASSED' if markdown_structural_report.passed else 'FAILED'}")
    print(f"\nOutput: {output_dir}")
    print(f"{'='*80}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
