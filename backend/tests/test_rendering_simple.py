"""
Simplified rendering tests that work with actual models.
"""

import json
from pathlib import Path
import pytest
from app.rendering.renderer import MarkdownRenderer
from app.assembly.models import AssembledNotesDocument


def test_render_assembled_notes_json():
    """Load and render the real assembled_notes.json file."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Validate output
    assert result.content is not None
    assert len(result.content) > 0
    assert result.content.startswith("#")
    
    # Validate manifest
    assert result.manifest.total_items > 0
    assert len(result.manifest.items) == result.manifest.total_items
    
    # Check provenance
    for item in result.manifest.items:
        assert item.knowledge_id is not None
        assert len(item.source_unit_ids) > 0
        assert item.start_line >= 1
        assert item.end_line >= item.start_line
        assert item.format_used is not None
    
    # Print summary
    print(f"\n✓ Rendered {result.manifest.total_items} items")
    print(f"✓ Markdown length: {len(result.content)} chars")
    print(f"✓ Warnings: {len(result.manifest.warnings)}")


def test_deterministic_rendering():
    """Verify that rendering the same document multiple times produces identical output."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    
    # Render 3 times
    result1 = renderer.render(doc)
    result2 = renderer.render(doc)
    result3 = renderer.render(doc)
    
    # All should be identical
    assert result1.content == result2.content
    assert result2.content == result3.content
    assert result1.manifest.total_items == result2.manifest.total_items
    
    print("\n✓ Three consecutive renders produced identical output")


def test_manifest_serialization():
    """Test that manifest can be serialized to JSON."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Should serialize without error
    manifest_json = result.manifest.model_dump_json(indent=2)
    assert len(manifest_json) > 0
    
    # Should be valid JSON
    manifest_data = json.loads(manifest_json)
    assert manifest_data['total_items'] == result.manifest.total_items
    
    print(f"\n✓ Manifest serialized to {len(manifest_json)} chars of JSON")


def test_all_items_have_provenance():
    """Verify every rendered item has provenance tracking."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Check every item
    for item in result.manifest.items:
        # Has knowledge ID
        assert item.knowledge_id is not None
        assert len(item.knowledge_id) > 0
        
        # Has source units
        assert len(item.source_unit_ids) > 0
        
        # Has line numbers
        assert item.start_line > 0
        assert item.end_line >= item.start_line
        
        # Has format
        assert item.format_used is not None
        
        # Has status
        assert item.status in ["complete", "partial", "fallback"]
    
    print(f"\n✓ All {len(result.manifest.items)} items have complete provenance")


def test_markdown_contains_provenance_annotations():
    """Verify markdown contains inline provenance annotations."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Should have Knowledge ID annotations
    assert "Knowledge ID:" in result.content
    assert "Sources:" in result.content
    
    # Count annotations (should match item count roughly)
    annotation_count = result.content.count("Knowledge ID:")
    assert annotation_count > 0
    
    print(f"\n✓ Markdown contains {annotation_count} provenance annotations")


def test_output_file_creation(tmp_path):
    """Test saving rendered output to files."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Save markdown
    md_path = tmp_path / "rendered_notes.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(result.content)
    
    # Save manifest
    manifest_path = tmp_path / "render_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(result.manifest.model_dump_json(indent=2))
    
    # Verify files exist
    assert md_path.exists()
    assert manifest_path.exists()
    assert md_path.stat().st_size > 0
    assert manifest_path.stat().st_size > 0
    
    print(f"\n✓ Saved markdown ({md_path.stat().st_size} bytes) and manifest ({manifest_path.stat().st_size} bytes)")



def test_save_rendered_markdown_and_manifest():
    """Test saving rendered markdown and manifest to files."""
    input_path = Path("data/output/assembled_notes.json")
    if not input_path.exists():
        pytest.skip("assembled_notes.json not found")
    
    # Load and render
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    doc = AssembledNotesDocument(**data)
    renderer = MarkdownRenderer()
    result = renderer.render(doc)
    
    # Save markdown
    md_path = Path("data/output/test_rendered.md")
    md_path.write_text(result.content, encoding='utf-8')
    
    # Verify markdown file
    assert md_path.exists()
    saved_content = md_path.read_text(encoding='utf-8')
    assert saved_content == result.content
    assert len(saved_content) > 0
    assert saved_content.startswith("#")  # Markdown header
    
    # Save manifest
    manifest_path = Path("data/output/test_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(result.manifest.model_dump(), f, indent=2, ensure_ascii=False)
    
    # Verify manifest file
    assert manifest_path.exists()
    with open(manifest_path, 'r', encoding='utf-8') as f:
        saved_manifest = json.load(f)
    
    assert saved_manifest['document_id'] == result.manifest.document_id
    assert saved_manifest['total_items'] == result.manifest.total_items
    assert len(saved_manifest['items']) == result.manifest.total_items
    
    # Verify manifest items have required fields
    for item in saved_manifest['items']:
        assert 'knowledge_id' in item
        assert 'source_unit_ids' in item
        assert 'start_line' in item
        assert 'end_line' in item
        assert 'status' in item
        assert 'format_used' in item
    
    # Clean up test files
    md_path.unlink()
    manifest_path.unlink()
    
    print(f"\n✓ Saved and verified markdown ({len(saved_content)} chars)")
    print(f"✓ Saved and verified manifest ({result.manifest.total_items} items)")
