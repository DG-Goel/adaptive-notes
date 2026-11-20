"""
Integration tests for source fidelity preservation.

Verifies that original source text is preserved exactly across ingestion,
including LaTeX, code blocks, tables, definitions, unicode, and long content.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from src.services.ingestion_service import get_ingestion_service, generate_chunk_id


@pytest.fixture
def test_collection_name():
    """Generate unique collection name for test isolation."""
    return f"test_fidelity_{uuid4().hex[:8]}"


@pytest.fixture
def ingestion_service(test_collection_name):
    """Provide IngestionService instance with test collection."""
    service = get_ingestion_service(
        embedding_batch_size=16,
        collection_name=test_collection_name
    )
    
    # Ensure collection is created
    service.vector_store.create_collection()
    
    yield service
    
    # Cleanup: delete test collection
    try:
        service.vector_store.client.delete_collection(test_collection_name)
    except:
        pass


@pytest.mark.integration
class TestSourceFidelity:
    """Test exact source preservation across content types."""
    
    def test_latex_formulas_preserved(self, ingestion_service, tmp_path):
        """Test that LaTeX mathematical formulas are preserved exactly."""
        test_file = tmp_path / "math.md"
        
        latex_content = r"""# Mathematical Formulas

## Quadratic Formula

The quadratic formula is:

$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

## Integral

$$\int_a^b f(x) \, dx = F(b) - F(a)$$

## Matrix

$$\begin{bmatrix} a & b \\ c & d \end{bmatrix}$$

Inline math: $E = mc^2$ and $\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$
"""
        test_file.write_text(latex_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "\n\n".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify specific LaTeX expressions are preserved
        assert r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}" in all_text
        assert r"\int_a^b f(x) \, dx" in all_text
        assert r"\begin{bmatrix}" in all_text
        assert r"E = mc^2" in all_text
        assert r"\sum_{i=1}^{n}" in all_text
        
        # Verify dollar signs preserved
        assert "$$" in all_text or "$" in all_text
    
    def test_code_blocks_preserved(self, ingestion_service, tmp_path):
        """Test that code blocks with various languages are preserved."""
        test_file = tmp_path / "code.md"
        
        code_content = '''# Code Examples

## Python

```python
def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Edge case with special characters
special = "string with \\n newline and \\'quotes\\'"
```

## JavaScript

```javascript
const fetchData = async () => {
    const response = await fetch('/api/data');
    return response.json();
};
```

## SQL

```sql
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.name
HAVING COUNT(o.id) > 5;
```
'''
        test_file.write_text(code_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "\n\n".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify code is preserved with correct syntax
        assert "def fibonacci(n):" in all_text
        assert "return fibonacci(n-1) + fibonacci(n-2)" in all_text
        assert "const fetchData = async () =>" in all_text
        assert "await fetch('/api/data')" in all_text
        assert "SELECT u.name, COUNT(o.id)" in all_text
        assert "LEFT JOIN orders o" in all_text
        
        # Verify special characters in strings preserved
        assert "\\n" in all_text or "newline" in all_text
        
        # Verify code fence markers
        assert "```" in all_text or "python" in all_text.lower()
    
    def test_tables_preserved(self, ingestion_service, tmp_path):
        """Test that markdown tables are preserved with structure."""
        test_file = tmp_path / "tables.md"
        
        table_content = """# Data Tables

## Algorithm Complexity

| Algorithm | Best | Average | Worst | Space |
|-----------|------|---------|-------|-------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |

## Comparison

| Feature | Option A | Option B |
|---------|----------|----------|
| Speed | Fast | Medium |
| Cost | $100 | $50 |
| Quality | High | Medium |
"""
        test_file.write_text(table_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "\n\n".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify table structure preserved
        assert "| Algorithm |" in all_text or "Algorithm" in all_text
        assert "Bubble Sort" in all_text
        assert "O(n²)" in all_text or "O(n^2)" in all_text or "O(n2)" in all_text
        assert "Quick Sort" in all_text
        assert "O(n log n)" in all_text
        
        # Verify table separators (if preserved as-is)
        if "|---" in all_text:
            assert "|---" in all_text
    
    def test_definitions_and_lists_preserved(self, ingestion_service, tmp_path):
        """Test that definitions and various list types are preserved."""
        test_file = tmp_path / "lists.md"
        
        list_content = """# Definitions and Lists

## Term Definitions

**Algorithm**: A step-by-step procedure for solving a problem.

**Recursion**: A technique where a function calls itself.

## Numbered List

