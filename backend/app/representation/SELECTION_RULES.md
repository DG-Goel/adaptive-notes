# Representation Selection Rules

Quick reference for format selection logic.

## Format Selection Matrix

| Input | Characteristic | Selected Format | Score | Requirements |
|-------|---------------|-----------------|-------|--------------|
| **Definition** (with term+text) | DEFINITION | DEFINITION_BOX | 0.95 | term ≠ empty, definition_text ≠ empty |
| **Definition** (incomplete) | DEFINITION | DEFINITION_BOX | 0.70 | Missing some fields |
| **Example** (with exemplifies+text) | EXAMPLE | EXAMPLE_CALLOUT | 0.95 | exemplifies ≠ empty, example_text ≠ empty |
| **Example** (incomplete) | EXAMPLE | EXAMPLE_CALLOUT | 0.70 | Missing some fields |
| **Procedure** (≥2 steps, non-temporal) | SEQUENCE | FLOWCHART | 0.90 | len(steps) ≥ 2, no temporal keywords |
| **Procedure** (≥2 steps, temporal) | SEQUENCE | TIMELINE | 0.85 | len(steps) ≥ 2, has temporal keywords |
| **Procedure** (1 step) | SEQUENCE | FLOWCHART | 0.50 | len(steps) = 1 |
| **Explanation** (causal, extractable) | CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | 0.90 | Can parse cause→effect |
| **Explanation** (causal, implicit) | CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | 0.60 | Causal type but unclear structure |
| **Explanation** (procedural, steps) | SEQUENCE | FLOWCHART | 0.70 | Has step structure |
| **Explanation** (procedural, no steps) | SEQUENCE | FLOWCHART | 0.40 | Missing step structure |
| **Explanation** (functional/interpretive) | FACTUAL_EXPLANATION | STANDARD_TEXT | 0.20 | No specific format available |
| **Fact** (general) | FACTUAL_EXPLANATION | STANDARD_TEXT | 0.20 | No specific format available |
| **Fact** (statistical) | FACTUAL_EXPLANATION, COMPARISON | STANDARD_TEXT | 0.20 | Comparison dimensions not explicit |
| **Formula** (with formula_text) | DEFINITION | FORMULA_DISPLAY | 0.95 | formula_text ≠ empty |
| **Formula** (without formula_text) | DEFINITION | FORMULA_DISPLAY | 0.30 | formula_text empty |
| **Concept** (with aliases) | DEFINITION | DEFINITION_BOX | 0.80 | len(aliases) > 0 |
| **Concept** (without aliases, >10 chars) | - | STANDARD_TEXT | 0.20 | No clear structure |
| **Concept** (without aliases, ≤10 chars) | UNKNOWN | STANDARD_TEXT | 0.20 | Insufficient content |
| **Relationship** (is_a, part_of) | HIERARCHY | STANDARD_TEXT | 0.40 | Single level insufficient for tree |
| **Relationship** (causes, leads_to) | CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | 0.85 | Clear causal relationship |
| **Relationship** (contrasts_with) | COMPARISON | STANDARD_TEXT | 0.30 | Dimensions not explicit |
| **Relationship** (exemplifies) | EXAMPLE | EXAMPLE_CALLOUT | 0.95 | Relationship type indicates example |
| **Any** with UNKNOWN | UNKNOWN | STANDARD_TEXT | 0.20 | Fallback |

## Temporal Keywords

Used to distinguish TIMELINE from FLOWCHART for sequences:

```python
[
    "year", "month", "week", "day", "date", "time",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "before", "after", "during", "when", "while"
]
```

## Cause-Effect Detection Patterns

Used to identify extractable cause-effect relationships:

```python
[
    r'because\s+.+?,\s+therefore',    # "because X, therefore Y"
    r'since\s+.+?,\s+then',           # "since X, then Y"
    r'.+?\s+causes\s+.+',             # "X causes Y"
    r'.+?\s+results in\s+.+',         # "X results in Y"
    r'.+?\s+leads to\s+.+'            # "X leads to Y"
]
```

