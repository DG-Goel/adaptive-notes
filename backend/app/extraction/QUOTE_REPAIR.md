# Quote Repair System

## Overview

The quote repair system automatically fixes inexact evidence quotes that don't match source text exactly. This addresses a common LLM behavior where models paraphrase slightly (changing contractions, pronouns, or case) while maintaining semantic equivalence.

## Problem

During live extraction runs, the model generated quotes that were semantically correct but textually inexact:

1. **Case variations**: `"Java SE"` → `"Java se"` 
2. **Contractions**: `"you will"` → `"you'll"`
3. **Pronoun substitutions**: `"you can see"` → `"we can see"`

These inexact quotes caused strict validation to reject otherwise valid extractions.

## Solution

The `QuoteRepair` class finds and corrects inexact quotes through:

### 1. Variant Generation
- Expands/contracts common contractions (you'll ↔ you will)
- Swaps common pronouns (you ↔ we ↔ I) with auxiliary verb handling
- Handles case variations (SE ↔ se)

### 2. Fuzzy Matching
- Uses SequenceMatcher for similarity scoring (0-1)
- Minimum similarity threshold: 0.85
- Maximum length difference: 20 characters

### 3. Semantic Validation
- Verifies content word overlap (80% minimum)
- Ensures similarity above threshold (0.90 for strict mode)
- Confirms no critical information is changed

## Integration

Quote repair is integrated into `KnowledgeExtractor` when `strict_evidence=True`:

```python
# In _parse_response, after JSON parsing:
if self.strict_evidence:
    data = self._repair_quotes_in_response(data, chunk)
    self._validate_strict_raw_contract(data, chunk)
```

The repair happens **before** strict validation, ensuring corrected quotes pass exact-match checks.

## Diagnostics

Repaired quotes are logged in `extractor.repaired_quotes`:

```python
{
    'chunk_id': 'CHUNK_001',
    'category': 'concepts',
    'source_id': 'T0001',
    'fields': ['/concept_name', '/content'],
    'original_quote': 'Java SE which is short for Java standard edition',
    'repaired_quote': 'Java se which is short for Java standard edition',
    'similarity': 1.000,
    'position': 1850,
    'repair_type': 'case_insensitive',
    'validation': 'Semantically equivalent'
}
```

## Real-World Performance

Live test with Java transcript:
- **Total evidence entries**: 10
- **Repairs needed**: 3 (30%)
- **Successful repairs**: 3 (100%)
- **Failed repairs**: 0

All three failing quotes from the live run were successfully repaired:
1. Java SE case difference (1.000 similarity)
2. Contraction difference (0.958 similarity)  
3. Pronoun difference (0.970 similarity)

## Configuration

```python
repairer = QuoteRepair(
    min_similarity=0.85,  # Minimum similarity for fuzzy match
    max_length_diff=20    # Max character difference from original
)
```

## Limitations

- Does not correct semantic errors (wrong concepts, hallucinations)
- Only repairs small textual variations, not substantial rewrites
- Requires semantic equivalence validation to pass
- Limited to predefined pronoun and contraction patterns

## Future Improvements

Potential enhancements if needed:
1. More language-specific contraction patterns
2. Context-aware pronoun resolution
3. Better handling of quoted code vs prose
4. Machine learning-based similarity for technical terms
5. Support for multiple languages beyond English

## Testing

See:
- `test_quote_repair.py` — Unit tests with actual failing cases
- `test_extractor_quote_repair.py` — Integration test with full extractor

Both tests use the real failing quotes from the Java live run (November 6, 2026).
