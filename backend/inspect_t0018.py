import json

with open('data/output/complete_e2e_validation/validation_20261101_174430/source_units.json', encoding='utf-8') as f:
    data = json.load(f)
    
print(f"Keys in JSON: {list(data.keys())}")

if 'source_units' in data:
    units = data['source_units']
elif isinstance(data, list):
    units = data
else:
    print(f"Unexpected structure: {type(data)}")
    units = []
    
t18 = [u for u in units if u.get('source_id') == 'T0018' or u.get('unit_id') == 'T0018'][0]

print(f"\nT0018 Details:")
print(f"Text length: {len(t18['text'])} chars")
print(f"Word count: {len(t18['text'].split())}")
print(f"\nFirst 800 chars:")
print(t18['text'][:800])
print(f"\n\nLast 800 chars:")
print(t18['text'][-800:])
