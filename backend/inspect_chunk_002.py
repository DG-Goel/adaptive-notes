"""Inspect chunk 002 content"""
import json
from pathlib import Path

# Load source document
source_path = Path('data/output/full_document_109_units/source_document.json')
source_data = json.loads(source_path.read_text())

# Find chunk 002's source units (pages 6-9, section 'Stop and Think')
units = source_data['source_units']

print('Chunk 002 source units (pages 6-9, section "Stop and Think"):')
print('=' * 80)

chunk_units = []
for unit in units:
    if 6 <= unit['page_num'] <= 9 and 'Stop and Think' in unit.get('section_heading', ''):
        chunk_units.append(unit)

print(f"Found {len(chunk_units)} units in chunk 002")
print()

total_chars = sum(len(u.get('text', '')) for u in chunk_units)
print(f"Total character count: {total_chars:,}")
print(f"Estimated tokens: ~{total_chars // 4:,}")
print()

# Show first few units
for i, unit in enumerate(chunk_units[:5]):
    print(f"Unit {i+1}: {unit['source_id']}, Page {unit['page_num']}")
    print(f"  Section: {unit.get('section_heading', '(none)')}")
    text = unit.get('text', '')
    print(f"  Length: {len(text)} chars")
    if text:
        preview = text[:150].replace('\n', ' ')
        print(f"  Preview: {preview}...")
    print()

if len(chunk_units) > 5:
    print(f"... and {len(chunk_units) - 5} more units")