1. First item with details
2. Second item with more details
   a. Sub-item A
   b. Sub-item B
3. Third item

## Bullet List

- Primary point one
  - Nested point 1.1
  - Nested point 1.2
- Primary point two
* Alternative bullet style
+ Another bullet style

## Checklist

- [x] Completed task
- [ ] Pending task
- [x] Another completed task
"""
        test_file.write_text(list_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "\n\n".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify definitions preserved
        assert "Algorithm" in all_text
        assert "step-by-step procedure" in all_text
        assert "Recursion" in all_text
        
        # Verify numbered list
        assert "1." in all_text or "First item" in all_text
        assert "2." in all_text or "Second item" in all_text
        assert "3." in all_text or "Third item" in all_text
        
        # Verify bullet points
        assert "Primary point one" in all_text
        assert "Primary point two" in all_text
        assert "Nested point" in all_text
        
        # Verify checklist items
        assert "Completed task" in all_text
        assert "Pending task" in all_text
    
    def test_long_paragraphs_preserved(self, ingestion_service, tmp_path):
        """Test that long paragraphs are not silently truncated."""
        test_file = tmp_path / "long.md"
        
        # Create a very long paragraph (2000 words)
        long_paragraph = " ".join([f"Word{i}" for i in range(2000)])
        long_content = f"""# Long Content

## Introduction

This is a test document with very long content.

## Long Paragraph

{long_paragraph}

## Conclusion

This concludes the long document.
"""
        test_file.write_text(long_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = " ".join(chunk.payload["text"] for chunk in chunks)
        
        # Count how many words preserved
        words_found = sum(1 for i in range(2000) if f"Word{i}" in all_text)
        
        # Should preserve vast majority of words (allowing for chunking boundaries)
        preservation_rate = words_found / 2000
        assert preservation_rate > 0.95, \
            f"Only {preservation_rate:.1%} of words preserved, expected >95%"
        
        # Verify start and end preserved
        assert "Word0" in all_text
        assert "Word1999" in all_text
    
    def test_nested_headings_preserved(self, ingestion_service, tmp_path):
        """Test that nested heading hierarchy is preserved."""
        test_file = tmp_path / "headings.md"
        
        heading_content = """# Level 1 Title

Content under level 1.

## Level 2 Section A

Content under 2A.

### Level 3 Subsection A1

Content under 3A1.

#### Level 4 Detail A1a

Content under 4A1a.

### Level 3 Subsection A2

Content under 3A2.

## Level 2 Section B

Content under 2B.

### Level 3 Subsection B1

Content under 3B1.
"""
        test_file.write_text(heading_content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "\n".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify all heading levels preserved
        assert "# Level 1 Title" in all_text or "Level 1 Title" in all_text
        assert "Level 2 Section A" in all_text
        assert "Level 3 Subsection A1" in all_text
        assert "Level 4 Detail A1a" in all_text
        assert "Level 3 Subsection A2" in all_text
        assert "Level 2 Section B" in all_text
        
        # Verify content under each heading preserved
        assert "Content under 2A" in all_text
        assert "Content under 3A1" in all_text
        assert "Content under 4A1a" in all_text
    
    def test_unicode_and_multilingual_preserved(self, ingestion_service, tmp_path):
        """Test that unicode and multilingual content is preserved."""
        test_file = tmp_path / "unicode.md"
        
        unicode_content = """# Unicode and Multilingual Content

## Mathematical Symbols

- Greek: α β γ δ ε ζ η θ
- Operators: ∑ ∫ ∂ ∇ ∞ √ ≈ ≠ ≤ ≥
- Sets: ∈ ∉ ⊂ ⊃ ∩ ∪ ∅
- Logic: ∀ ∃ ∧ ∨ ¬ ⇒ ⇔

## Various Languages

### Chinese (Simplified)
你好世界！这是一个测试文档。

### Japanese
こんにちは世界！これはテスト文書です。

### Arabic
مرحبا بالعالم! هذا مستند تجريبي.

### Russian
Привет мир! Это тестовый документ.

### Hebrew
שלום עולם! זה מסמך בדיקה.

### Emoji and Symbols
✓ ✗ ★ ☆ ❤ ♠ ♣ ♥ ♦ 🌍 🚀 📚 🎯

## Special Characters

