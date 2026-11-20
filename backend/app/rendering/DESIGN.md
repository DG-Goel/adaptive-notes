# Renderer v1 - Design Document

## Purpose

The Renderer v1 layer converts an `AssembledNotesDocument` into readable, deterministic Markdown notes with full provenance tracking.

## Position in Architecture

```
Ingestion → Extraction → Analysis → Representation → Assembly → **Renderer v1** → Output
```

**Input**: `AssembledNotesDocument` (organized sections with ordered items)  
**Output**: Markdown text + Render Manifest (provenance mapping)

## Responsibilities

### Core Functions

1. **Convert to Markdown** - Transform assembled notes into readable Markdown
2. **Render all formats** - Support every defined representation format
3. **Preserve ordering** - Maintain section and item order from assembly
4. **Track provenance** - Map every rendered element to knowledge IDs and source units
5. **Handle edge cases** - Empty documents, missing fields, malformed payloads
6. **Deterministic output** - Same input always produces same output

### Format-Specific Rendering

#### STANDARD_TEXT
```markdown
{content}

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### DEFINITION_BOX
```markdown
### {term}

{definition}

{context if present}

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### EXAMPLE_CALLOUT
```markdown
> **Example: {exemplifies}**
> 
> {example_text}

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### FLOWCHART
```markdown
#### Flowchart: {procedure_name if present}

```mermaid
flowchart TD
    A[{step_1}] --> B[{step_2}]
    B --> C[{step_3}]
    ...
```

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### TIMELINE
```markdown
#### Timeline: {title if present}

1. **{event_1_time}**: {event_1_text}
2. **{event_2_time}**: {event_2_text}
...

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### CAUSE_EFFECT_DIAGRAM
```markdown
#### Cause and Effect

```mermaid
flowchart LR
    A[{cause}] -->|{mechanism if present}| B[{effect}]
```

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### HIERARCHY_TREE
```markdown
#### Hierarchy: {root}

- {root}
  - {child_1}
    - {child_1_1}
  - {child_2}

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### COMPARISON_TABLE
```markdown
#### Comparison: {items}

| Dimension | {item_1} | {item_2} | ... |
|-----------|----------|----------|-----|
| {dim_1}   | {val_11} | {val_12} | ... |
| {dim_2}   | {val_21} | {val_22} | ... |

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

#### FORMULA_DISPLAY
```markdown
#### Formula

{formula_text}

{variables if present}

*[Knowledge ID: {knowledge_id} | Sources: {source_unit_ids}]*
```

## Fallback Behavior

### Missing Required Fields

**FLOWCHART** without steps → Render as text:
```markdown
{procedure_name if present}

*Unable to generate flowchart: insufficient data*
```

**COMPARISON_TABLE** without dimensions → Render as text list

**CAUSE_EFFECT_DIAGRAM** without cause/effect → Render mechanism as text

**HIERARCHY_TREE** without children → Render as simple item

### Malformed Payloads

- Log warning
- Render available fields as text
- Include note about incomplete data
- Never crash or skip item

## Markdown Escaping

### What to Escape
- Markdown special characters in content: `*`, `_`, `#`, `[`, `]`, `<`, `>`
- BUT NOT in:
  - Formulas (preserve mathematical notation)
  - Code blocks (already escaped)
  - Mermaid diagrams (preserve syntax)

### Escape Function
```python
def escape_markdown(text: str, preserve_formulas: bool = False) -> str:
    if preserve_formulas:
        # Only escape basic characters, preserve math
        return text.replace('[', '\\[').replace(']', '\\]')
    else:
        # Full escape
        return text.replace('\\', '\\\\')
                   .replace('*', '\\*')
                   .replace('_', '\\_')
                   .replace('[', '\\[')
                   .replace(']', '\\]')
```

## Provenance Tracking

### Render Manifest

```python
{
    "document_id": str,
    "source_filename": str,
    "render_timestamp": str,
    "markdown_length": int,
    "items_rendered": List[RenderedItem],
    "warnings": List[RenderWarning]
}
```

### RenderedItem

```python
{
    "knowledge_id": str,
    "source_unit_ids": List[str],
    "format_rendered": RepresentationFormat,
    "line_start": int,  # Line number in markdown where this item starts
    "line_end": int,    # Line number where this item ends
    "rendering_status": "complete" | "partial" | "fallback",
    "fallback_reason": Optional[str]
}
```

### RenderWarning

```python
{
    "knowledge_id": str,
    "warning_type": "missing_field" | "malformed_payload" | "unsupported_format",
    "message": str
}
```

## Content Integrity

### Must NOT

❌ Invent content (headings, explanations, examples, data)  
❌ Modify or summarize source text  
❌ Change representation formats  
❌ Fabricate missing fields  
❌ Skip items silently  
❌ Alter formula meaning  

### Must

✅ Render every item from input  
✅ Preserve exact text from format_content  
✅ Use selected format from assembly  
✅ Track provenance for every rendered element  
✅ Handle missing fields safely with fallbacks  
✅ Provide deterministic output  
✅ Log all warnings  

## Error Handling

### Empty Document
- Return valid Markdown with header and no content
- Empty manifest with 0 items

### Empty Section
- Render section heading
- Note "No items in this section"

### Missing Optional Fields
- Use sensible defaults ("Untitled" for missing names)
- Continue rendering

### Malformed Format Content
- Log warning
- Render available fields
- Add note about incomplete data

### Unsupported Format (future-proofing)
- Log warning
- Render as STANDARD_TEXT fallback
- Track in manifest

## Output Structure

### Markdown File

```markdown
# {source_filename}

*Generated from assembled notes*

---

## {section_name_1}

{rendered_item_1}

{rendered_item_2}

...

## {section_name_2}

...

---

*Render complete: {item_count} items from {section_count} sections*
```

### Render Manifest (JSON)

Separate file tracking provenance and warnings.

## Testing Strategy

### Unit Tests
- Each format with valid data
- Each format with missing optional fields
- Each format with malformed data
- Empty documents and sections
- Markdown escaping
- Mermaid syntax generation
- Provenance tracking
- Warning generation

### Integration Tests
- Full pipeline: load assembled notes → render → verify
- Deterministic output (repeated runs)
- Manifest accuracy

### Edge Cases
- Formula preservation
- Special characters in text
- Empty format_content
- Null fields
- Very long content
- Unicode characters

## Known Limitations

This layer does NOT:
- Generate PDF output
- Apply styling or CSS
- Create interactive elements
- Render images or media
- Support custom templates
- Personalize content
- Track user engagement

Those belong to future layers or separate rendering pipelines.

## Extensibility

Future enhancements (not implemented now):
- PDF export
- HTML rendering
- Custom templates
- Theme support
- Interactive diagrams
- Multi-format output
- Conditional rendering based on user preferences
