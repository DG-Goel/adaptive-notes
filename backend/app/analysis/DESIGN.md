# Content Analysis Layer - Design Document

**Version:** 1.0  
**Date:** October 18, 2026  
**Status:** Implementation Ready

---

## Purpose

The Content Analysis layer identifies **structural characteristics** of extracted knowledge items to inform representation selection without choosing specific visual formats.

**Key Principles:**
1. **Rule-based** - No LLM calls, fully deterministic
2. **Provenance-preserving** - All source IDs maintained
3. **Evidence-based** - Only assign characteristics supported by content
4. **Multiple assignments** - Items can have multiple characteristics
5. **Explicit uncertainty** - Unknown or insufficient-evidence states supported

---

## Scope

### In Scope ✅
- Analyze existing KnowledgeItems (Concept, Definition, Explanation, etc.)
- Identify structural characteristics from content and type
- Preserve all source traceability
- Support ambiguous/multiple classifications
- Handle insufficient evidence explicitly

### Out of Scope ❌
- Choosing visual representations (that's Representation Selector)
- Generating diagrams, tables, or notes
- Modifying extracted knowledge
- LLM-based semantic analysis
- Quality scoring or ranking

---

## Data Model

### ContentCharacteristics (Enum)
```python
DEFINITION           # Defines what something is
SEQUENCE             # Ordered steps or stages
COMPARISON           # Contrasts or compares items
CAUSE_EFFECT         # Causal relationships
HIERARCHY            # Parent-child or categorical structure
RELATIONSHIP         # General connections between concepts
FACTUAL_EXPLANATION  # Describes how/why with facts
EXAMPLE              # Illustrates a concept
UNKNOWN              # Cannot classify with confidence
```

### AnalyzedKnowledge (extends KnowledgeItem)
```python
class AnalyzedKnowledge:
    # Original knowledge item (unchanged)
    knowledge_item: KnowledgeItem
    
    # Assigned characteristics
    characteristics: List[ContentCharacteristics]
    
    # Confidence in assignment
    analysis_confidence: Literal["high", "medium", "low", "insufficient"]
    
    # Reasoning (for debugging/transparency)
    analysis_reasoning: str
    
    # Provenance (inherited from knowledge_item)
    # source_unit_ids, document_id preserved
```

---

## Analysis Rules

### Rule-Based Classification Strategy

#### 1. Type-Based Rules (High Confidence)

**Definition → DEFINITION**
- Knowledge type: Definition
- Has: term, definition_text
- Confidence: HIGH
- Reasoning: "Explicit definition structure"

**Example → EXAMPLE**
- Knowledge type: Example
- Has: exemplifies, example_text
- Confidence: HIGH
- Reasoning: "Explicit example structure"

**Procedure → SEQUENCE**
- Knowledge type: Procedure
- Has: steps (ordered list)
- Confidence: HIGH
- Reasoning: "Explicit sequential steps"

**Relationship → determined by relationship_type**
- "is_a" → HIERARCHY
- "part_of" → HIERARCHY
- "causes" → CAUSE_EFFECT
- "requires" → RELATIONSHIP
- "contrasts_with" → COMPARISON
- "exemplifies" → EXAMPLE

#### 2. Content-Based Rules (Medium Confidence)

**Explanation → multiple possibilities**
```
IF explanation_type == "causal":
    → CAUSE_EFFECT + FACTUAL_EXPLANATION
    
IF explanation_type == "procedural":
    → SEQUENCE + FACTUAL_EXPLANATION
    
IF explanation_type == "functional":
    → FACTUAL_EXPLANATION
    
IF explanation_type is None:
    Check content for keywords:
    - "because", "therefore", "causes" → CAUSE_EFFECT
    - "first", "then", "next", "finally" → SEQUENCE
    - "compared to", "versus", "while" → COMPARISON
    - else → FACTUAL_EXPLANATION
```

**Concept → inferred from context**
```
IF has aliases:
    → DEFINITION (implicit definition via equivalence)
    
IF content contains comparative language:
    → COMPARISON
    
ELSE:
    → UNKNOWN (needs more context)
```

**Fact → FACTUAL_EXPLANATION**
- Knowledge type: Fact
- Confidence: MEDIUM (facts can also be definitions or examples)
- Check fact_type:
  - "historical" → FACTUAL_EXPLANATION
  - "biographical" → FACTUAL_EXPLANATION
  - "statistical" → Could be COMPARISON

#### 3. Composite Rules

**Multiple characteristics when:**
```
Explanation + causal type:
  → [CAUSE_EFFECT, FACTUAL_EXPLANATION]
  
Definition + has relationships:
  → [DEFINITION, HIERARCHY]
  
Procedure + describes why:
  → [SEQUENCE, FACTUAL_EXPLANATION]
```

#### 4. Insufficient Evidence

Assign `UNKNOWN` with `insufficient` confidence when:
- Content is too brief (<10 words)
- No clear structural markers
- Ambiguous type (e.g., Concept without context)
- Conflicting signals

---

## Implementation Strategy

### Class Structure
```
app/analysis/
├── __init__.py
├── analyzer.py          # Main ContentAnalyzer class
├── rules.py             # Classification rules
└── characteristics.py   # Enum and AnalyzedKnowledge model
```

### ContentAnalyzer Class
```python
class ContentAnalyzer:
    def analyze(self, knowledge_doc: KnowledgeDocument) -> AnalyzedKnowledgeDocument:
        """Analyze all knowledge items"""
        
    def _analyze_item(self, item: KnowledgeItem) -> AnalyzedKnowledge:
        """Analyze single knowledge item"""
        
    def _apply_type_rules(self, item) -> List[ContentCharacteristics]:
        """Apply type-based rules (high confidence)"""
        
    def _apply_content_rules(self, item) -> List[ContentCharacteristics]:
        """Apply content-based rules (medium confidence)"""
        
    def _determine_confidence(self, characteristics, item) -> str:
        """Determine analysis confidence level"""
```

### Rule Engine
```python
class ClassificationRule:
    def matches(self, item: KnowledgeItem) -> bool:
        """Check if rule applies"""
        
    def classify(self, item: KnowledgeItem) -> List[ContentCharacteristics]:
        """Return characteristics"""
        
    def confidence(self) -> str:
        """Rule confidence level"""
```

---

## Test Strategy

### Unit Tests Required

1. **Type-Based Classification**
   - test_definition_gets_DEFINITION
   - test_example_gets_EXAMPLE
   - test_procedure_gets_SEQUENCE
   - test_relationship_hierarchy_gets_HIERARCHY
   - test_relationship_causes_gets_CAUSE_EFFECT

2. **Content-Based Classification**
   - test_causal_explanation_gets_CAUSE_EFFECT
   - test_procedural_explanation_gets_SEQUENCE
   - test_comparison_keywords_detected
   - test_sequence_keywords_detected

3. **Multiple Characteristics**
   - test_causal_explanation_gets_both_characteristics
   - test_procedural_explanation_gets_both_characteristics

4. **Ambiguous Cases**
   - test_concept_without_aliases_gets_UNKNOWN
   - test_short_content_flagged_insufficient
   - test_no_clear_markers_gets_UNKNOWN

5. **Provenance Preservation**
   - test_source_ids_preserved
   - test_document_id_preserved
   - test_original_item_unchanged

6. **Edge Cases**
   - test_empty_content_handled
   - test_multiple_relationships_handled
   - test_mixed_signals_handled

7. **Regression**
   - test_all_knowledge_types_processable
   - test_no_items_lost_during_analysis

---

## Example Scenarios

### Scenario 1: Clear Definition
```python
Input:
  Definition(
    term="short story",
    definition_text="A prose narrative of limited length",
    source_unit_ids=["S0010"]
  )

Output:
  AnalyzedKnowledge(
    characteristics=[DEFINITION],
    analysis_confidence="high",
    reasoning="Explicit definition structure"
  )
```

### Scenario 2: Causal Explanation
```python
Input:
  Explanation(
    topic="dream impact",
    explanation_text="The dream caused him to leave Vienna",
    explanation_type="causal",
    source_unit_ids=["S0020", "S0021"]
  )

Output:
  AnalyzedKnowledge(
    characteristics=[CAUSE_EFFECT, FACTUAL_EXPLANATION],
    analysis_confidence="high",
    reasoning="Causal explanation type with explicit cause-effect"
  )
```

### Scenario 3: Ambiguous Concept
```python
Input:
  Concept(
    concept_name="Vienna",
    content="A city",
    aliases=[],
    source_unit_ids=["S0015"]
  )

Output:
  AnalyzedKnowledge(
    characteristics=[UNKNOWN],
    analysis_confidence="insufficient",
    reasoning="Minimal context, no structural markers"
  )
```

### Scenario 4: Procedure with Multiple Characteristics
```python
Input:
  Procedure(
    procedure_name="dream interpretation method",
    steps=["Listen to dream", "Identify symbols", "Provide meaning"],
    source_unit_ids=["S0025"]
  )

Output:
  AnalyzedKnowledge(
    characteristics=[SEQUENCE, FACTUAL_EXPLANATION],
    analysis_confidence="high",
    reasoning="Ordered steps (sequence) describing a process (explanation)"
  )
```

---

## Success Criteria

### Must Have ✅
- [ ] All knowledge types can be analyzed
- [ ] Provenance preserved (source_ids, document_id)
- [ ] Multiple characteristics supported
- [ ] UNKNOWN state for ambiguous cases
- [ ] Confidence levels assigned correctly
- [ ] 15+ unit tests, all passing
- [ ] Deterministic (same input → same output)
- [ ] No LLM calls

### Nice to Have (Future)
- Confidence scoring based on multiple signals
- Learning from user feedback
- Custom rule addition via configuration
- Statistical analysis of characteristic distribution

---

## Integration Points

### Input
```python
KnowledgeDocument (from extraction layer)
  ├─ concepts: List[Concept]
  ├─ definitions: List[Definition]
  ├─ explanations: List[Explanation]
  └─ ... (other types)
```

### Output
```python
AnalyzedKnowledgeDocument
  ├─ analyzed_items: List[AnalyzedKnowledge]
  ├─ document_id: str
  ├─ source_filename: str
  ├─ analysis_timestamp: str
  └─ statistics: AnalysisStatistics
```

### Next Layer (Representation Selector)
```python
# Representation Selector will use characteristics to choose formats
# Example:
#   DEFINITION → definition box
#   SEQUENCE → numbered list or flowchart
#   CAUSE_EFFECT → cause-effect diagram
#   COMPARISON → comparison table
```

---

## Non-Goals

- ❌ Choosing visual formats (that's Representation Selector)
- ❌ Generating actual diagrams or notes
- ❌ Semantic quality scoring
- ❌ Content validation or fact-checking
- ❌ Relationship discovery (that's extraction)
- ❌ Knowledge graph construction

---

## Summary

The Content Analysis layer:
1. Takes extracted knowledge items
2. Identifies structural characteristics using rules
3. Assigns 1+ characteristics per item
4. Maintains provenance throughout
5. Handles ambiguity explicitly
6. Outputs analyzed items for representation selection

**Key: This layer IDENTIFIES structure, it doesn't CHOOSE representations.**

---

**Design Status:** ✅ Ready for Implementation
