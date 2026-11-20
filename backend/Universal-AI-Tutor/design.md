# Universal AI Tutor — Architecture and Design

## Document Information
- **Version**: 1.0
- **Date**: November 11, 2026
- **Status**: Draft for Approval

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Layer                            │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │   Ingestion    │  │   Query      │  │   Conversation     │  │
│  │   Endpoints    │  │   Endpoints  │  │   Management       │  │
│  └────────┬───────┘  └──────┬───────┘  └─────────┬──────────┘  │
└───────────┼──────────────────┼────────────────────┼─────────────┘
            │                  │                    │
┌───────────▼──────────────────▼────────────────────▼─────────────┐
│                     Service Orchestration                        │
│  ┌─────────────────────────────────┐  ┌──────────────────────┐  │
│  │   Ingestion Service             │  │  LangGraph Workflow  │  │
│  │   - Parse & Chunk               │  │  - Query Analysis    │  │
│  │   - Enrich Metadata             │  │  - Retrieval         │  │
│  │   - Index Management            │  │  - Evidence Check    │  │
│  └────────────┬────────────────────┘  │  - Generation        │  │
│               │                       │  - Citation Verify   │  │
│               │                       └──────────┬───────────┘  │
└───────────────┼──────────────────────────────────┼──────────────┘
                │                                  │
┌───────────────▼──────────────────────────────────▼──────────────┐
│                      Core Components                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  LlamaIndex  │  │   Embedding  │  │   Retrieval Engine   │  │
│  │  Ingestion   │  │   Service    │  │   - Hybrid Search    │  │
│  │  Pipeline    │  │              │  │   - RRF Fusion       │  │
│  └──────────────┘  └──────────────┘  │   - Reranking        │  │
│                                      └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  LLM Client  │  │   Context    │  │   Citation           │  │
│  │  (Groq API)  │  │   Manager    │  │   Verifier           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────┬──────────────────────────────────┬──────────────┘
                │                                  │
┌───────────────▼──────────────────────────────────▼──────────────┐
│                      Data Layer                                  │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐ │
│  │   Qdrant Vector Database     │  │   Future: PostgreSQL     │ │
│  │   - Dense Index (HNSW)       │  │   - Student Progress     │ │
│  │   - BM25 Sparse Index        │  │   - Conversation History │ │
│  │   - Document Metadata        │  │   - Learning Analytics   │ │
│  └──────────────────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

External Services:
- Groq API (LLM inference)
- Hugging Face (model downloads)
```

### 1.2 Layer Responsibilities

#### API Layer (FastAPI)
- HTTP request/response handling
- Authentication/authorization (future)
- Input validation (Pydantic)
- Rate limiting
- Error handling and formatting
- API documentation generation

#### Service Layer
- Business logic orchestration
- LangGraph workflow execution
- Service composition
- Transaction boundaries
- Caching strategies

#### Core Component Layer
- Ingestion pipeline
- Embedding generation
- Retrieval and ranking
- LLM interaction
- Citation verification
- Context management

#### Data Layer
- Vector storage and search
- Metadata management
- Conversation persistence (future)
- Student data (future)

---

## 2. Component Design

### 2.1 Knowledge Ingestion Pipeline

```
Input Files (.txt/.md)
    ↓
