# Testing Guidelines

## Testing Philosophy

### Test Pyramid
- **Unit Tests (70%)**: Test individual components in isolation
- **Integration Tests (20%)**: Test component interactions
- **End-to-End Tests (10%)**: Test complete workflows

### Test Coverage Goals
- **Critical paths**: 100% (retrieval, generation, citation verification)
- **Core logic**: 80%+ (embedding, chunking, fusion, reranking)
- **API endpoints**: 90%+
- **Utilities**: 70%+

## Unit Testing Standards

### Test Structure
```python
# tests/core/test_bm25_retriever.py
import pytest
from src.core.bm25_retriever import BM25Retriever

class TestBM25Retriever:
    """Test suite for BM25 retrieval functionality."""
    
    @pytest.fixture
    def retriever(self):
        """Provide a BM25Retriever instance for tests."""
        return BM25Retriever()
    
    @pytest.fixture
    def sample_documents(self):
        """Provide sample documents for testing."""
        return [
            {"id": "1", "text": "The quick brown fox"},
            {"id": "2", "text": "The lazy dog sleeps"},
            {"id": "3", "text": "Quick brown foxes jump"}
        ]
    
    def test_tokenize_basic(self, retriever):
        """Test basic tokenization."""
        text = "Hello World"
        tokens = retriever.tokenize(text)
        
        assert tokens == ["hello", "world"]
    
    def test_tokenize_empty(self, retriever):
        """Test tokenization of empty string."""
        tokens = retriever.tokenize("")
        
        assert tokens == []
    
    def test_search_returns_top_k(self, retriever, sample_documents):
        """Test that search returns requested number of results."""
        retriever.index(sample_documents)
        results = retriever.search("brown fox", top_k=2)
        
        assert len(results) == 2
        assert results[0]["id"] in ["1", "3"]  # Should find relevant docs
```

### Testing Best Practices

#### 1. Test One Thing Per Test
```python
# GOOD: Focused test
def test_embed_returns_correct_dimension(embedding_service):
    """Test that embedding has correct dimensionality."""
    embedding = embedding_service.embed("test")
    assert len(embedding) == 384

# BAD: Testing multiple concerns
def test_embedding_service(embedding_service):
    """Test embedding service."""  # Vague!
    embedding = embedding_service.embed("test")
    assert len(embedding) == 384  # Dimensionality
    assert all(isinstance(x, float) for x in embedding)  # Type
    assert -1 <= max(embedding) <= 1  # Range
    # Too many assertions!
```

#### 2. Use Descriptive Test Names
```python
# GOOD: Clear what's being tested
def test_reranker_reorders_results_by_relevance()
def test_citation_verifier_detects_unsupported_claims()
def test_ingestion_pipeline_handles_duplicate_documents()

# BAD: Vague or cryptic names
def test_reranker()
def test_citations()
def test_ingestion()
```

#### 3. Test Both Success and Failure
```python
def test_chunk_text_success(chunker):
    """Test successful text chunking."""
    text = "A" * 1000
    chunks = chunker.chunk(text, max_size=200)
    
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)

def test_chunk_text_empty_raises_error(chunker):
    """Test that empty text raises ValueError."""
    with pytest.raises(ValueError, match="Text cannot be empty"):
        chunker.chunk("")

def test_chunk_text_negative_size_raises_error(chunker):
    """Test that negative max_size raises ValueError."""
    with pytest.raises(ValueError, match="max_size must be positive"):
        chunker.chunk("test", max_size=-1)
```

#### 4. Use Fixtures for Setup
```python
@pytest.fixture
def mock_qdrant_client(mocker):
    """Provide a mocked Qdrant client."""
    client = mocker.Mock()
    client.search.return_value = [
        {"id": "1", "score": 0.9, "payload": {"text": "result 1"}},
        {"id": "2", "score": 0.8, "payload": {"text": "result 2"}}
    ]
    return client

@pytest.fixture
def vector_store(mock_qdrant_client):
    """Provide a VectorStore with mocked client."""
    return VectorStore(client=mock_qdrant_client)

def test_search_calls_qdrant(vector_store, mock_qdrant_client):
    """Test that search calls Qdrant client."""
    vector_store.search([0.1, 0.2, 0.3], top_k=5)
    
    mock_qdrant_client.search.assert_called_once()
```

## Integration Testing

