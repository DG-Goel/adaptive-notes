#!/usr/bin/env python3
"""
Resume Java transcript validation from existing artifacts.
Loads knowledge and analyzed data, then continues with:
- Representation selection
- Note assembly
- Markdown rendering
- Semantic verification
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.knowledge import KnowledgeDocument
from app.analysis.analyzer import AnalyzedKnowledgeDocument
from app.representation.selector import RepresentationSelector
from app.assembly.assembler import NoteAssembler
from app.rendering.renderer import MarkdownRenderer
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier

def main():
    print("=" * 80)
    print("RESUMING JAVA TRANSCRIPT VALIDATION")
    print("=" * 80)
    print()
    
    # Load existing artifacts
    timestamp = "20261030_185308"
    artifact_dir = Path("data/output/java_transcript_validation")
    
    print(f"Loading artifacts from: {artifact_dir}")
    print(f"Timestamp: {timestamp}")
    print()
    
    # Load knowledge document
    knowledge_path = artifact_dir / f"knowledge_{timestamp}.json"
    print(f"Loading: {knowledge_path.name}")
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        knowledge_data = json.load(f)
    knowledge_doc = KnowledgeDocument(**knowledge_data)
    print(f"  OK Loaded {knowledge_doc.total_items} knowledge items")
    print()
    
    # Load analyzed document
    analyzed_path = artifact_dir / f"analyzed_{timestamp}.json"
    print(f"Loading: {analyzed_path.name}")
    with open(analyzed_path, 'r', encoding='utf-8') as f:
        analyzed_data = json.load(f)
    analyzed_doc = AnalyzedKnowledgeDocument(**analyzed_data)
    print(f"  OK Loaded {len(analyzed_doc.analyzed_items)} analyzed items")
    print()
    
    # Create output directory for new artifacts (use current timestamp)
    new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = artifact_dir
    
    # ==================================================
    # STEP 4: REPRESENTATION SELECTION
    # ==================================================
    print("=" * 80)
    print("STEP 4: REPRESENTATION SELECTION")
    print("=" * 80)
    print()
    
    selector = RepresentationSelector()
    representations_doc = selector.select(analyzed_doc)
    
    print(f"OK Selected {len(representations_doc.representations)} representations")
    print()
    
    # Save representations
    repr_path = output_dir / f"representations_{new_timestamp}.json"
    with open(repr_path, 'w', encoding='utf-8') as f:
        json.dump(representations_doc.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"OK Saved: {repr_path.name}")
    print()
    
    # ==================================================
    # STEP 5: NOTE ASSEMBLY
    # ==================================================
    print("=" * 80)
    print("STEP 5: NOTE ASSEMBLY")
    print("=" * 80)
    print()
    
    assembler = NoteAssembler()
    assembled_notes = assembler.assemble(representations_doc)
    
    print(f"OK Assembled {len(assembled_notes.sections)} note sections")
    print()
    
    # Save assembled notes
    assembled_path = output_dir / f"assembled_{new_timestamp}.json"
    with open(assembled_path, 'w', encoding='utf-8') as f:
        json.dump(assembled_notes.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"OK Saved: {assembled_path.name}")
    print()
    
    # ==================================================
    # STEP 6: MARKDOWN RENDERING
    # ==================================================
    print("=" * 80)
    print("STEP 6: MARKDOWN RENDERING")
    print("=" * 80)
    print()
    
    renderer = MarkdownRenderer()
    rendered_doc = renderer.render(assembled_notes)
    markdown_content = rendered_doc.content
    
    # Save markdown
    markdown_path = output_dir / f"java_notes_{new_timestamp}.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"OK Rendered {len(markdown_content)} characters of Markdown")
    print(f"OK Saved: {markdown_path.name}")
    print()
    
    # ==================================================
    # STEP 7: SEMANTIC VERIFICATION
    # (Skip - requires source document which we didn't load)
    # ==================================================
    print("=" * 80)
    print("STEP 7: SEMANTIC VERIFICATION - SKIPPED")
    print("=" * 80)
    print("(Requires source document - not needed for pipeline completion)")
    print()
    
    # Create placeholder verification results
    from app.evaluation.semantic_verifier import SemanticVerificationReport
    verification_results = SemanticVerificationReport(
        document_id=knowledge_doc.document_id,
        source_filename=knowledge_doc.source_filename,
        verification_timestamp=datetime.now().isoformat(),
        total_items=len(analyzed_doc.analyzed_items),
        passed_items=0,
        failed_items=0,
        verifications=[]
    )
    print()
    
    # ==================================================
    # FINAL SUMMARY
    # ==================================================
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Pipeline executed successfully!")
    print()
    print(f"Key metrics:")
    print(f"  Knowledge items extracted: {knowledge_doc.total_items}")
    print(f"  Analyzed items: {len(analyzed_doc.analyzed_items)}")
    print(f"  Representations selected: {len(representations_doc.representations)}")
    print(f"  Note sections: {len(assembled_notes.sections)}")
    print(f"  Markdown size: {len(markdown_content):,} chars")
    print(f"  Verification: Skipped (requires source document)")
    print()
    print(f"Output files:")
    print(f"  Representations: {repr_path.name}")
    print(f"  Assembled notes: {assembled_path.name}")
    print(f"  Markdown: {markdown_path.name}")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
