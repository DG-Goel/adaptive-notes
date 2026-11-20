"""Inspect failed chunk 002 details"""
import json
from pathlib import Path

print("=" * 80)
print("CHUNK 002 DETAILED INSPECTION")
print("=" * 80)

# Load knowledge document to see extraction metadata
knowledge_path = Path('data/output/full_document_109_units/knowledge_document.json')
if not knowledge_path.exists():
    print("ERROR: knowledge_document.json not found")
    exit(1)

knowledge_data = json.loads(knowledge_path.read_text())
metadata = knowledge_data.get('extraction_metadata', {})

print(f"\nExtraction Metadata:")
print(f"  Total chunks: {metadata.get('total_chunks')}")
print(f"  Successful: {metadata.get('successful_chunks')}")
print(f"  Failed: {metadata.get('failed_chunks')}")
print(f"  Completeness: {metadata.get('completeness', 0)*100:.1f}%")

# Find chunk 002 attempts
attempts = metadata.get('chunk_attempts', [])
chunk_002_attempts = [a for a in attempts if a['chunk_id'] == 'full_document_CHUNK_002']

print(f"\n" + "=" * 80)
print(f"CHUNK 002 EXTRACTION ATTEMPTS")
print("=" * 80)

for attempt in chunk_002_attempts:
    print(f"\nAttempt {attempt['attempt']}:")
    print(f"  Success: {attempt['success']}")
    print(f"  Items extracted: {attempt['items_extracted']}")
    print(f"  Error: {attempt.get('error', 'None')}")

# Now we need to reconstruct what chunk 002 contained
# Load source units to understand the document structure
source_path = Path('data/output/source_units.json')
if not source_path.exists():
    print("\nERROR: source_units.json not found")
    exit(1)

source_data = json.loads(source_path.read_text())
all_units = source_data.get('source_units', [])

print(f"\n" + "=" * 80)
print(f"SOURCE DOCUMENT STRUCTURE")
print("=" * 80)
print(f"Total source units: {len(all_units)}")

# Group by section to understand chunking
sections = {}
for unit in all_units:
    section = unit.get('section', '(none)')
    if section not in sections:
        sections[section] = []
    sections[section].append(unit)

print(f"\nSections ({len(sections)} total):")
for i, (section, units) in enumerate(sections.items(), 1):
    chars = sum(len(u.get('text') or '') for u in units)
    tokens = chars // 4
    print(f"  {i}. {section}: {len(units)} units, ~{tokens} tokens")

# Chunk 002 is the 3rd chunk (index 2)
# Based on chunking logic: chunks are created by section or size
# Let's identify which section would be chunk 002

print(f"\n" + "=" * 80)
print(f"CHUNK RECONSTRUCTION (max_tokens_per_chunk=2000)")
print("=" * 80)

chunk_num = 0
for section, units in sections.items():
    section_chars = sum(len(u.get('text') or '') for u in units)
    section_tokens = section_chars // 4
    
    # Estimate how many chunks this section would create
    if section_tokens > 2000:
        num_chunks = (section_tokens // 2000) + 1
        print(f"\nChunk {chunk_num}-{chunk_num + num_chunks - 1}: {section}")
        print(f"  Units: {len(units)}, Tokens: ~{section_tokens}")
        print(f"  Would create {num_chunks} chunks")
        
        if chunk_num <= 2 < chunk_num + num_chunks:
            print(f"  >>> CHUNK 002 IS IN THIS SECTION <<<")
            
            # Try to identify the exact units in chunk 002
            # This requires simulating the chunking algorithm
            current_chars = 0
            chunk_start = chunk_num
            current_chunk = chunk_start
            
            for unit in units:
                unit_chars = len(unit.get('text') or '')
                if current_chars + unit_chars > 8000 and current_chars > 0:  # 2000 tokens * 4
                    current_chunk += 1
                    current_chars = 0
                
                if current_chunk == 2:
                    # This unit is in chunk 002
                    if current_chars == 0:
                        print(f"\n  Chunk 002 starts with unit: {unit.get('source_id')}")
                
                current_chars += unit_chars
        
        chunk_num += num_chunks
    else:
        print(f"\nChunk {chunk_num}: {section}")
        print(f"  Units: {len(units)}, Tokens: ~{section_tokens}")
        chunk_num += 1

print(f"\n" + "=" * 80)
print(f"DIAGNOSTIC SAVED RESPONSES")
print("=" * 80)

# Check for saved diagnostic responses
diag_dir = Path('data/diagnostics/failed_responses')
if diag_dir.exists():
    chunk_002_files = list(diag_dir.glob('*CHUNK_002*'))
    if chunk_002_files:
        print(f"\nFound {len(chunk_002_files)} diagnostic files for chunk 002:")
        for f in chunk_002_files:
            print(f"  - {f.name}")
            # Read first few lines
            content = f.read_text()
            lines = content.split('\n')[:15]
            for line in lines:
                print(f"    {line}")
            print(f"    ... (truncated)")
            break
    else:
        print("\nNo diagnostic files found for chunk 002")
else:
    print("\nDiagnostics directory not found")