### Testing Component Interactions
```python
# tests/integration/test_ingestion_pipeline.py
import pytest
from src.services.ingestion.pipeline import IngestionPipeline
from src.core.vector_store import VectorStore

@pytest.mark.integration
class TestIngestionPipeline:
    """Integration tests for ingestion pipeline."""
    
    @pytest.fixture
    def pipeline(self, test_qdrant_client):
        """Provide ingestion pipeline with test database."""
        return IngestionPipeline(vector_store=VectorStore(test_qdrant_client))
    
    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a temporary test file."""
        file_path = tmp_path / "test_document.txt"
        file_path.write_text("""
        # Introduction to Testing
        
        Testing is important for software quality.
        Unit tests verify individual components.
        Integration tests verify component interactions.
        """)
        return str(file_path)
    
    def test_ingest_document_end_to_end(self, pipeline, sample_file):
        """Test complete ingestion workflow."""
        # Ingest document
        result = pipeline.ingest([sample_file])
        
        # Verify results
        assert result.status == "success"
        assert result.documents_processed == 1
        assert result.chunks_created > 0
        
        # Verify data is searchable
        search_results = pipeline.vector_store.search("testing quality")
        assert len(search_results) > 0
        assert "Testing is important" in search_results[0]["text"]
```

### API Integration Tests
```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def ingested_data(client, sample_documents):
    """Ingest sample data before tests."""
    response = client.post("/api/v1/ingest", json={
        "file_paths": sample_documents,
        "overwrite": True
    })
    assert response.status_code == 200
    return response.json()

def test_ask_question_returns_answer(client, ingested_data):
    """Test asking a question returns an answer."""
    response = client.post("/api/v1/ask", json={
        "question": "What is testing?",
        "mode": "strict",
        "top_k": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
    assert data["confidence"] > 0.5

def test_ask_question_invalid_input(client):
    """Test that invalid input returns 400."""
    response = client.post("/api/v1/ask", json={
        "question": "",  # Empty question
        "mode": "strict"
    })
    
    assert response.status_code == 422  # Validation error
```

## Mocking External Services

### Mock Groq API
```python
@pytest.fixture
def mock_groq_client(mocker):
    """Mock Groq API client."""
    mock_client = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.choices = [
        mocker.Mock(
            message=mocker.Mock(
                content="The Pythagorean theorem states that a² + b² = c²."
            )
        )
    ]
    mock_response.usage = mocker.Mock(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150
    )
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

def test_generate_answer(mock_groq_client):
    """Test answer generation with mocked LLM."""
    llm_client = LLMClient(client=mock_groq_client)
    answer = llm_client.generate("What is the Pythagorean theorem?")
    
    assert "Pythagorean theorem" in answer
    mock_groq_client.chat.completions.create.assert_called_once()
```

### Mock Qdrant (Unit Tests)
```python
@pytest.fixture
def mock_vector_store(mocker):
    """Mock vector store for unit tests."""
    store = mocker.Mock()
    store.search.return_value = [
        {
            "id": "chunk_1",
            "score": 0.95,
            "payload": {
                "text": "The Pythagorean theorem is a² + b² = c²",
                "doc_id": "geometry_notes",
                "section": "Right Triangles"
            }
        }
    ]
    return store
```

### Use Real Qdrant (Integration Tests)
```python
@pytest.fixture(scope="session")
def test_qdrant_client():
    """Provide real Qdrant client for integration tests."""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(host="localhost", port=6333)
    
    # Create test collection
    collection_name = "test_tutor_knowledge"
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config={"size": 384, "distance": "Cosine"}
    )
    
    yield client
    
    # Cleanup
    client.delete_collection(collection_name)
```

## Parametrized Testing

### Test Multiple Scenarios
```python
@pytest.mark.parametrize("query,expected_count", [
    ("testing software", 2),
    ("quality assurance", 1),
    ("nonexistent topic", 0),
])
def test_search_various_queries(retriever, sample_docs, query, expected_count):
    """Test search with various queries."""
    retriever.index(sample_docs)
    results = retriever.search(query, top_k=10)
    
    assert len(results) == expected_count

@pytest.mark.parametrize("chunk_size", [200, 400, 600, 800])
def test_chunking_various_sizes(chunker, sample_text, chunk_size):
    """Test chunking with various sizes."""
    chunks = chunker.chunk(sample_text, max_size=chunk_size)
    
    assert all(len(chunk) <= chunk_size for chunk in chunks)
```

## Evaluation Testing