┌─────────────────────────┐
│  Document Loader        │ ← LlamaIndex SimpleDirectoryReader
│  - Read files           │
│  - Validate encoding    │
│  - Extract metadata     │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Document Parser        │ ← LlamaIndex MarkdownNodeParser
│  - Parse structure      │
│  - Extract headings     │
│  - Identify sections    │
│  - Preserve formatting  │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Hierarchical Chunker   │ ← LlamaIndex SentenceSplitter
│  - Create parent chunks │   (two-level approach)
│  - Create child chunks  │
│  - Link parent-child    │
│  - Respect token limits │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Metadata Enricher      │ ← Custom component
│  - Add doc_id           │
│  - Add section_path     │
│  - Add parent_id        │
│  - Add source location  │
│  - Add timestamp        │
│  - Deterministic        │
│    contextual prefix    │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Embedding Generator    │ ← BGE-small-en-v1.5
│  - Generate embeddings  │
│  - Batch processing     │
│  - Error handling       │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  BM25 Indexer          │ ← Qdrant native full-text index
│  - Create text index    │   (built-in BM25 support)
│  - BM25 scoring on query│
│  - No manual computation│
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Qdrant Writer         │
│  - Store vectors        │
│  - Store metadata       │
│  - Create collections   │
│  - Handle duplicates    │
└─────────────────────────┘
```

**Key Design Decisions:**

1. **Chunking Strategy**:
   - **Target**: 400 tokens (mean), 256-512 tokens (hard limits)
   - **Approach**: Two-level hierarchy using `SentenceSplitter`
   - **Parent chunks**: 1200 tokens (for context expansion)
   - **Child chunks**: 400 tokens (for retrieval)
   - **Overlap**: 50 tokens for child chunks, 100 for parents
   - **Parent-child linking**: Manual - store parent_id and parent_text preview in child metadata
   - **Rationale**: BGE-small-en-v1.5 supports max 512 tokens; two-tier approach enables both precise retrieval and rich context expansion

2. **Metadata Schema** (with contextual enrichment support):
```python
{
    "doc_id": str,           # Unique document identifier
    "doc_title": str,        # Document name
    "doc_path": str,         # Original file path
    "section_path": list,    # ["Chapter 3", "Section 1.1"]
    "section_title": str,    # Current section heading
    "parent_id": str,        # Parent chunk ID
    "chunk_index": int,      # Position in document
    "content_type": str,     # "text", "code", "formula", etc.
    "indexed_at": datetime,  # Indexing timestamp
    "version": str,          # Content version hash
    "original_text": str,    # PRESERVED original chunk text
    "contextual_text": str,  # Enriched text (for retrieval)
    "is_contextualized": bool  # Flag for tracking
}
```

3. **Deduplication**: Hash content + metadata, check before insert

### 2.2 Retrieval Engine

```
Query Text
    ↓
┌─────────────────────────────────────────────────────┐
│  Query Preprocessing                                 │
│  - Normalize text                                   │
│  - Expand abbreviations (optional)                  │
│  - Generate embedding                               │
└──────────┬──────────────────────────────────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌─────────┐  ┌─────────┐
│ Dense   │  │ BM25    │
│ Search  │  │ Search  │
│ Top-20  │  │ Top-20  │
└────┬────┘  └────┬────┘
     │            │
     └─────┬──────┘
           ↓
┌─────────────────────────┐
│  RRF Fusion             │ ← Reciprocal Rank Fusion
│  - Combine rankings     │   k=60 (tunable)
│  - Deduplicate          │
│  - Top-10 candidates    │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Cross-Encoder Rerank   │ ← ms-marco-MiniLM-L-6-v2
│  - Score query-doc pairs│
│  - Re-sort by score     │
│  - Top-5 final results  │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Parent Context Expand  │ ← Retrieve parent chunks
│  - Fetch parent docs    │
│  - Include surrounding  │
│  - Preserve boundaries  │
└─────────────────────────┘
```

**Key Design Decisions:**

1. **Hybrid Search Configuration**:
   - Dense retrieval: cosine similarity via query vector
   - BM25 retrieval: Qdrant native full-text index
   - Fusion: Qdrant native RRF (no manual implementation)
   - Reranking: Cross-encoder on fused results
   - Final output: top-5 after reranking

2. **Qdrant Native Hybrid Query** (Qdrant 1.20+):
   ```python
   from qdrant_client import models
   
   results = client.query_points(
       collection_name="tutor_knowledge",
       # Prefetches: both retrieval methods
       prefetch=[
           models.Prefetch(
               query=models.TextQuery(text=query_text),  # BM25 search
               using="text",  # Full-text index
               limit=20
           ),
           models.Prefetch(
               query=query_embedding,  # Dense vector search
               using="dense",
               limit=20
           )
       ],
       # Query: RRF fusion of prefetches
       query=models.RrfQuery(rrf=models.Rrf()),  # Native RRF
       limit=10,
       with_payload=True,
       with_vectors=False
   )
   ```
   
3. **Benefits of Qdrant Native Approach**:
   - No manual RRF implementation needed
   - Optimized performance
   - Simpler codebase
   - Single API call for hybrid search

### 2.3 LangGraph Tutoring Workflow

```
Question Input
    ↓
