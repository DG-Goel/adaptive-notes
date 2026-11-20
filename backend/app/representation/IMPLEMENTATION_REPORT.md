# Representation Selector Layer - Implementation Report

## Summary

Successfully implemented the **Representation Selector layer**, the fourth layer in the adaptive notes-generation pipeline. This layer maps analyzed knowledge items to appropriate visual/textual representation formats using deterministic, rule-based selection.

## Implementation Status

✅ **COMPLETE** - All requirements met, all tests passing

- 19/19 unit tests passing
- 1/1 end-to-end integration test passing
- All previous layer tests still passing (23 extraction + 27 analysis)
- **Total: 70 tests passing across all layers**

## Files Created

### Core Implementation

1. **`app/representation/__init__.py`** - Module exports
2. **`app/representation/formats.py`** - RepresentationFormat enum (9 formats)
3. **`app/representation/models.py`** - Data models (SelectedRepresentation, RepresentationDocument, Statistics)
4. **`app/representation/selector.py`** - Main selection logic (RepresentationSelector class)
5. **`app/representation/DESIGN.md`** - Design documentation
6. **`app/representation/IMPLEMENTATION_REPORT.md`** - This file

### Tests

7. **`tests/test_representation_unit.py`** - 19 unit tests
8. **`test_representation_e2e.py`** - End-to-end integration test

## Supported Representation Formats

The selector supports 9 representation formats:

1. **STANDARD_TEXT** - Default format for general content
2. **DEFINITION_BOX** - Highlighted term definitions
3. **COMPARISON_TABLE** - Side-by-side comparisons
4. **FLOWCHART** - Step-by-step process visualization
5. **TIMELINE** - Chronological event sequences
6. **CAUSE_EFFECT_DIAGRAM** - Causal relationship visualization
7. **HIERARCHY_TREE** - Parent-child relationship structure
8. **EXAMPLE_CALLOUT** - Highlighted illustrative examples
9. **FORMULA_DISPLAY** - Mathematical/scientific formula formatting

## Selection Rules

### Type-Based Mappings (High Confidence)

| Knowledge Type | Characteristic | Format | Score | Notes |
|---------------|---------------|--------|-------|-------|
| Definition | DEFINITION | DEFINITION_BOX | 0.95 | With term + text |
| Example | EXAMPLE | EXAMPLE_CALLOUT | 0.95 | With exemplifies + text |
| Procedure (multi-step) | SEQUENCE | FLOWCHART | 0.9 | ≥2 steps |
| Procedure (temporal) | SEQUENCE | TIMELINE | 0.85 | With time markers |
| Causal Explanation | CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | 0.9 | Extractable cause/effect |
| Formula | - | FORMULA_DISPLAY | 0.95 | With formula text |
| Relationship (hierarchical) | HIERARCHY | - | 0.4 | Single level insufficient |
| Relationship (causal) | CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | 0.85 | Explicit causation |
| Concept (with aliases) | DEFINITION | DEFINITION_BOX | 0.8 | Implies definition |

### Content-Based Detection (Medium Confidence)

- **Temporal sequences**: Detected via keywords (year, month, January, before, after, etc.)
- **Cause-effect patterns**: Regex matching "because...therefore", "X causes Y", "leads to"
- **Step structure**: Numbered steps, "first/then/next" patterns

### Fallback Behavior

- **UNKNOWN** characteristic → STANDARD_TEXT (0.2 score)
- **Missing required fields** → Reduced confidence, may still select format
- **Insufficient evidence** → STANDARD_TEXT fallback
- **Single-step procedures** → FLOWCHART with low confidence (0.5)
- **Ambiguous content** → Highest-scoring candidate wins

## Confidence Scoring

Confidence labels are assigned based on selection scores:

- **High** (0.8-1.0): All requirements met, clear structural fit
- **Medium** (0.6-0.79): Requirements met, some ambiguity
- **Low** (0.3-0.59): Minimal requirements, weak match
- **Fallback** (0.0-0.29): Using STANDARD_TEXT due to insufficient evidence