### RAG Quality Tests
```python
# tests/evaluation/test_retrieval_quality.py
import pytest
from src.evaluation.retrieval_eval import compute_recall_at_k

@pytest.fixture
def labeled_test_set():
    """Provide labeled test queries and expected documents."""
    return [
        {
            "query": "What is the Pythagorean theorem?",
            "relevant_docs": ["geometry_notes_chunk_5", "geometry_notes_chunk_6"]
        },
        {
            "query": "Explain binary search algorithm",
            "relevant_docs": ["algorithms_notes_chunk_12"]
        }
    ]

def test_retrieval_recall_at_k(retrieval_system, labeled_test_set):
    """Test retrieval recall on labeled test set."""
    recall_scores = []
    
    for item in labeled_test_set:
        results = retrieval_system.retrieve(item["query"], top_k=5)
        retrieved_ids = [r["id"] for r in results]
        
        # Compute recall
        relevant_found = sum(1 for doc_id in item["relevant_docs"] 
                           if doc_id in retrieved_ids)
        recall = relevant_found / len(item["relevant_docs"])
        recall_scores.append(recall)
    
    avg_recall = sum(recall_scores) / len(recall_scores)
    assert avg_recall >= 0.8, f"Recall@5 is {avg_recall:.2f}, expected >= 0.8"

def test_groundedness_on_test_set(qa_system, labeled_test_set):
    """Test answer groundedness on test set."""
    groundedness_scores = []
    
    for item in labeled_test_set:
        response = qa_system.answer(item["query"], mode="strict")
        
        # Compute groundedness
        score = compute_groundedness(
            answer=response["answer"],
            sources=response["citations"]
        )
        groundedness_scores.append(score)
    
    avg_groundedness = sum(groundedness_scores) / len(groundedness_scores)
    assert avg_groundedness >= 0.9, \
        f"Groundedness is {avg_groundedness:.2f}, expected >= 0.9"
```

## Performance Testing

### Latency Tests
```python
import time
import pytest

@pytest.mark.performance
def test_retrieval_latency(retrieval_system):
    """Test that retrieval completes within time limit."""
    query = "What is machine learning?"
    
    start = time.time()
    results = retrieval_system.retrieve(query, top_k=5)
    duration = time.time() - start
    
    assert duration < 2.0, f"Retrieval took {duration:.2f}s, expected < 2.0s"

@pytest.mark.performance
def test_end_to_end_latency(qa_system):
    """Test end-to-end question answering latency."""
    question = "Explain the scientific method."
    
    start = time.time()
    response = qa_system.answer(question, mode="strict")
    duration = time.time() - start
    
    assert duration < 10.0, f"Q&A took {duration:.2f}s, expected < 10.0s"
```

## Test Organization

### Directory Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── core/
│   │   ├── test_embedding_service.py
│   │   ├── test_bm25_retriever.py
│   │   ├── test_fusion.py
│   │   └── test_reranker.py
│   └── services/
│       ├── test_chunker.py
│       └── test_enricher.py
├── integration/
│   ├── test_ingestion_pipeline.py
│   ├── test_qa_workflow.py
│   └── test_api.py
├── evaluation/
│   ├── test_retrieval_quality.py
│   └── test_answer_quality.py
├── performance/
│   └── test_latency.py
└── fixtures/
    ├── sample_documents/
    │   ├── math_notes.txt
    │   └── cs_notes.md
    └── test_qa_pairs.json
```

### Shared Fixtures (conftest.py)
```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def sample_documents_dir(fixtures_dir):
    """Return path to sample documents."""
    return fixtures_dir / "sample_documents"

@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return """
    Machine learning is a subset of artificial intelligence.
    It focuses on training models to learn from data.
    Common algorithms include linear regression and neural networks.
    """
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/core/test_embedding_service.py
```

### Run Specific Test
```bash
pytest tests/core/test_embedding_service.py::test_embed_single_text
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run by Marker
```bash
pytest -m integration     # Run only integration tests
pytest -m "not performance"  # Skip performance tests
```

### Run with Verbose Output
```bash
pytest -v
pytest -vv  # Even more verbose
```

## Continuous Integration

### Test Matrix
- Python versions: 3.11, 3.12
- OS: Windows, Linux (Ubuntu)
- Test suites: unit, integration, evaluation

### CI Configuration Example (.github/workflows/test.yml)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Start Qdrant
        run: |
          docker compose up -d qdrant
          sleep 5  # Wait for startup
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Quality Checklist

Before committing tests, verify:

- [ ] Tests are independent (can run in any order)
- [ ] Tests have descriptive names
- [ ] Each test has a docstring explaining what it tests
- [ ] Fixtures are used for common setup
- [ ] External services are mocked (unit tests)
- [ ] Both success and failure cases are tested
- [ ] Edge cases and boundary conditions are covered
- [ ] Tests run quickly (< 1 second for unit tests)
- [ ] Tests are deterministic (no random failures)
- [ ] Coverage meets standards for code area
- [ ] Performance tests have reasonable thresholds
- [ ] Evaluation tests verify RAG quality metrics
