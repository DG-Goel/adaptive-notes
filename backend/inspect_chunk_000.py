"""Inspect CHUNK_000 content"""
import json
from pathlib import Path

# Load source units
source_path = Path('data/output/source_units.json')
source_data = json.loads(source_path.read_text())
units = source_data.get('source_units', [])

print("=" * 80)
print("CHUNK_000 INSPECTION")
print("=" * 80)

# Find CHUNK_000 source units
# Based on chunking logic, CHUNK_000 should be units with no/empty section
first_section_units = []
for unit in units:
    section = unit.get('section')
    if section is None or not section or section == '(none)':
        first_section_units.append(unit)

print(f"\nFound {len(first_section_units)} units with no section")
print()

# Show first 5
for i, unit in enumerate(first_section_units[:10]):
    print(f"Unit {i+1}: {unit.get('source_id')}")
    print(f"  Page: {unit.get('page')}")
    print(f"  Type: {unit.get('type')}")
    print(f"  Content role: {unit.get('content_role')}")
    text = unit.get('text')
    if text:
        preview = text[:150].replace('\n', ' ')
        print(f"  Text ({len(text)} chars): {preview}...")
    else:
        print(f"  Text: None/empty")
    print()

# Calculate total chars
total_chars = sum(len(unit.get('text') or '') for unit in first_section_units)
print(f"Total characters in no-section units: {total_chars:,}")
print(f"Estimated tokens: ~{total_chars // 4}")
