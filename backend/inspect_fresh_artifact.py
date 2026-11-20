"""Inspect fresh ingestion artifact."""
import json
from pathlib import Path

artifact_path = Path("data/output/fresh_ingestion_test/source_units.json")

print(f"Artifact exists: {artifact_path.exists()}")
print(f"Size: {artifact_path.stat().st_size:,} bytes")
print(f"Created: {artifact_path.stat().st_ctime}")

with open(artifact_path) as f:
    data = json.load(f)

print(f"\nDocument ID: {data['document_id']}")
print(f"Filename: {data['filename']}")
print(f"Page count: {data['page_count']}")
print(f"Source units: {len(data['source_units'])}")

# Check IDs
ids = [u['source_id'] for u in data['source_units']]
print(f"\nFirst 3 IDs: {ids[:3]}")
print(f"Last 3 IDs: {ids[-3:]}")
print(f"Duplicate IDs: {len(ids) - len(set(ids))}")

# Check for empty/malformed units
empty_text = sum(1 for u in data['source_units'] if u.get('text') is None or u['text'] == '')
print(f"\nUnits with empty/no text: {empty_text}")
print(f"Units with text: {len(data['source_units']) - empty_text}")

# Sample text from S0022 (key unit for CON_0001)
s0022 = [u for u in data['source_units'] if u['source_id'] == 'S0022']
if s0022:
    text = s0022[0]['text']
    print(f"\nS0022 text preview (first 150 chars):")
    print(f"{text[:150]}...")
    print(f"\nS0022 full length: {len(text)} chars")
