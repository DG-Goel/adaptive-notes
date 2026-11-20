"""
Regenerate rendering output (Markdown and manifest) from assembled notes.
"""

import json
from pathlib import Path
from app.assembly.models import AssembledNotesDocument
from app.rendering.renderer import MarkdownRenderer

def main():
    print("=" * 80)
    print("REGENERATE RENDERING OUTPUT")
    print("=" * 80)
    print()
    
    # Load assembled notes
    asm_path = Path('data/output/assembled_notes.json')
    if not asm_path.exists():
        print(f"ERROR: {asm_path} not found")
        return 1
    
    print(f"Loading: {asm_path}")
    asm_doc = AssembledNotesDocument.model_validate_json(
        asm_path.read_text(encoding='utf-8')
    )
    print(f"  Document ID: {asm_doc.document_id}")
    print(f"  Total items: {asm_doc.statistics.total_items}")
    print()
    
    # Render
    print("Rendering markdown...")
    renderer = MarkdownRenderer(verbose=False)
    rendered_doc = renderer.render(asm_doc)
    
    # Save manifest
    manifest_path = Path('data/output/render_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(rendered_doc.manifest.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"✓ Saved manifest: {manifest_path}")
    
    # Save markdown
    md_path = Path('data/output/rendered_notes.md')
    md_path.write_text(rendered_doc.content, encoding='utf-8')
    print(f"✓ Saved markdown: {md_path}")
    
    # Report statistics
    print()
    print("=" * 80)
    print("RENDERING STATISTICS")
    print("=" * 80)
    print(f"Document ID:        {rendered_doc.manifest.document_id}")
    print(f"Markdown length:    {rendered_doc.manifest.markdown_length} characters")
    print(f"Total lines:        {rendered_doc.manifest.total_lines}")
    print(f"Items rendered:     {rendered_doc.manifest.total_items}")
    print(f"  Complete:         {rendered_doc.manifest.items_complete}")
    print(f"  Partial:          {rendered_doc.manifest.items_partial}")
    print(f"  Fallback:         {rendered_doc.manifest.items_fallback}")
    print(f"Warnings:           {len(rendered_doc.manifest.warnings)}")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    exit(main())