## Step Structure Detection

Used to identify step-like content:

```python
# Numbered/ordered steps
r'\b(step \d|first|second|third|then|next)\b'

# Bullet/list structure
r'(\n\s*[-*•]\s|\n\s*\d+\.)'
```

## Confidence Thresholds

| Score Range | Label | Meaning |
|-------------|-------|---------|
| 0.80 - 1.00 | high | All requirements met, clear structural fit |
| 0.60 - 0.79 | medium | Requirements met, some ambiguity |
| 0.30 - 0.59 | low | Minimal requirements, weak match |
| 0.00 - 0.29 | fallback | Using STANDARD_TEXT due to insufficient evidence |

## Multiple Characteristics Handling

When an item has multiple characteristics:

1. **Score all candidates** based on each characteristic
2. **Sort by score** (descending)
3. **Select primary** (highest score)
4. **Consider secondary** if:
   - Secondary score ≥ 70% of primary score
   - Formats are different
   - Formats are complementary

### Complementary Format Pairs

- DEFINITION_BOX + EXAMPLE_CALLOUT
- FLOWCHART + STANDARD_TEXT
- CAUSE_EFFECT_DIAGRAM + STANDARD_TEXT
- Any structured format + STANDARD_TEXT

## Format Requirements Summary

### DEFINITION_BOX
- **Requires**: term, definition text
- **Best for**: Definitions, Concepts with aliases, Formulas

### EXAMPLE_CALLOUT
- **Requires**: What it exemplifies, example text
- **Best for**: Examples, Relationships with "exemplifies" type

### FLOWCHART
- **Requires**: ≥2 ordered steps
- **Best for**: Procedures, Procedural explanations

### TIMELINE
- **Requires**: ≥2 events, temporal markers
- **Best for**: Temporal sequences, Historical events

### CAUSE_EFFECT_DIAGRAM
- **Requires**: Identifiable cause, identifiable effect
- **Best for**: Causal explanations, Causal relationships

### HIERARCHY_TREE
- **Requires**: ≥2 levels of parent-child relationships
- **Best for**: Multi-level hierarchies (rarely selected for single items)

### COMPARISON_TABLE
- **Requires**: ≥2 items, comparison dimensions
- **Best for**: Structured comparisons (rarely selected for single items)

### FORMULA_DISPLAY
- **Requires**: Valid formula text
- **Best for**: Mathematical/scientific formulas

### STANDARD_TEXT
- **Requires**: Any content
- **Best for**: Fallback for all items without specific format match

## Decision Tree

```
Is it a Definition with term+text?
├─ YES → DEFINITION_BOX (0.95)
└─ NO ↓

Is it an Example with exemplifies+text?
├─ YES → EXAMPLE_CALLOUT (0.95)
└─ NO ↓

Is it a Formula with formula_text?
├─ YES → FORMULA_DISPLAY (0.95)
└─ NO ↓

Is it a Procedure with ≥2 steps?
├─ YES → Check temporal markers
│   ├─ Has temporal → TIMELINE (0.85)
│   └─ No temporal → FLOWCHART (0.90)
└─ NO ↓

Is it CAUSE_EFFECT characteristic?
├─ YES → Check if cause/effect extractable
│   ├─ Extractable → CAUSE_EFFECT_DIAGRAM (0.90)
│   └─ Not extractable → CAUSE_EFFECT_DIAGRAM (0.60)
└─ NO ↓

Is it a Concept with aliases?
├─ YES → DEFINITION_BOX (0.80)
└─ NO ↓

Is it UNKNOWN or insufficient evidence?
├─ YES → STANDARD_TEXT (0.20)
└─ NO → Check remaining patterns...

No strong match found?
└─ STANDARD_TEXT (0.20) [fallback]
```

## Notes

- All scores are in range [0.0, 1.0]
- STANDARD_TEXT always available as fallback (0.20 score)
- Selection is deterministic (same input → same output)
- No randomness or LLM calls involved
- Original knowledge items never modified
