# Universal AI Tutor

A production-oriented, subject-independent AI tutoring platform that transforms text-based educational notes into an intelligent, source-grounded AI teacher.

## Features

- **Universal**: Works with any subject (math, CS, history, etc.)
- **Source-Grounded**: All answers traceable to uploaded notes with citations
- **Hybrid Retrieval**: Dense embeddings + BM25 + reranking
- **Intelligent Workflows**: LangGraph-based tutoring logic
- **Two Modes**: Strict (notes only) and Teaching (notes + explanations)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- 16 GB RAM
- Groq API key

### Installation

```powershell
# Clone repository
git clone <repository-url>
cd Universal-AI-Tutor

# Install dependencies
pip install -e .

# Configure environment
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start Qdrant
docker compose up -d

# Run API server
uvicorn src.main:app --reload
```

### Usage

```python
# Upload notes
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{"file_paths": ["notes/math.txt"]}'

# Ask a question
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the Pythagorean theorem?", "mode": "strict"}'
```

## Architecture

```
FastAPI REST API
    ↓
LangGraph Tutoring Workflow
    ↓
Core Components (Retrieval, Embeddings, LLM)
    ↓
Qdrant Vector Database
```

## Development

### Running Tests

```powershell
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration -m integration

# With coverage
pytest --cov=src --cov-report=html
```

### Project Structure

```
Universal-AI-Tutor/
├── src/
│   ├── core/           # Core components (embeddings, vector store, LLM)
│   ├── services/       # Business logic (ingestion, retrieval, QA)
│   └── api/            # FastAPI endpoints
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── evaluation/     # Quality evaluation tests
├── data/
│   ├── raw/            # Original documents
│   └── processed/      # Processed chunks
├── .kiro/steering/     # Development guidelines
└── docs/               # Documentation
```

## Documentation

- [Requirements](requirements.md) - Full requirements specification
- [Design](design.md) - Architecture and design decisions
- [Tasks](tasks.md) - Implementation roadmap
- [Project Summary](PROJECT_SUMMARY.md) - Executive overview

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Orchestration**: LangGraph
- **Ingestion**: LlamaIndex
- **Vector DB**: Qdrant (1.20+)
- **Embeddings**: BGE-small-en-v1.5
- **Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **LLM**: Groq API (llama-3.1-70b-versatile)

## License

TBD

## Contributing

TBD

## Status

🚧 **Phase 1 (MVP) - In Development**

Current milestone: Project structure and core components