## Provenance Preservation

The selector preserves all traceability information:

- ✅ `source_unit_ids` - Copied exactly from knowledge item
- ✅ `document_id` - Preserved from original document
- ✅ `knowledge_id` - Preserved from knowledge item
- ✅ `knowledge_type` - Preserved from knowledge item
- ✅ Original items unchanged - No mutation of input data

## Content Extraction

Each format has specific content requirements extracted from knowledge items:

### DEFINITION_BOX
```python
{
    "term": str,
    "definition": str,
    "context": Optional[str]
}
```

### EXAMPLE_CALLOUT
```python
{
    "exemplifies": str,
    "example_text": str,
    "example_type": Optional[str]
}
```

### FLOWCHART
```python
{
    "steps": List[str],
    "procedure_name": Optional[str]
}
```

### CAUSE_EFFECT_DIAGRAM
```python
{
    "cause": str,
    "effect": str,
    "mechanism": Optional[str]
}
```

### STANDARD_TEXT
```python
{
    "content": str
}
```

## Test Results

### Unit Tests (19 tests)

```
Format Selection (7 tests):
✅ Definition → DEFINITION_BOX
✅ Example → EXAMPLE_CALLOUT
✅ Procedure → FLOWCHART
✅ Single-step procedure → Low confidence
✅ Causal explanation → CAUSE_EFFECT_DIAGRAM
✅ Formula → FORMULA_DISPLAY
✅ UNKNOWN → STANDARD_TEXT

Multiple Characteristics (2 tests):
✅ Multiple characteristics pick best
✅ Conflicting characteristics deterministic

Content Validation (2 tests):
✅ Missing required fields → Reduced confidence
✅ Temporal vs procedural sequence detection

Provenance (2 tests):
✅ Provenance preserved
✅ No source modification

Edge Cases (3 tests):
✅ Empty content handling
✅ Formula without formula text
✅ Single-level hierarchy

Other (3 tests):
✅ Confidence scoring accuracy
✅ Deterministic selection
✅ Complementary format detection
```

### End-to-End Test

**Input**: 8 knowledge items from test.pdf
- 2 Concepts
- 2 Explanations
- 1 Example
- 2 Facts
- 1 Relationship

**Output**: 8 representations
- 2 DEFINITION_BOX (concepts with aliases)
- 2 CAUSE_EFFECT_DIAGRAM (causal explanation + causal relationship)
- 1 EXAMPLE_CALLOUT (example)
- 3 STANDARD_TEXT (functional explanation + 2 facts)

**Statistics**:
- 4 high confidence
- 1 medium confidence
- 3 fallback
- 0 items with secondary format
- 4 different formats used
- 100% provenance preserved

## E2E Pipeline Test Commands

```powershell
cd "C:\Projects\adaptive-notes\backend"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD"

# Run all tests
python tests/test_extraction_unit.py        # 23 tests
python tests/test_content_analysis.py       # 27 tests
python tests/test_representation_unit.py    # 19 tests
python test_representation_e2e.py           # 1 e2e test

# Total: 70 tests, all passing
```

## Known Limitations

### By Design

1. **No LLM calls** - Purely rule-based, deterministic
2. **No rendering** - Selects formats only, doesn't generate output
3. **No personalization** - Doesn't consider user preferences
4. **No adaptive learning** - Doesn't adjust based on performance
5. **Single-level structures** - Hierarchy/comparison require multi-item analysis

### Content Requirements

1. **COMPARISON_TABLE** - Rarely selected due to need for explicit dimensions
2. **HIERARCHY_TREE** - Single relationships insufficient for tree visualization
3. **TIMELINE** - Requires explicit temporal markers
4. **CAUSE_EFFECT_DIAGRAM** - Works best with explicit cause-effect language

### Not Implemented (Future Layers)

- Note assembly and layout
- HTML/PDF rendering
- Interactive diagram generation
- Personalization based on learning style
- Performance-based adaptation
- Faithfulness evaluation
- Repair pipeline