┌─────────────────────────┐
│  Query Understanding    │
│  - Classify intent      │
│  - Extract entities     │
│  - Resolve coreference  │
│  - Add conversation ctx │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Retrieval Node         │
│  - Hybrid search        │
│  - RRF fusion           │
│  - Reranking            │
│  - Parent expansion     │
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Evidence Assessment    │
│  - Check sufficiency    │
│  - Compute coverage     │
│  - Decide: proceed/retry│
└──────────┬──────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌─────────┐  ┌─────────────┐
│ Retry   │  │ Generate    │
│ w/ New  │  │ Answer      │
│ Query   │  │             │
└─────────┘  └──────┬──────┘
                    ↓
           ┌─────────────────────────┐
           │  Citation Verification  │
           │  - Check claims         │
           │  - Validate sources     │
           │  - Flag unsupported     │
           └──────────┬──────────────┘
                      ↓
           ┌─────────────────────────┐
           │  Response Formatting    │
           │  - Structure output     │
           │  - Add metadata         │
           │  - Return to user       │
           └─────────────────────────┘
```

**LangGraph State Schema**:

```python
class TutoringState(TypedDict):
    question: str
    conversation_history: list[dict]
    mode: str  # "strict" or "teaching"
    query_embedding: list[float]
    retrieved_chunks: list[dict]
    retrieval_scores: list[float]
    evidence_sufficient: bool
    retry_count: int
    answer: str
    citations: list[dict]
    confidence: float
    metadata: dict
```

**Workflow Nodes**:

1. **query_understanding**: Parse question, resolve context
2. **retrieval**: Execute hybrid search + rerank
3. **evidence_check**: Assess if evidence is sufficient
4. **retry_retrieval**: Reformulate query if needed (max 2 retries)
5. **generate_answer**: Call LLM with context and mode
6. **verify_citations**: Check answer grounding
7. **format_response**: Prepare final output

**Conditional Edges**:
- `evidence_check` → `generate_answer` if sufficient
- `evidence_check` → `retry_retrieval` if insufficient and retries < 2
- `evidence_check` → `format_response` (admit unknown) if max retries

### 2.4 Answer Generation

**Prompt Templates**:

**Strict Notes Mode**:
```
You are an AI tutor. Answer the question using ONLY the provided context from the student's notes.

Context:
{context_chunks}

Question: {question}

Rules:
1. Only use information present in the context above
2. Cite sources using [Document Name, Section]
3. If the context doesn't contain enough information, say: "I don't have enough information in your notes to answer this question."
4. Do not add external knowledge or examples not in the context
5. Be precise and accurate

Answer:
```

**Teaching Mode**:
```
You are an AI tutor. Answer the question primarily using the provided context, but you may add explanations and examples to help the student understand.

Context from student's notes:
{context_chunks}

Question: {question}

Rules:
1. Use the context as the primary source
2. Clearly mark information from notes with citations [Document, Section]
3. You may add clarifying explanations and examples
4. Clearly distinguish: "From your notes: ... Additionally, to help understand: ..."
5. If notes don't cover the question, state that clearly
6. Be pedagogical and clear