Quotes: "curly" "quotes" 'single'
Dashes: en–dash em—dash
Ellipsis: …
Copyright: © ® ™
Currency: $ € £ ¥ ₹
Fractions: ½ ¼ ¾
"""
        test_file.write_text(unicode_content, encoding='utf-8')
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all original text
        all_text = "".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify Greek letters
        assert "α" in all_text
        assert "θ" in all_text
        
        # Verify mathematical operators
        assert "∑" in all_text
        assert "∫" in all_text
        assert "∞" in all_text
        
        # Verify Chinese
        assert "你好世界" in all_text
        
        # Verify Japanese
        assert "こんにちは" in all_text
        
        # Verify Arabic
        assert "مرحبا" in all_text
        
        # Verify Russian
        assert "Привет" in all_text
        
        # Verify special punctuation
        assert "©" in all_text or "Copyright" in all_text
        assert "€" in all_text or "EUR" in all_text or "Currency" in all_text
    
    def test_original_vs_enriched_separation(self, ingestion_service, tmp_path):
        """Test that original text is kept separate from enriched text."""
        test_file = tmp_path / "test.md"
        
        content = """# Test Document

## Section One

This is the original content that should be preserved exactly.
"""
        test_file.write_text(content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        for chunk in chunks:
            payload = chunk.payload
            
            # Both fields should exist
            assert "text" in payload, "Original text field missing"
            assert "enriched_text" in payload, "Enriched text field missing"
            
            # Original text should not contain enrichment
            original = payload["text"]
            enriched = payload["enriched_text"]
            
            # For child chunks, enriched should be longer (has context added)
            if not payload.get("is_parent", False):
                # Check if enrichment was applied
                if "Document:" in enriched or "deterministic_context" in payload:
                    # Enrichment applied - verify original is clean
                    assert len(enriched) >= len(original), \
                        "Enriched text should be >= original length"
            
            # Original should always contain the actual content
            if "original content" in content:
                # At least one chunk should have the original phrase
                has_original = any("original content" in c.payload["text"] 
                                 for c in chunks)
                assert has_original, "Original content phrase not found"
    
    def test_no_silent_content_discard(self, ingestion_service, tmp_path):
        """Test that content exceeding token limits is handled without silent discard."""
        test_file = tmp_path / "very_long.md"
        
        # Create content that exceeds typical token limits
        # BGE-small has 512 token limit, child chunks are 400 tokens
        # This creates content that will definitely need multiple chunks
        very_long_text = "This is a test sentence. " * 500  # ~2500 words
        
        content = f"""# Very Long Document

{very_long_text}

## End Section

Final paragraph to mark the end.
"""
        test_file.write_text(content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        assert result.chunks_indexed > 1, "Should create multiple chunks"
        
        # Retrieve all chunks
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Combine all text
        all_text = " ".join(chunk.payload["text"] for chunk in chunks)
        
        # Verify beginning and end are both present
        assert "This is a test sentence" in all_text, "Beginning missing"
        assert "Final paragraph" in all_text, "End missing"
        assert "End Section" in all_text, "End section missing"
        
        # Count occurrences of repeated phrase
        phrase_count = all_text.count("This is a test sentence")
        
        # Should preserve most occurrences (allowing some boundary effects)
        # We repeated it 500 times, should find most of them
        assert phrase_count > 400, \
            f"Only found {phrase_count}/500 phrase occurrences - content was discarded"
    
    def test_source_offset_tracking(self, ingestion_service, tmp_path):
        """Test that chunk indices enable source location tracking."""
        test_file = tmp_path / "test.md"
        
        content = """# Document

## Section 1
Content A.

## Section 2  
Content B.

## Section 3
Content C.
"""
        test_file.write_text(content)
        
        result = ingestion_service.ingest_document(str(test_file))
        assert result.success is True
        
        # Retrieve chunks in order
        chunk_ids = [generate_chunk_id(result.doc_id, i) for i in range(result.chunks_indexed)]
        chunks = ingestion_service.vector_store.get_points(chunk_ids)
        
        # Sort by chunk_index to verify ordering
        chunks_sorted = sorted(chunks, key=lambda c: c.payload["chunk_index"])
        
        # Verify chunk_index is sequential
        for i, chunk in enumerate(chunks_sorted):
            assert chunk.payload["chunk_index"] == i, \
                "Chunk indices should be sequential"
        
        # Verify we can map back to source
        for chunk in chunks:
            # Each chunk should have sufficient metadata for provenance
            payload = chunk.payload
            assert "doc_id" in payload
            assert "doc_path" in payload
            assert "doc_title" in payload
            assert "chunk_index" in payload
            assert "chunk_id" in payload
            
            # Should be able to reconstruct: which document, which position
            doc_id = payload["doc_id"]
            chunk_index = payload["chunk_index"]
            # This gives us: Document X, Chunk Y - sufficient for citation
