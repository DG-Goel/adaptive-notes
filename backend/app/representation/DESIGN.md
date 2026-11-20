# Representation Selector Layer - Design Document

## Purpose

The Representation Selector layer maps analyzed knowledge items to appropriate visual/textual representation formats for adaptive learning. It bridges the gap between structural analysis (Content Analysis layer) and final rendering (future Note Assembler layer).

## Position in Architecture

```
Ingestion (Docling) → Knowledge Extraction (LLM) → Content Analysis (Rules) → **Representation Selector** → Note Assembler
```

**Input**: `AnalyzedKnowledgeDocument` (knowledge items with characteristics)  
**Output**: `RepresentationDocument` (knowledge items with selected formats)

## Supported Representation Formats

### 1. STANDARD_TEXT
- **Purpose**: Default format for general content
- **Use cases**: Simple facts, basic concepts, insufficient evidence
- **Requirements**: None (always available)

### 2. DEFINITION_BOX
- **Purpose**: Highlight term definitions
- **Use cases**: DEFINITION characteristic, concepts with aliases
- **Requirements**: term + definition text

### 3. COMPARISON_TABLE
- **Purpose**: Side-by-side comparison
- **Use cases**: COMPARISON characteristic with explicit dimensions
- **Requirements**: ≥2 items, comparison dimensions

### 4. FLOWCHART
- **Purpose**: Step-by-step process visualization
- **Use cases**: SEQUENCE characteristic with clear steps
- **Requirements**: ≥2 ordered steps

### 5. TIMELINE
- **Purpose**: Chronological event sequence
- **Use cases**: SEQUENCE with temporal markers
- **Requirements**: ≥2 events with time/order indicators

### 6. CAUSE_EFFECT_DIAGRAM
- **Purpose**: Causal relationship visualization
- **Use cases**: CAUSE_EFFECT characteristic with explicit cause → effect
- **Requirements**: Clear cause + effect identification

### 7. HIERARCHY_TREE
- **Purpose**: Parent-child relationship structure
- **Use cases**: HIERARCHY characteristic with multi-level structure
- **Requirements**: ≥2 levels of parent-child relationships

### 8. EXAMPLE_CALLOUT
- **Purpose**: Highlight illustrative examples
- **Use cases**: EXAMPLE characteristic
- **Requirements**: What it exemplifies + example content

### 9. FORMULA_DISPLAY
- **Purpose**: Mathematical/scientific formula formatting
- **Use cases**: Formula knowledge type with usable formula text
- **Requirements**: Valid formula text

## Selection Strategy

### Deterministic Rule-Based Selection

1. **Evidence Validation**: Verify the knowledge item contains required content for candidate formats
2. **Priority Scoring**: Score each candidate format based on:
   - Characteristic match (primary evidence)
   - Knowledge type alignment
   - Content completeness
   - Specificity (prefer specific formats over generic)
3. **Primary Selection**: Choose highest-scoring format
4. **Secondary Selection**: Optionally select a second format only if:
   - It scores ≥70% of primary score
   - It provides complementary value (different structural view)
   - The content supports both representations

### Selection Rules

#### High-Priority Mappings (direct evidence)

| Characteristic | Format | Requirement Check |
|---------------|--------|-------------------|
| DEFINITION | DEFINITION_BOX | Has term + definition text |
| EXAMPLE | EXAMPLE_CALLOUT | Has exemplifies + example text |
| CAUSE_EFFECT | CAUSE_EFFECT_DIAGRAM | Can extract cause + effect |
| COMPARISON | COMPARISON_TABLE | Has ≥2 items + dimensions |
| HIERARCHY | HIERARCHY_TREE | Has ≥2 levels |
| SEQUENCE (procedural) | FLOWCHART | Has ≥2 ordered steps |
| SEQUENCE (temporal) | TIMELINE | Has ≥2 time-ordered events |
| Formula type | FORMULA_DISPLAY | Has valid formula text |

#### Fallback Rules

- FACTUAL_EXPLANATION → STANDARD_TEXT (unless stronger characteristic present)
- RELATIONSHIP → STANDARD_TEXT (unless HIERARCHY/CAUSE_EFFECT/COMPARISON)
- UNKNOWN → STANDARD_TEXT
- Missing required content → STANDARD_TEXT

