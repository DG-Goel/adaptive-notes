#!/usr/bin/env python3
"""Audit unsupported claims from retry1 validation"""
import json
from pathlib import Path

retry1_path = Path("data/output/real_llm_validation_15_20_retry1/semantic_verification.json")

with open(retry1_path) as f:
    data = json.load(f)

print("=" * 80)
print("RETRY 1: NON-SUPPORTED CLAIMS AUDIT")
print("=" * 80)
print(f"Total claims: {data['total_claims_verified']}")
print(f"Supported: {data['claims_supported']}")
print(f"Unsupported: {data['claims_unsupported']}")
print(f"Inconclusive: {data['claims_inconclusive']}")
print()

non_supported = [v for v in data['claim_verifications'] 
                 if v['verification_status']['status'] != 'SUPPORTED']

for i, claim in enumerate(non_supported, 1):
    print(f"[{i}] {claim['knowledge_id']} ({claim['knowledge_type'].upper()})")
    print(f"    Status: {claim['verification_status']['status']}")
    print(f"    Claim: {claim['claim_text']}")
    print(f"    Reason: {claim['verification_status']['reason']}")
    print(f"    Confidence: {claim['verification_status']['confidence']}")
    print(f"    Source units: {claim['source_unit_ids']}")
    print()