Answer:
```

**Generation Parameters**:
- Temperature: 0.3 (strict), 0.5 (teaching)
- Max tokens: 800
- Top-p: 0.9
- Frequency penalty: 0.3

### 2.5 Citation Verification

```python
def verify_citations(answer: str, retrieved_chunks: list[dict]) -> dict:
    """
    Check if claims in the answer are supported by retrieved chunks.
    
    Returns:
        {
            "grounded": bool,
            "unsupported_claims": list[str],
            "citation_accuracy": float,
            "warnings": list[str]
        }
    """
```

**Verification Strategy**:

1. **Extract Claims**: Parse answer into factual statements
2. **Match to Sources**: Use semantic similarity to find supporting chunks
3. **Verify Citations**: Check that cited sources actually contain the claimed info
4. **Compute Scores**:
   - Groundedness: % of claims supported
   - Citation accuracy: % of citations that are correct
5. **Flag Issues**: Return warnings for unsupported claims

**Implementation**: Use lightweight NLI model or heuristic matching for MVP

---

## 3. Data Models

### 3.1 Request/Response Models (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class IngestRequest(BaseModel):
    """Request to ingest documents"""
    file_paths: list[str] = Field(..., description="Paths to files to ingest")
    overwrite: bool = Field(False, description="Overwrite existing docs")

class IngestResponse(BaseModel):
    """Response from ingestion"""
    status: Literal["success", "partial", "failed"]
    documents_processed: int
    chunks_created: int
    errors: list[str]
    duration_seconds: float

class QuestionRequest(BaseModel):
    """Request to ask a question"""
    question: str = Field(..., min_length=1, max_length=1000)
    mode: Literal["strict", "teaching"] = Field("strict")
    conversation_id: Optional[str] = None
    top_k: int = Field(5, ge=1, le=20)

class Citation(BaseModel):
    """Source citation"""
    document: str
    section: str
    excerpt: str = Field(..., max_length=500)
    confidence: float = Field(..., ge=0.0, le=1.0)

class AnswerResponse(BaseModel):
    """Response to a question"""
    answer: str
    citations: list[Citation]
    confidence: float
    mode: str
    conversation_id: str
    evidence_sufficient: bool
    retrieval_time_ms: float
    generation_time_ms: float
    metadata: dict

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    qdrant_connected: bool
    models_loaded: bool
    timestamp: datetime
```

### 3.2 Internal Data Models

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Chunk:
    """Internal representation of a text chunk"""
    id: str
    content: str
    embedding: list[float]
    metadata: dict
    parent_id: Optional[str] = None
    
@dataclass
class RetrievalResult:
    """Result from retrieval"""
    chunk: Chunk
    score: float
    rank: int
    retrieval_method: str  # "dense", "bm25", "reranked"

@dataclass
class GenerationContext:
    """Context for answer generation"""
    question: str
    chunks: list[Chunk]
    conversation_history: list[dict]
    mode: str
    metadata: dict
```

### 3.3 Database Schema

**Qdrant Collection Configuration** (Qdrant 1.20+):

```python
from qdrant_client import models

# Create collection with dense vectors
client.create_collection(
    collection_name="tutor_knowledge",
    vectors_config={
        "dense": models.VectorParams(
            size=384,  # BGE-small-en-v1.5
            distance=models.Distance.COSINE
        )
    }
)

# Create full-text index with BM25 scoring (Qdrant 1.20+)
client.create_payload_index(
    collection_name="tutor_knowledge",
    field_name="text",  # Payload field containing contextual_text
    field_schema=models.TextIndexParams(
        type=models.TextIndexType.TEXT,
        scoring=True,  # Enable BM25 scoring
        tokenizer=models.TokenizerType.WORD,
        lowercase=True
    )
)
```

**Future PostgreSQL Schema** (Phase 3):

```sql
-- Student profiles
CREATE TABLE students (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP
);

-- Conversation sessions
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    student_id UUID REFERENCES students(id),
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

