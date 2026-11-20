#!/usr/bin/env python3
"""
Provenance audit for three claims flagged as INSUFFICIENT_SOURCE_CONTEXT.
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 80)
    print("PROVENANCE AUDIT REPORT")
    print("=" * 80)
    print()
    
    # Load data
    artifact_dir = Path("data/output/java_transcript_validation")
    
    with open(artifact_dir / "source_units_20261030_185308.json", 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    source_units_map = {unit['source_id']: unit for unit in source_data['source_units']}
    
    # Define audit results based on manual investigation
    audit_results = [
        {
            "knowledge_id": "EXP_0303",
            "knowledge_type": "explanation",
            "claim": "int is used for principal because short's max (32,000) is insufficient; float suffices for interest rates; byte is enough for a period up to 30 years.",
            "claimed_source_ids": ["T0032"],
            "classification": "INCORRECT_PROVENANCE",
            "correct_source_ids": ["T0032", "T0033"],
            "reasoning": "Claim is factually correct and grounded in source. T0032 discusses int for principal (32,000 limit) and float for interest. T0033 explicitly states 'maximum number we want to support is 30 so one byte is sufficient'. Extraction failed to include T0033 in source_unit_ids.",
            "evidence": {
                "T0032": "I thought integer is a good datatype for storing the principle because short is not enough with short we can store a maximum of $32,000... next we get the period we read this as a byte",
                "T0033": "because the maximum number we want to support is 30 so one byte is sufficient to store the number 30 or anything smaller"
            },
            "action_required": "Add T0033 to source_unit_ids for EXP_0303"
        },
        {
            "knowledge_id": "EXM_0215",
            "knowledge_type": "example",
            "claim": "double result = (double)5 / 2; // result is 2.5",
            "claimed_source_ids": ["T0022"],
            "classification": "INCORRECT_PROVENANCE",
            "correct_source_ids": ["T0024"],
            "reasoning": "Example demonstrates explicit casting in division. T0022 discusses final variables and constants (PI), not casting. T0024 extensively discusses casting and type conversion with examples of implicit and explicit casting. The example appears to be a pedagogical illustration derived from T0024's casting discussion, though the exact code may not appear verbatim.",
            "evidence": {
                "T0022": "its value later on you can see here we have a compilation error and it says cannot assign a value to final variable pi [discusses constants, not casting]",
                "T0024": "in this tutorial we're going to talk about casting and type conversion... [discusses implicit and explicit casting with examples of type conversion]"
            },
            "action_required": "Change source_unit_ids from ['T0022'] to ['T0024'] for EXM_0215"
        },
        {
            "knowledge_id": "EXM_0431",
            "knowledge_type": "example",
            "claim": "An infinite while‑true loop asks for the principal; if the entered value is between 1,000 and 1,000,000, break exits the loop.",
            "claimed_source_ids": ["T0048"],
            "classification": "SUPPORTED",
            "correct_source_ids": ["T0048"],
            "reasoning": "Claim is correctly attributed. T0048 explicitly describes: 'while true so we're gonna keep asking the same question until the user enters a valid value... if principle is greater than or equal to 1000 and it is less than or equal to 1 million... then we can break out of this infinite loop'. Provenance is correct despite initial investigation suggesting otherwise (T0048 is long and while-loop content appears later in the unit).",
            "evidence": {
                "T0048": "I'm gonna wrap these two lines inside an infinite loop while true so we're gonna keep asking the same question until the user enters a valid value so here after we read the principle we can write an if statement like this if principle is greater than or equal to 1000 and it is less than or equal to 1 million... if the user enters a valid value then we can break out of this infinite loop"
            },
            "action_required": "None - provenance is correct"
        }
    ]
    
    # Print detailed results
    for i, result in enumerate(audit_results, 1):
        print(f"\n{i}. {result['knowledge_id']} ({result['knowledge_type']})")
        print("=" * 80)
        print(f"Claim: {result['claim']}")
        print(f"\nClaimed Source IDs: {result['claimed_source_ids']}")
        print(f"Classification: {result['classification']}")
        print(f"Correct Source IDs: {result['correct_source_ids']}")
        print(f"\nReasoning: {result['reasoning']}")
        print(f"\nAction Required: {result['action_required']}")
        
        if result['evidence']:
            print(f"\nEvidence:")
            for source_id, evidence_text in result['evidence'].items():
                print(f"  [{source_id}]: {evidence_text[:200]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    
    classifications = [r['classification'] for r in audit_results]
    summary = {
        "total_audited": len(audit_results),
        "SUPPORTED": classifications.count("SUPPORTED"),
        "INCORRECT_PROVENANCE": classifications.count("INCORRECT_PROVENANCE"),
        "GENUINE_EXTRACTION_ERROR": classifications.count("GENUINE_EXTRACTION_ERROR"),
        "INSUFFICIENT_SOURCE_CONTEXT": classifications.count("INSUFFICIENT_SOURCE_CONTEXT")
    }
    
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nActions Required:")
    actions = [r for r in audit_results if r['action_required'] != "None - provenance is correct"]
    if actions:
        for action in actions:
            print(f"  - {action['knowledge_id']}: {action['action_required']}")
    else:
        print("  None")
    
    # Save report
    output_dir = artifact_dir / "validation_20261101_143618"
    report_path = output_dir / f"provenance_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "audit_timestamp": datetime.now().isoformat(),
            "audited_claims": 3,
            "audit_results": audit_results,
            "summary": summary
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved to: {report_path}")
    
    return 0 if summary["INCORRECT_PROVENANCE"] == 0 and summary["GENUINE_EXTRACTION_ERROR"] == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
