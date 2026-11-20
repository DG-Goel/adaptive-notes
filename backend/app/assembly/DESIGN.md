# Note Assembler Layer - Design Document

## Purpose

The Note Assembler layer organizes selected representations into a coherent, readable sequence for presentation to learners. It bridges representation selection and final rendering.

## Position in Architecture

```
Ingestion → Extraction → Analysis → Representation → **Note Assembler** → Renderer
```

**Input**: `RepresentationDocument` (knowledge items with selected formats)  
**Output**: `AssembledNotesDocument` (organized, ordered items ready for rendering)

## Responsibilities

### Core Functions

1. **Accept representation document** - Load persisted JSON or in-memory object
2. **Validate input** - Ensure all required fields present, no corrupt data
3. **Organize items** - Group and order knowledge items logically
4. **Preserve provenance** - Maintain all IDs, source mappings, metadata
5. **Structure output** - Create sections with ordered items

### Organizational Strategy

**Primary: Section-based grouping** (when section metadata available)
- Group items by their section field from source documents
- Maintain original document ordering within sections
- Use source_unit_ids to determine relative position

**Secondary: Source-order fallback** (when sections unreliable)
- Order by minimum source_unit_id (lexicographic sort: S0001, S0002, etc.)
- Deterministic and reproducible

**Tertiary: ID-based fallback** (when no source metadata)
- Order by knowledge_id (CON_0001, DEF_0002, etc.)
- Ensures stable output for testing

### Grouping Rules

1. Items with same section → same output section
2. Items with null/empty section → "Main Content" default section
3. Preserve order of items within each group
4. Do not merge distinct knowledge items
5. Do not silently drop items
6. Do not reorder arbitrarily

## Data Models

### AssembledItem

```python
{
    knowledge_id: str
    document_id: str
    knowledge_type: str
    
    # Representation from selector
    primary_format: RepresentationFormat
    format_content: Dict[str, Any]
    secondary_format: Optional[RepresentationFormat]
    secondary_content: Optional[Dict[str, Any]]
    
    # Selection metadata
    selection_confidence: float
    confidence_label: str
    selection_reasoning: str
    
    # Provenance (preserved)
    source_unit_ids: List[str]
    
    # Ordering metadata
    position_in_section: int
    ordering_rationale: str  # "section-based", "source-order", "id-based"
}
```

### AssembledSection

```python
{
    section_id: str            # "section_0", "section_1", etc.
    section_name: str          # Original section name or "Main Content"
    section_type: str          # "named_section", "default_section"
    items: List[AssembledItem]
    item_count: int
}
```

### AssemblyMetadata

```python
{
    assembly_timestamp: str
    ordering_strategy: str     # "section-based", "source-order", "id-based"
    total_sections: int
    total_items: int
    items_with_section: int
    items_without_section: int
}
```

### AssembledNotesDocument

```python
{
    # Metadata
    document_id: str
    source_filename: str
    assembly_timestamp: str
    
    # Previous layer timestamps
    representation_timestamp: str
    analysis_timestamp: str
    extraction_timestamp: str
    
    # Organized content
    sections: List[AssembledSection]
    
    # Assembly metadata
    metadata: AssemblyMetadata
    
    # Statistics
    statistics: AssemblyStatistics
}
```

### AssemblyStatistics

```python
{
    total_sections: int
    total_items: int
    items_by_format: Dict[RepresentationFormat, int]
    items_by_confidence: Dict[str, int]
}
```

## Ordering Algorithm

### Step 1: Extract section information

```python
for rep in representations:
    section = extract_section(rep)
    sections_map[section].append(rep)
```

### Step 2: Determine ordering within sections

For each section:
```python
if all items have source_unit_ids:
    # Sort by minimum source_unit_id
    items.sort(key=lambda x: min(x.source_unit_ids))
else:
    # Fallback to knowledge_id
    items.sort(key=lambda x: x.knowledge_id)
```

### Step 3: Order sections

```python
# Named sections in alphabetical order (deterministic)
sections.sort(key=lambda s: s.section_name)

# Exception: "Main Content" always first
if "Main Content" in sections:
    move_to_front("Main Content")
```

## Section Extraction Strategy

### Priority 1: Knowledge item section field

Look for section in original knowledge item metadata (not directly in representation):
- Must reconstruct from source or pass through representation

### Priority 2: Infer from source_unit_ids

If knowledge extraction preserved section metadata, use it.

### Priority 3: Default section

Items without section → "Main Content"

## Content Integrity Constraints

### Must NOT

❌ Invent explanations or transitions between items  
❌ Rewrite or summarize content  
❌ Change representation formats  
❌ Fabricate missing fields in format_content  
❌ Lose source provenance  
❌ Silently drop items  
❌ Generate headings that imply unsupported content  

### Must

✅ Preserve all knowledge_id, document_id, source_unit_ids exactly  
✅ Preserve format_content without modification  
✅ Preserve selection metadata (confidence, reasoning)  
✅ Use deterministic ordering (same input → same output)  
✅ Handle empty documents gracefully  
✅ Handle missing metadata safely (use defaults)  
✅ Detect and report duplicate IDs  
✅ Allow distinct items with identical content (if IDs differ)  

## Error Handling

### Empty Input
- Empty representations list → Empty sections list
- Return valid AssembledNotesDocument with 0 items
- Do not error or return None

### Missing Section Metadata
- Use "Main Content" default section
- Log rationale in ordering_rationale field
- Continue processing

### Duplicate knowledge_id
- Log warning
- Include both items (they may differ in other fields)
- Use position to distinguish

### Missing source_unit_ids
- Fallback to knowledge_id ordering
- Document in ordering_rationale
- Continue processing

## Output Format

**Structured JSON** ready for persistence or rendering.

**Not included:**
- HTML generation
- PDF generation
- Markdown rendering
- Diagram drawing
- CSS styling
- Interactive elements
- Personalization
- Learning analytics

Those belong in future layers (Renderer, Personalization).

## Testing Strategy

### Unit Tests
- Normal assembly (8 items → sections)
- Section grouping logic
- Deterministic ordering (repeated runs)
- Empty input handling
- Missing section metadata
- Duplicate knowledge_ids
- Identical content, different IDs
- Source-order vs ID-order
- Provenance preservation

### Integration Tests
- Full pipeline: load representations JSON → assemble → save
- Round-trip: assemble → serialize → deserialize → verify
- Item count preservation

### Edge Cases
- All items have same section
- All items have different sections
- Mix of null and non-null sections
- Items with overlapping source_unit_ids
- Items with no source_unit_ids

## Extensibility

Future enhancements (not implemented now):
- Topical clustering (ML-based)
- Dependency-based ordering (concept before example)
- Difficulty-based ordering (simple to complex)
- User preference-based ordering
- Dynamic section generation
- Cross-references between items

## Known Limitations

This layer does NOT:
- Render visual output
- Generate transitions or narrative flow
- Perform content summarization
- Handle multi-document assembly
- Support interactive reorganization
- Evaluate pedagogical effectiveness

Those are explicitly out of scope for this layer.