-- Question-answer pairs
CREATE TABLE qa_history (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    question TEXT,
    answer TEXT,
    citations JSONB,
    mode VARCHAR(50),
    confidence FLOAT,
    asked_at TIMESTAMP
);

-- Learning progress
CREATE TABLE concept_mastery (
    id UUID PRIMARY KEY,
    student_id UUID REFERENCES students(id),
    concept VARCHAR(255),
    mastery_level FLOAT,
    last_updated TIMESTAMP
);
```

---

## 4. API Design

### 4.1 Endpoints

**Base URL**: `http://localhost:8000/api/v1`

#### POST /ingest
Upload and index documents.

**Request**:
```json
{
  "file_paths": ["/path/to/notes1.txt", "/path/to/notes2.md"],
  "overwrite": false
}
```

**Response** (200):
```json
{
  "status": "success",
  "documents_processed": 2,
  "chunks_created": 145,
  "errors": [],
  "duration_seconds": 12.3
}
```

#### POST /ask
Ask a question.

**Request**:
```json
{
  "question": "What is the Pythagorean theorem?",
  "mode": "strict",
  "conversation_id": "optional-uuid",
  "top_k": 5
}
```

**Response** (200):
```json
{
  "answer": "The Pythagorean theorem states that...",
  "citations": [
    {
      "document": "geometry_notes.md",
      "section": "Right Triangles",
      "excerpt": "In a right triangle, a² + b² = c²",
      "confidence": 0.95
    }
  ],
  "confidence": 0.92,
  "mode": "strict",
  "conversation_id": "uuid",
  "evidence_sufficient": true,
  "retrieval_time_ms": 234.5,
  "generation_time_ms": 1245.2,
  "metadata": {}
}
```

#### GET /health
Health check.

**Response** (200):
```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "models_loaded": true,
  "timestamp": "2026-11-11T10:30:00Z"
}
```

#### GET /docs
OpenAPI documentation (auto-generated by FastAPI)

### 4.2 Error Responses

**400 Bad Request**:
```json
{
  "detail": "Validation error: question must be between 1 and 1000 characters"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal error during retrieval",
  "request_id": "uuid"
}
```

**503 Service Unavailable**:
```json
{
  "detail": "Qdrant database is not available"
}
```

---

## 5. Configuration Management

### 5.1 Environment Variables

```bash
# Application
APP_ENV=development  # development, production
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=      # Optional, for Qdrant Cloud
QDRANT_COLLECTION_NAME=tutor_knowledge

# Groq
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_MAX_RETRIES=3
GROQ_TIMEOUT_SECONDS=30

# Models
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
EMBEDDING_DEVICE=cpu     # cpu, cuda
EMBEDDING_BATCH_SIZE=32

# Retrieval
DENSE_TOP_K=20
BM25_TOP_K=20
RRF_K=60
RERANK_TOP_K=5

# Generation
GENERATION_TEMPERATURE_STRICT=0.3
GENERATION_TEMPERATURE_TEACHING=0.5
GENERATION_MAX_TOKENS=800

# Performance
MAX_CHUNK_SIZE=800
MIN_CHUNK_SIZE=200
EMBEDDING_CACHE_SIZE=10000
```

### 5.2 Configuration File (config.py)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    
    # Qdrant
    qdrant_url: str
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "tutor_knowledge"
    
    # Groq
    groq_api_key: str
    groq_model: str = "llama-3.1-70b-versatile"
    groq_max_retries: int = 3
    groq_timeout_seconds: int = 30
    
    # Models
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32
    
    # Retrieval
    dense_top_k: int = 20
    bm25_top_k: int = 20
    rrf_k: int = 60
    rerank_top_k: int = 5
    
    # Generation
    generation_temperature_strict: float = 0.3
    generation_temperature_teaching: float = 0.5
    generation_max_tokens: int = 800
    
    # Performance
    max_chunk_size: int = 800
    min_chunk_size: int = 200
    embedding_cache_size: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 6. Technology Choices and Tradeoffs

