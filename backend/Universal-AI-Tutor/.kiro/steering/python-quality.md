# Python Code Quality Standards

## Code Style

### Type Hints
- Use type hints for ALL function parameters and return values
- Use `typing` module for complex types (`Optional`, `Union`, `List`, `Dict`, etc.)
- Use `TypedDict` for structured dictionaries
- Example:
```python
from typing import Optional, List
from pydantic import BaseModel

def process_chunks(
    text: str, 
    max_size: int = 800,
    metadata: Optional[dict] = None
) -> List[dict]:
    ...
```

### Docstrings
- Use Google-style docstrings for all public functions and classes
- Include Args, Returns, Raises sections
- Example:
```python
def hybrid_retrieve(query: str, top_k: int = 5) -> List[RetrievalResult]:
    """
    Perform hybrid retrieval combining dense and BM25 search.
    
    Args:
        query: Natural language query string
        top_k: Number of results to return (default: 5)
        
    Returns:
        List of RetrievalResult objects sorted by relevance
        
    Raises:
        QdrantConnectionError: If vector database is unavailable
        ValueError: If query is empty or top_k < 1
    """
    ...
```

### Error Handling
- Use specific exception types, not bare `except:`
- Log errors before re-raising
- Provide context in error messages
- Example:
```python
try:
    results = qdrant_client.search(...)
except QdrantException as e:
    logger.error(f"Qdrant search failed: {e}", exc_info=True)
    raise VectorStoreError(f"Failed to search vectors: {str(e)}") from e
```

### Logging
- Use structured logging with context
- Include request IDs for traceability
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Example:
```python
logger.info(
    "Hybrid retrieval completed",
    extra={
        "query_length": len(query),
        "results_count": len(results),
        "duration_ms": duration * 1000,
        "request_id": request_id
    }
)
```

## Code Organization

### Module Structure
- Keep modules focused and single-purpose
- Maximum 500 lines per file (prefer smaller)
- Group related functionality
- Use `__init__.py` to expose public API

### Dependency Management
- Import standard library first
- Then third-party libraries
- Then local modules
- Use absolute imports from project root

### Configuration
- ALL configuration via environment variables
- Use Pydantic Settings for validation
- Never hardcode API keys, URLs, or magic numbers
- Document all config vars in `.env.example`

## Testing Standards

### Test Coverage
- Minimum 80% coverage for core logic
- 100% coverage for critical paths (retrieval, generation, citation)
- Test both success and failure cases
- Test edge cases and boundary conditions

### Test Organization
```python
# tests/core/test_embedding_service.py
import pytest
from src.core.embedding_service import EmbeddingService

@pytest.fixture
def embedding_service():
    return EmbeddingService(model_name="test-model")

def test_embed_single_text(embedding_service):
    """Test embedding generation for single text."""
    text = "This is a test."
    embedding = embedding_service.embed(text)
    
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)

def test_embed_empty_text_raises_error(embedding_service):
    """Test that empty text raises ValueError."""
    with pytest.raises(ValueError, match="Text cannot be empty"):
        embedding_service.embed("")
```

### Mocking External Services
- Mock Groq API calls
- Mock Qdrant for unit tests (use real for integration)
- Use `pytest-mock` or `unittest.mock`
- Provide realistic mock responses

## Performance Guidelines

### Async Operations
- Use `async/await` for I/O-bound operations (API calls, DB queries)
- Do NOT use async for CPU-bound operations (embedding generation)
- Example:
```python
async def retrieve_and_rerank(query: str) -> List[dict]:
    # I/O-bound: use async
    results = await qdrant_client.search_async(...)
    
    # CPU-bound: use sync
    reranked = reranker.rerank(query, results)
    
    return reranked
```

### Batching
- Batch embedding generation (32-64 per batch)
- Batch database operations when possible
- Balance batch size vs. memory usage

### Caching
- Cache embeddings for repeated queries
- Cache model instances (singleton pattern)
- Use LRU cache for expensive operations
- Set reasonable cache sizes

## RAG-Specific Guidelines

### Source Traceability
- ALWAYS preserve source metadata through the entire pipeline
- Every chunk must be traceable to original document and position
- Include source references in all intermediate representations

### Citation Accuracy
- Verify citations match retrieved content
- Never fabricate sources
- Admit when information is not available
- Example:
```python
# GOOD
if not retrieved_chunks:
    return "I don't have enough information in your notes to answer this question."

# BAD
if not retrieved_chunks:
    # Still generate an answer anyway (NEVER DO THIS)
    return llm.generate(question)
```

### Chunk Boundaries
- Never split code blocks, formulas, or tables
- Preserve context around specialized content
- Maintain parent-child relationships

### Prompt Engineering
- Keep prompts focused and specific
- Clearly distinguish modes (strict vs. teaching)
- Include explicit constraints ("only use provided context")
- Test prompts against failure modes (hallucination, irrelevance)

## Security Best Practices

### Input Validation
- Validate all user inputs with Pydantic
- Sanitize file paths
- Limit input sizes (max question length, max file size)
- Check file types before processing

### API Safety
- Rate limit API endpoints
- Timeout on LLM calls (30 seconds default)
- Implement retries with exponential backoff
- Track and limit API costs

### Secrets Management
- Never commit secrets to version control
- Use environment variables for all sensitive data
- Add `.env` to `.gitignore`
- Provide `.env.example` with dummy values

## Documentation Standards

### Code Comments
- Explain WHY, not WHAT
- Document non-obvious design decisions
- Highlight important constraints or assumptions
- Example:
```python
# Use RRF k=60 based on empirical testing
# Lower values over-weight top ranks, higher values dilute signal
rrf_scores = reciprocal_rank_fusion(dense_results, bm25_results, k=60)
```

### README and Docs
- Keep README up-to-date with setup instructions
- Document all API endpoints
- Provide usage examples
- Include troubleshooting section

## Common Pitfalls to Avoid

### ❌ Silent Failures
```python
# BAD: Silently catch all exceptions
try:
    result = some_operation()
except:
    result = None  # What went wrong? No idea!
```

### ✅ Explicit Error Handling
```python
# GOOD: Specific exception with logging and re-raise
try:
    result = some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

### ❌ Premature Optimization
```python
# BAD: Complex caching logic before measuring need
@lru_cache(maxsize=10000)
def simple_function(x):
    return x * 2  # This doesn't need caching!
```

### ✅ Measure First, Optimize Second
```python
# GOOD: Profile first, optimize hot paths
import time

start = time.time()
result = expensive_operation()
duration = time.time() - start

logger.info(f"Operation took {duration:.2f}s")
# Only optimize if this is actually slow
```

### ❌ Hardcoded Values
```python
# BAD: Magic numbers
chunks = splitter.split(text, chunk_size=400)
```

### ✅ Configuration
```python
# GOOD: Configurable parameters
chunks = splitter.split(text, chunk_size=settings.max_chunk_size)
```

## Review Checklist

Before submitting code, verify:

- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] No bare `except:` clauses
- [ ] Errors are logged
- [ ] No hardcoded secrets or config
- [ ] Tests written and passing
- [ ] Source traceability maintained (for RAG code)
- [ ] Citations verified (for generation code)
- [ ] No silent failures
- [ ] Performance considered
- [ ] Security checked
- [ ] Documentation updated
