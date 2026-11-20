# Semantic Faithfulness Verification

## Overview

The semantic faithfulness verifier checks whether generated knowledge items are semantically supported by their original source units. This is a separate module from the structural evaluator and must be explicitly invoked.

## Purpose

- **Structural Evaluator** (`FaithfulnessEvaluator`): Validates coverage, provenance integrity, and representation validity
- **Semantic Verifier** (`DeterministicSemanticVerifier`): Validates factual correctness of extracted claims against source text

Both are necessary for complete pipeline validation.

## Verification Methods

### Deterministic Verification (Current)

The `DeterministicSemanticVerifier` performs rule-based semantic verification:

1. **Keyword/Phrase Matching**: Measures text overlap between claims and source
2. **Numeric Accuracy**: Verifies numbers, percentages, years match exactly
3. **Named Entity Matching**: Checks proper nouns (names, places) are preserved
4. **Basic Contradiction Detection**: Flags numeric/entity mismatches

### Verification Statuses

Each claim receives one of these statuses:

- **SUPPORTED**: High keyword overlap, all numerics/entities match, no contradictions
- **UNSUPPORTED**: Very low keyword overlap, claim contains many terms not in source
- **CONTRADICTED**: Numeric or entity mismatches detected
- **INCONCLUSIVE**: Ambiguous evidence, cannot determine with confidence
- **INSUFFICIENT_EVIDENCE**: No source text available for verification

### Status Decision Logic

```python
# CONTRADICTED
if numeric_mismatch or significant_entity_mismatch:
    return "CONTRADICTED"

# SUPPORTED
if keyword_overlap >= 70%:
    return "SUPPORTED" (high confidence)
elif keyword_overlap >= 40%:
    return "SUPPORTED" (moderate confidence)

# UNSUPPORTED
if keyword_overlap < 20%:
    return "UNSUPPORTED"

# INCONCLUSIVE (default for ambiguous cases)
else:
    return "INCONCLUSIVE"
```

## Semantic Faithfulness Verified Criteria

The report marks `semantic_faithfulness_verified = True` only if ALL of:

1. **No contradictions**: `claims_contradicted == 0`
2. **High support rate**: At least 80% of claims are SUPPORTED
3. **Low unsupported rate**: Less than 10% are UNSUPPORTED
4. **Complete verification**: No INSUFFICIENT_EVIDENCE cases

These thresholds are conservative to avoid false positives.

## Usage

### Basic Usage

```python
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier
from app.models.source import SourceDocument
from app.models.knowledge import KnowledgeDocument

# Load documents
source_doc = SourceDocument(**source_data)
knowledge_doc = KnowledgeDocument(**knowledge_data)

# Run verification
verifier = DeterministicSemanticVerifier(verbose=True)
report = verifier.verify(knowledge_doc, source_doc)

# Check results
print(f"Support rate: {report.support_rate:.1%}")
print(f"Contradicted: {report.claims_contradicted}")
print(f"Verified: {report.semantic_faithfulness_verified}")
```

### Command-Line Script

```bash
python run_semantic_verification.py
```

This script:
1. Loads `data/output/source_units.json`
2. Loads `data/output/knowledge_document.json`
3. Runs deterministic verification
4. Saves report to `data/output/semantic_verification_report.json`
5. Prints human-readable summary

### Integration with Structural Evaluator

```python
from app.evaluation.evaluator import FaithfulnessEvaluator
from app.evaluation.semantic_verifier import DeterministicSemanticVerifier

# Run structural evaluation
structural_evaluator = FaithfulnessEvaluator()
structural_report = structural_evaluator.evaluate(
    source_doc, knowledge_doc, analyzed_doc,
    represented_doc, assembled_doc, render_manifest
)

# Run semantic verification
semantic_verifier = DeterministicSemanticVerifier()
semantic_report = semantic_verifier.verify(knowledge_doc, source_doc)

# Attach semantic results to structural report
structural_report.semantic_verification_report = semantic_report.model_dump()
structural_report.semantic_faithfulness_verified = semantic_report.semantic_faithfulness_verified
structural_report.semantic_faithfulness_note = (
    f"Semantic verification performed: {semantic_report.claims_supported}/"
    f"{semantic_report.total_claims_verified} claims supported"
)
```

## Verification Report Structure