## Selection Decision Examples

### Example 1: Concept with Aliases → Definition Box

**Input**:
```python
Concept(
    concept_name="dream interpretation",
    content="The practice of assigning meaning to dreams",
    aliases=["dream reading", "oneiromancy"]
)
Characteristic: DEFINITION (medium confidence)
```

**Selection**:
- Format: DEFINITION_BOX
- Score: 0.80
- Confidence: high
- Reasoning: "Concept with aliases serves as definition"

**Content**:
```python
{
    "term": "dream interpretation",
    "definition": "The practice of assigning meaning to dreams",
    "context": None
}
```

### Example 2: Causal Explanation → Cause-Effect Diagram

**Input**:
```python
Explanation(
    explanation_type="causal",
    explanation_text="Because the dream was prophetic, the narrator left Vienna immediately"
)
Characteristic: CAUSE_EFFECT (high confidence)
```

**Selection**:
- Format: CAUSE_EFFECT_DIAGRAM
- Score: 0.60
- Confidence: medium
- Reasoning: "Causal explanation with implicit structure"

**Content**:
```python
{
    "cause": "the dream was prophetic",
    "effect": "the narrator left Vienna",
    "mechanism": "Because the dream was prophetic, the narrator left Vienna immediately"
}
```

### Example 3: Example → Example Callout

**Input**:
```python
Example(
    exemplifies="dream interpretation",
    example_text="When someone dreamed of drowning, she interpreted it..."
)
Characteristic: EXAMPLE (high confidence)
```

**Selection**:
- Format: EXAMPLE_CALLOUT
- Score: 0.95
- Confidence: high
- Reasoning: "Example with clear exemplification"

**Content**:
```python
{
    "exemplifies": "dream interpretation",
    "example_text": "When someone dreamed of drowning, she interpreted it...",
    "example_type": "literary"
}
```

## Architecture Position

```
[Ingestion Layer]           (Docling-based PDF parsing)
        ↓                   109 source units
[Knowledge Extraction]      (LLM-based, 8 knowledge types)
        ↓                   8 knowledge items
[Content Analysis]          (Rule-based, 9 characteristics)
        ↓                   8 analyzed items
[Representation Selector]   ← **CURRENT LAYER**
        ↓                   8 representations (4 formats)
[Note Assembler]            (NOT YET IMPLEMENTED)
        ↓
[Final Output]
```

## Design Principles Maintained

✅ **Deterministic** - Same input always produces same output
✅ **Transparent** - Every selection has explicit reasoning
✅ **Evidence-based** - Formats justified by content characteristics
✅ **Conservative** - Defaults to STANDARD_TEXT when evidence insufficient
✅ **Non-destructive** - Never modifies original knowledge items
✅ **Traceable** - Preserves all source IDs and provenance
✅ **Testable** - Pure functions, no external dependencies
✅ **Extensible** - New formats can be added without rewriting core logic

## Verification Checklist

- ✅ Phase 1: Inspected existing models and interfaces
- ✅ Phase 2: Defined 9 representation formats with extensible design
- ✅ Phase 3: Implemented deterministic selection with transparent scoring
- ✅ Phase 4: Created structured output models with provenance
- ✅ Phase 5: Wrote comprehensive unit and integration tests
- ✅ All existing tests still passing
- ✅ No modifications to previous layers
- ✅ No implementation of future layers

## Next Steps (Not Implemented)

The following layers remain to be implemented:

1. **Note Assembler** - Layout and structure assembly
2. **Renderer** - HTML/PDF generation with actual diagrams
3. **Personalization** - Learning style adaptation
4. **Analytics** - Performance tracking
5. **Faithfulness Evaluator** - Accuracy verification
6. **Repair Pipeline** - Error correction and improvement

## Conclusion

The Representation Selector layer is **complete and validated**. It successfully maps content characteristics to appropriate representation formats using deterministic, rule-based selection. All 70 tests across all four implemented layers are passing.

The system is ready for the next layer (Note Assembler) to be designed and implemented.