### 6.1 LlamaIndex for Ingestion
**Chosen**: LlamaIndex  
**Alternatives**: LangChain, custom pipeline  
**Rationale**:
- Native hierarchical chunking support
- Rich document parsers
- Metadata management
- Integration with Qdrant

**Tradeoffs**:
- Learning curve
- Additional dependency
- Some overhead for simple cases

### 6.2 Qdrant for Vector Storage
**Chosen**: Qdrant  
**Alternatives**: Weaviate, Milvus, ChromaDB  
**Rationale**:
- Native sparse vector support (BM25)
- Excellent performance
- Easy local deployment
- Rich filtering capabilities

**Tradeoffs**:
- Requires separate service
- Memory usage for large datasets

### 6.3 LangGraph for Orchestration
**Chosen**: LangGraph  
**Alternatives**: LangChain, custom state machine  
**Rationale**:
- Explicit workflow control
- Debuggable state transitions
- Conditional logic support
- Retry and error handling

**Tradeoffs**:
- Newer framework
- Less community resources
- Potential API changes

### 6.4 Groq for LLM
**Chosen**: Groq API  
**Alternatives**: OpenAI, Anthropic, local Ollama  
**Rationale**:
- Very fast inference
- Good quality models
- Competitive pricing
- Simple API

**Tradeoffs**:
- API dependency
- Rate limits
- Cost for high volume
- Less control than local

### 6.5 BGE-small for Embeddings
**Chosen**: BGE-small-en-v1.5  
**Alternatives**: OpenAI embeddings, BGE-M3, E5  
**Rationale**:
- CPU-compatible
- Good quality
- 384 dimensions (smaller storage)
- Free/local

**Tradeoffs**:
- Not state-of-the-art
- English-only
- Lower quality than larger models

---

## 7. Security Considerations

### 7.1 Current Phase
- Environment variables for secrets
- Input validation (Pydantic)
- SQL injection prevention (ORM when added)
- Rate limiting (future)
- No authentication (local use)

### 7.2 Future Phases
- JWT authentication
- Role-based access control
- Multi-tenancy with data isolation
- Audit logging
- HTTPS/TLS
- API key management
- Content security policy

---

## 8. Deployment Architecture

### 8.1 Local Development (Phase 1)

```
┌─────────────────────────────────────┐
│  Windows Development Machine        │
│                                     │
│  ┌────────────────────────────┐    │
│  │  FastAPI (uvicorn)         │    │
│  │  Port: 8000                │    │
│  └────────────────────────────┘    │
│                                     │
│  ┌────────────────────────────┐    │
│  │  Qdrant (Docker)           │    │
│  │  Port: 6333                │    │
│  └────────────────────────────┘    │
│                                     │
│  ┌────────────────────────────┐    │
│  │  Models (local cache)      │    │
│  │  ~/.cache/huggingface      │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘
         │
         │ HTTPS
         ↓
┌─────────────────────┐
│   Groq API          │
│   (Cloud)           │
└─────────────────────┘
```

### 8.2 Future Production (Phase 4)

```
                ┌──────────────┐
                │  Load        │
                │  Balancer    │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ FastAPI │   │ FastAPI │   │ FastAPI │
   │ Instance│   │ Instance│   │ Instance│
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   ┌─────────┐   ┌──────────┐  ┌─────────┐
   │ Qdrant  │   │PostgreSQL│  │ Redis   │
   │ Cluster │   │          │  │ Cache   │
   └─────────┘   └──────────┘  └─────────┘
```

---

## 9. Monitoring and Observability

### 9.1 Logging Strategy
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request ID tracking
- Performance metrics per request

### 9.2 Metrics to Track
- Request latency (p50, p95, p99)
- Retrieval latency
- Generation latency
- API error rate
- Cache hit rate
- Groq API costs
- Concurrent requests