```json
{
  "verification_timestamp": "2026-10-20T22:33:29.901038",
  "document_id": "TEST_DOC",
  "source_filename": "test.pdf",
  
  "total_claims_verified": 8,
  "claims_supported": 5,
  "claims_unsupported": 1,
  "claims_contradicted": 0,
  "claims_inconclusive": 2,
  "claims_insufficient_evidence": 0,
  
  "semantic_faithfulness_verified": false,
  "verification_complete": true,
  "verification_method": "deterministic",
  
  "claim_verifications": [
    {
      "knowledge_id": "CON_0001",
      "knowledge_type": "concept",
      "claim_text": "The practice of assigning meaning to dreams",
      "source_unit_ids": ["TEST_DOC_0001", "TEST_DOC_0002"],
      
      "verification_status": {
        "status": "INCONCLUSIVE",
        "confidence": 0.5,
        "reason": "Moderate keyword overlap (25.0%) but insufficient evidence for strong verdict",
        "evidence_snippets": ["TEST_DOC_0001: She learned to interpret dreams..."],
        "has_numeric_match": true,
        "has_entity_match": true,
        "has_keyword_match": false
      },
      
      "numeric_verification": {
        "claimed_numbers": [],
        "source_numbers": [],
        "all_matched": true,
        "mismatches": []
      },
      
      "entity_verification": {
        "claimed_entities": [],
        "source_entities": [],
        "all_matched": true,
        "mismatches": []
      },
      
      "source_snippets": ["TEST_DOC_0001: She learned to interpret dreams..."],
      "source_full_text": "She learned to interpret dreams as a child...",
      "verification_method": "deterministic"
    }
  ],
  
  "limitations": [
    "This verification uses deterministic text matching and heuristics only.",
    "Cannot detect paraphrasing or semantic equivalence beyond keyword matching.",
    "May produce false negatives (marking valid claims as INCONCLUSIVE).",
    "Returns INCONCLUSIVE when evidence is ambiguous rather than making guesses.",
    "Numeric and entity matching is case-sensitive and exact.",
    "Does not understand context, inference, or implicit information."
  ]
}
```

## Claim Verification Details

Each `ClaimVerification` includes:

### Overall Verdict
- `verification_status.status`: SUPPORTED | UNSUPPORTED | CONTRADICTED | INCONCLUSIVE | INSUFFICIENT_EVIDENCE
- `verification_status.confidence`: 0.0 to 1.0
- `verification_status.reason`: Human-readable explanation

### Detailed Checks
- `numeric_verification`: Numbers in claim vs source
- `entity_verification`: Named entities in claim vs source
- `verification_status.has_keyword_match`: Boolean

### Evidence
- `source_snippets`: Short excerpts from source units (up to 200 chars each)
- `source_full_text`: Complete concatenated source text
- `verification_status.evidence_snippets`: Relevant supporting excerpts

## Examples

### Example 1: Supported Claim

**Source Text:**
```
A short story is a prose narrative of limited length, typically under 7,500 words.
```

**Extracted Claim:**
```
A short story is a prose narrative of limited length.
```

**Verification Result:**
- Status: `SUPPORTED`
- Confidence: 0.95
- Reason: Strong keyword overlap (87.5%), no contradictions
- Has keyword match: true
- Has numeric match: true (no numbers to check)

### Example 2: Contradicted Claim (Numeric Mismatch)

**Source Text:**
```
The study included 450 participants over a period of 3 years.
```

**Extracted Claim:**
```
The study included 350 participants.
```

**Verification Result:**
- Status: `CONTRADICTED`
- Confidence: 0.9
- Reason: Numeric mismatch: claimed numbers ['350'] not found in source
- Has numeric match: false
- Numeric mismatches: [{"claimed": "350", "status": "not_found_in_source"}]

### Example 3: Unsupported Claim (Added Details)

**Source Text:**
```
The protagonist faces a difficult choice.
```

**Extracted Claim:**
```
The protagonist John Smith faces a moral dilemma about betraying his country.
```

**Verification Result:**
- Status: `UNSUPPORTED` or `CONTRADICTED`
- Confidence: 0.7-0.8
- Reason: Low keyword overlap, claim contains many terms not in source: John, Smith, moral, dilemma, betraying, country
- Entity mismatches: ["John Smith"] not in source

### Example 4: Inconclusive (Paraphrase)

