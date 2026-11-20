"""Inspect the failed chunk 002 from full document validation"""
import json
from pathlib import Path

print("=" * 80)
print("FAILED CHUNK INSPECTION - full_document_CHUNK_002")
print("=" * 80)

# Load source units
source_path = Path('data/output/source_units.json')
if not source_path.exists():
    print("ERROR: source_units.json not found")
    exit(1)

data = json.loads(source_path.read_text())
units = data.get('source_units', [])
print(f"\nTotal source units available: {len(units)}")

# Find units in pages 6-9 (chunk 002 range based on validation output)
chunk_002_units = [u for u in units if 6 <= u.get('page_num', 0) <= 9]
print(f"Units in pages 6-9: {len(chunk_002_units)}")

# Get sections
sections = {}
for u in chunk_002_units:
    section = u.get('section_heading', '(none)')
    sections[section] = sections.get(section, 0) + 1

print("\nSection breakdown:")
for section, count in sorted(sections.items()):
    print(f"  {section}: {count} units")

# Calculate text length
total_chars = sum(len(u.get('text', '')) for u in chunk_002_units)
print(f"\nTotal characters in pages 6-9: {total_chars:,}")
print(f"Estimated tokens (chars/4): ~{total_chars // 4:,}")

# Show first few unit IDs
unit_ids = [u.get('source_id', 'unknown') for u in chunk_002_units[:10]]
print(f"\nFirst 10 unit IDs: {unit_ids}")

# Load extraction details
extract_path = Path('data/output/full_document_109_units/extraction_chunk_details.json')
if extract_path.exists():
    extract_data = json.loads(extract_path.read_text())
    chunk_002_attempts = [a for a in extract_data['attempts_per_chunk'] 
                          if a['chunk_id'] == 'full_document_CHUNK_002']
    
    print("\n" + "=" * 80)
    print("EXTRACTION ATTEMPTS FOR CHUNK 002")
    print("=" * 80)
    
    for attempt in chunk_002_attempts:
        print(f"\nAttempt {attempt['attempt']}:")
        print(f"  Success: {attempt['success']}")
        print(f"  Items extracted: {attempt['items_extracted']}")
        print(f"  Error: {attempt['error']}")
else:
    print("\nWARNING: extraction_chunk_details.json not found")

# Load knowledge document to see what was extracted from other chunks
knowledge_path = Path('data/output/full_document_109_units/knowledge_document.json')
if knowledge_path.exists():
    knowledge_data = json.loads(knowledge_path.read_text())
    items = knowledge_data.get('concepts', []) + \
            knowledge_data.get('definitions', []) + \
            knowledge_data.get('explanations', []) + \
            knowledge_data.get('examples', []) + \
            knowledge_data.get('facts', []) + \
            knowledge_data.get('formulas', []) + \
            knowledge_data.get('procedures', []) + \
            knowledge_data.get('relationships', [])
    
    # Find items from pages 6-9
    chunk_002_source_ids = set(u.get('source_id') for u in chunk_002_units)
    missing_items = []
    for item in items:
        item_source_ids = set(item.get('source_unit_ids', []))
        if item_source_ids & chunk_002_source_ids:
            missing_items.append(item)
    
    print(f"\n" + "=" * 80)
    print(f"PARTIAL EXTRACTION FROM PAGES 6-9")
    print("=" * 80)
    print(f"Items referencing pages 6-9 source IDs: {len(missing_items)}")
    print("(Note: These may be from successful chunks that overlap with pages 6-9)")