### 9.3 Future Integration
- Langfuse for LLM tracing
- Prometheus for metrics
- Grafana for visualization
- Sentry for error tracking

---

## 10. Testing Strategy

### 10.1 Unit Tests
- Model validation (Pydantic)
- Chunking logic
- RRF fusion algorithm
- Citation extraction
- Utility functions

### 10.2 Integration Tests
- API endpoints (FastAPI TestClient)
- Qdrant connection and queries
- End-to-end ingestion
- End-to-end Q&A

### 10.3 Evaluation Tests
- Retrieval quality (Recall@k, MRR, nDCG)
- Answer correctness (manual labels)
- Groundedness (Ragas)
- Citation accuracy
- Latency benchmarks

### 10.4 Test Data
- 5-10 sample documents
- 20-30 labeled Q&A pairs
- Known good/bad retrieval cases
- Edge cases (empty query, no results, etc.)

---

## 11. Open Questions and Decisions Needed

### Q1: Chunking Parameters
- **Question**: Exact token size (200-800 target)?
- **Recommendation**: 400 tokens mean, 256-512 hard limits (BGE-small max is 512)
- **Decision**: ✅ **APPROVED** - Start with 400 avg, 256-512 range

### Q2: BM25 Implementation
- **Question**: Use Qdrant sparse vectors or separate index?
- **Recommendation**: Qdrant native full-text index with built-in BM25
- **Decision**: ✅ **APPROVED** - Use Qdrant >=1.20.0 native BM25 support

### Q3: Context Window Management
- **Question**: How to handle when retrieved context exceeds LLM limit?
- **Recommendation**: Truncate to most relevant chunks by rerank score
- **Decision**: ✅ **APPROVED** - Prioritize by score, 128k window is generous

### Q4: Conversation Storage
- **Question**: Where to store conversation history in Phase 1?
- **Recommendation**: In-memory TTLCache (simple, no infrastructure)
- **Decision**: ✅ **APPROVED** - Use cachetools.TTLCache with 1hr TTL

### Q5: Citation Format
- **Question**: Inline citations [1] or named [Document, Section]?
- **Recommendation**: Named format for clarity
- **Decision**: ✅ **APPROVED** - Use [Document Name, Section] format

---

## 12. Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| Groq rate limits | Exponential backoff, queue, usage monitoring |
| Poor retrieval | Systematic evaluation, A/B testing, parameter tuning |
| Memory issues | Batch processing, streaming, monitoring |
| Qdrant downtime | Health checks, graceful degradation, retry logic |

### Quality Risks

| Risk | Mitigation |
|------|------------|
| Hallucinations | Evidence check, citation verify, groundedness scoring |
| Wrong citations | Post-generation verification, confidence thresholds |
| Slow responses | Caching, async processing, timeouts |
| Bad chunks | Evaluation, chunk inspection, boundary tuning |

---

## 13. Future Enhancements

### Phase 2 Improvements
- PDF ingestion (PyPDF2, pdfplumber)
- Advanced rerankers (BGE-reranker-large)
- Query expansion
- Ragas evaluation integration
- Langfuse tracing

### Phase 3 Features
- PostgreSQL for student data
- Adaptive difficulty
- Quiz generation
- Progress tracking
- Concept mastery modeling

### Phase 4 Production
- Multi-tenancy
- Authentication/authorization
- Horizontal scaling
- Kubernetes deployment
- Production monitoring

---

## Approval Checklist

- [ ] Architecture reviewed and approved
- [ ] Technology choices validated
- [ ] Data models confirmed
- [ ] API design approved
- [ ] Configuration strategy agreed
- [ ] Security considerations acknowledged
- [ ] Deployment plan understood
- [ ] Testing strategy approved
- [ ] Open questions resolved
- [ ] Ready to proceed to task breakdown