**Source Text:**
```
The character experiences transformation.
```

**Extracted Claim:**
```
The character undergoes psychological metamorphosis.
```

**Verification Result:**
- Status: `INCONCLUSIVE`
- Confidence: 0.5
- Reason: Moderate keyword overlap but insufficient evidence for strong verdict
- Note: Deterministic verifier cannot detect paraphrasing

## Limitations

### What the Deterministic Verifier CAN Do

✓ Detect exact numeric mismatches  
✓ Detect missing or incorrect named entities  
✓ Measure keyword overlap between claim and source  
✓ Flag claims with very low source support  
✓ Provide deterministic, repeatable results  

### What the Deterministic Verifier CANNOT Do

✗ Understand paraphrasing or semantic equivalence  
✗ Detect subtle contradictions beyond numeric/entity mismatches  
✗ Reason about context or inference  
✗ Understand implicit information  
✗ Handle synonyms or related terms  
✗ Evaluate logical validity of claims  

### Expected Behavior

- **False Negatives**: Valid paraphrases may be marked INCONCLUSIVE
- **True Positives**: Numeric/entity contradictions are reliably detected
- **Conservative**: Returns INCONCLUSIVE rather than guessing
- **Deterministic**: Same input always produces same output

## When Verification Fails

If `semantic_faithfulness_verified == False`, check:

1. **Contradictions** (`claims_contradicted > 0`):
   - Review numeric verification details
   - Check entity mismatches
   - Verify extraction didn't introduce errors

2. **Low Support Rate** (`support_rate < 80%`):
   - Many INCONCLUSIVE claims may indicate:
     - Extraction used heavy paraphrasing
     - Source text is insufficient
     - Knowledge items combine multiple sources
   - Review UNSUPPORTED claims for factual additions

3. **Unsupported Claims** (`claims_unsupported > 0`):
   - Check if extraction added details not in source
   - Verify source_unit_ids are correct
   - Review unique keywords not in source

## Future Enhancements

### LLM-Assisted Verification (Optional)

Future versions may include optional LLM-assisted semantic verification:

```python
verifier = LLMAssistedSemanticVerifier(
    api_key="...",
    model="gpt-4",
    fallback_to_deterministic=True
)
```

**Requirements for LLM Verifier:**
- Must cite supplied evidence explicitly
- Must validate output against schema
- Must not claim guaranteed correctness
- Must document when LLM was used vs deterministic
- Must be clearly optional and configurable

### Other Potential Enhancements

- Synonym/paraphrase detection using embeddings
- Logical validity checking
- Cross-reference resolution
- Temporal reasoning (dates, sequences)
- Quantifier handling (all, some, most)

## Testing

Run semantic verifier tests:

```bash
pytest tests/test_semantic_verifier.py -v
```

**Test Coverage:**
- Direct support from source
- Numeric contradictions
- Entity mismatches
- Unsupported additions
- Ambiguous evidence (INCONCLUSIVE)
- Missing source units
- Empty documents
- Deterministic repeatability
- Multiple knowledge types

## Integration Checklist

When integrating semantic verification into the pipeline:

- [ ] Run semantic verification AFTER extraction
- [ ] Include semantic report in evaluation output
- [ ] Keep `semantic_faithfulness_verified` false unless criteria met
- [ ] Document verification method used (deterministic vs LLM)
- [ ] Include limitations in report
- [ ] Do not claim semantic verification is perfect
- [ ] Separate from structural evaluation results
- [ ] Provide claim-level verification details
- [ ] Include evidence snippets for review
- [ ] Make verification output machine-readable

## Summary

The semantic faithfulness verifier provides **deterministic, rule-based verification** of whether extracted knowledge items are supported by their source text. It complements the structural evaluator by checking factual correctness, not just structural validity.

**Key Points:**
- Returns INCONCLUSIVE when uncertain (conservative approach)
- Reliably detects numeric and entity contradictions
- Cannot understand paraphrasing (limitation of deterministic approach)
- Provides detailed per-claim verification with evidence
- Separate from structural evaluation
- Must be explicitly invoked

**Next Steps:**
- Review verification reports manually
- Investigate CONTRADICTED claims (likely extraction errors)
- Consider INCONCLUSIVE claims as needing human review
- Use verification to tune extraction prompts
- Consider LLM-assisted verification for paraphrase detection