### Confidence Scoring

- **High confidence** (0.9-1.0): All requirements met, clear structural fit
- **Medium confidence** (0.6-0.8): Requirements met, but some ambiguity
- **Low confidence** (0.3-0.5): Minimal requirements, weak structural match
- **Fallback** (0.1-0.2): Using STANDARD_TEXT due to insufficient evidence

## Data Models

### RepresentationFormat (Enum)
```python
STANDARD_TEXT
DEFINITION_BOX
COMPARISON_TABLE
FLOWCHART
TIMELINE
CAUSE_EFFECT_DIAGRAM
HIERARCHY_TREE
EXAMPLE_CALLOUT
FORMULA_DISPLAY
```

### SelectedRepresentation
```python
{
    knowledge_id: str
    document_id: str
    primary_format: RepresentationFormat
    secondary_format: Optional[RepresentationFormat]
    selection_confidence: float  # 0.0-1.0
    selection_reasoning: str
    source_unit_ids: List[str]  # Preserved from original
    
    # Format-specific content (extracted from knowledge item)
    format_content: Dict[str, Any]
}
```

### RepresentationDocument
```python
{
    document_id: str
    source_filename: str
    representation_timestamp: str
    analysis_timestamp: str
    
    representations: List[SelectedRepresentation]
    statistics: RepresentationStatistics
}
```

### RepresentationStatistics
```python
{
    items_processed: int
    format_distribution: Dict[RepresentationFormat, int]
    confidence_distribution: Dict[str, int]  # high/medium/low/fallback
    items_with_secondary: int
    fallback_count: int
}
```

## Content Extraction Rules

Each format requires specific content fields extracted from the knowledge item:

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

### COMPARISON_TABLE
```python
{
    "items": List[str],
    "dimensions": List[str],
    "values": Dict[str, Dict[str, str]]  # item → dimension → value
}
```

### HIERARCHY_TREE
```python
{
    "root": str,
    "children": List[Dict[str, Any]]  # recursive structure
}
```

### TIMELINE
```python
{
    "events": List[Dict[str, str]],  # {"time": ..., "event": ...}
    "title": Optional[str]
}
```

### FORMULA_DISPLAY
```python
{
    "formula": str,
    "variables": Optional[Dict[str, str]],
    "conditions": Optional[str]
}
```

### STANDARD_TEXT
```python
{
    "content": str
}
```

## Implementation Constraints

### Must NOT
- Infer missing facts or relationships
- Generate comparison dimensions not present in content
- Fabricate steps, causes, effects, or hierarchy levels
- Call LLM or external services
- Modify original knowledge items
- Create new source mappings

### Must
- Preserve all source_unit_ids exactly
- Use deterministic selection (same input → same output)
- Default to STANDARD_TEXT when evidence is insufficient
- Log all selection decisions for transparency
- Validate content requirements before selecting non-text formats

## Testing Strategy

### Unit Tests (per format)
- Valid content → correct format selected
- Missing required fields → STANDARD_TEXT fallback
- Ambiguous cases → deterministic resolution
- Confidence scoring accuracy
- Content extraction correctness

### Integration Tests
- Full pipeline: extraction → analysis → representation
- Multiple characteristics → appropriate selection
- Provenance preservation
- Statistics accuracy

### Edge Cases
- Empty content
- Malformed knowledge items
- Conflicting characteristics
- Minimal Procedure (single step)
- Formula without variables
- Relationship without hierarchy

## Extensibility

New formats can be added by:
1. Adding enum value to `RepresentationFormat`
2. Defining content schema in `format_content`
3. Adding selection rule to `RepresentationSelector._select_format()`
4. Adding content extractor to `RepresentationSelector._extract_format_content()`
5. Adding unit tests for new format

No changes required to:
- Data models (generic `format_content` dict)
- Statistics calculation
- Provenance tracking
- Other formats

## Limitations

This layer does NOT:
- Render final output (HTML, PDF, etc.)
- Perform layout or styling decisions
- Handle personalization or learning preferences
- Track user interaction or performance
- Evaluate faithfulness or accuracy
- Generate adaptive variations

Those capabilities belong to future layers (Note Assembler, Personalization, etc.)
