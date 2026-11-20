# Universal AI Tutor — Implementation Tasks

## Document Information
- **Version**: 1.0
- **Date**: November 11, 2026
- **Status**: Draft for Approval

---

## Development Phases Overview

### Phase 1: Functional RAG Foundation (MVP)
**Goal**: End-to-end working system with ingestion, retrieval, and answer generation  
**Duration**: ~2-3 weeks  
**Deliverable**: Functioning Q&A system with source citations

### Phase 2: Retrieval Optimization & Evaluation
**Goal**: Improve retrieval quality and establish systematic evaluation  
**Duration**: ~1-2 weeks  
**Deliverable**: Measurable quality improvements and evaluation framework

### Phase 3: Adaptive Tutoring & Learning
**Goal**: Student memory, progress tracking, adaptive explanations  
**Duration**: ~2-3 weeks  
**Deliverable**: Personalized learning features

### Phase 4: Production Readiness
**Goal**: Security, monitoring, scalability, deployment  
**Duration**: ~2 weeks  
**Deliverable**: Production-ready deployment

---

## Phase 1: Functional RAG Foundation

### 1.1 Project Setup and Infrastructure

#### Task 1.1.1: Initialize Project Structure
**Objective**: Create project skeleton with proper Python structure

**Actions**:
- Create directory structure:
  ```
  universal-ai-tutor/
  ├── src/
  │   ├── api/
  │   ├── services/
  │   ├── core/
  │   ├── models/
  │   └── utils/
  ├── tests/
  ├── data/
  │   ├── raw/
  │   └── processed/
  ├── config/
  ├── docker/
  └── docs/
  ```
- Create `pyproject.toml` with dependencies
- Create `.env.example` template
- Create `.gitignore`
- Create `README.md` with setup instructions

**Files**: 
- `pyproject.toml`
- `.env.example`
- `.gitignore`
- `README.md`

**Dependencies**: None

**Acceptance Criteria**:
- [ ] Directory structure created
- [ ] All dependencies listed in pyproject.toml
- [ ] .env.example contains all required variables
- [ ] README has clear setup instructions

**Tests**: None (infrastructure task)

**Definition of Done**: Project can be cloned and dependencies installed

---

#### Task 1.1.2: Configure Dependency Management
**Objective**: Set up Python dependencies with proper versions

**Actions**:
- Define dependencies:
  - fastapi>=0.104.0
  - uvicorn[standard]>=0.24.0
  - pydantic>=2.5.0
  - pydantic-settings>=2.1.0
  - llama-index>=0.9.0
  - qdrant-client>=1.7.0
  - sentence-transformers>=2.2.2
  - groq>=0.4.0
  - langgraph>=0.0.20
  - langchain-core>=0.1.0
  - python-dotenv>=1.0.0
  - pytest>=7.4.3
  - pytest-asyncio>=0.21.1
  - httpx>=0.25.2
- Add dev dependencies:
  - black
  - ruff
  - mypy
  - pytest-cov

**Files**: `pyproject.toml`

**Dependencies**: Task 1.1.1

**Acceptance Criteria**:
- [ ] All required packages listed
- [ ] Version constraints specified
- [ ] Dev dependencies separated
- [ ] Installation succeeds without errors

**Tests**: 
- Install dependencies in fresh environment
- Verify imports work

**Definition of Done**: `pip install -e .` completes successfully

---

#### Task 1.1.3: Set Up Docker Compose for Qdrant
**Objective**: Provide local Qdrant instance for development

**Actions**:
- Create `docker-compose.yml`:
  ```yaml
  version: '3.8'
  services:
    qdrant:
      image: qdrant/qdrant:v1.7.0
      ports:
        - "6333:6333"
      volumes:
        - ./data/qdrant_storage:/qdrant/storage
  ```
- Create startup script for Windows
- Add Qdrant health check utility

**Files**: 
- `docker-compose.yml`
- `scripts/start-qdrant.ps1`
- `src/utils/qdrant_health.py`

**Dependencies**: Task 1.1.1

**Acceptance Criteria**:
- [ ] Qdrant starts with docker compose up
- [ ] Port 6333 accessible
- [ ] Data persists across restarts
- [ ] Health check script works

**Tests**: 
- Test connection to Qdrant
- Test data persistence

**Definition of Done**: Qdrant accessible at localhost:6333

---

#### Task 1.1.4: Configuration Management
**Objective**: Implement settings management with environment variables

**Actions**:
- Create `src/config/settings.py`:
  - BaseSettings with all config vars
  - Validation for required fields
  - Type hints
  - Caching with lru_cache
- Create example `.env` file
- Add config loading tests

**Files**: 
- `src/config/__init__.py`
- `src/config/settings.py`
- `.env.example`

**Dependencies**: Task 1.1.2

**Acceptance Criteria**:
- [ ] All settings loaded from environment
- [ ] Required settings validated on startup
- [ ] Settings cached for performance
- [ ] Type hints present
- [ ] Defaults provided where appropriate

**Tests**:
- Test config loading with valid .env
- Test validation errors for missing required vars
- Test default values

**Definition of Done**: Settings can be imported and used throughout app

---

### 1.2 Core Components

#### Task 1.2.1: Embedding Service
**Objective**: Implement embedding generation with BGE-small

**Actions**:
- Create `src/core/embedding_service.py`:
  - Load BGE-small-en-v1.5 model
  - Batch embedding generation
  - Caching mechanism
  - Error handling
  - Device management (CPU/GPU)
- Add model download on first use
- Implement embedding normalization

**Files**: 
- `src/core/embedding_service.py`
- `src/core/__init__.py`

**Dependencies**: Task 1.1.4

**Acceptance Criteria**:
- [ ] Model loads successfully
- [ ] Embeddings generated for text
- [ ] Batch processing works
- [ ] Results cached
- [ ] Works on CPU
- [ ] Output is 384-dimensional

**Tests**:
- Test single text embedding
- Test batch embedding
- Test caching
- Verify output shape
- Test error handling for invalid input

**Definition of Done**: Can generate embeddings for any text

---

#### Task 1.2.2: Qdrant Client Wrapper
**Objective**: Create abstraction over Qdrant operations

**Actions**:
- Create `src/core/vector_store.py`:
  - Initialize Qdrant client
  - Create collection with dense vectors + full-text index
  - Insert vectors with metadata
  - Dense vector search
  - BM25 full-text search (using native index)
  - Hybrid search with native RRF fusion
  - Metadata filtering
  - Health check
  - Connection retry logic
- Implement collection creation on startup
- Handle duplicate detection

**Files**: 
- `src/core/vector_store.py`

**Dependencies**: Task 1.1.3, Task 1.2.1

**Acceptance Criteria**:
- [ ] Connects to Qdrant successfully
- [ ] Creates collection with vector + text index config
- [ ] Inserts vectors with metadata
- [ ] Dense search works
- [ ] BM25 search works on text index
- [ ] Hybrid search with native RRF works
- [ ] Handles connection failures gracefully

**Tests**:
- Test connection
- Test collection creation
- Test insert and retrieve
- Test dense search
- Test BM25 search
- Test hybrid search with RRF
- Test error handling

**Definition of Done**: Can perform hybrid search with native Qdrant RRF

---

#### Task 1.2.3: Cross-Encoder Reranking
**Objective**: Implement neural reranking of retrieved results

**Actions**:
- Create `src/core/reranker.py`:
  - Load cross-encoder model (ms-marco-MiniLM-L-6-v2)
  - Score query-document pairs
  - Batch processing for efficiency
  - Re-sort results by score
  - Return top-k reranked

**Files**: 
- `src/core/reranker.py`

**Dependencies**: Task 1.2.2

**Acceptance Criteria**:
- [ ] Model loads successfully
- [ ] Scores query-doc pairs
- [ ] Batch processing works
- [ ] Results re-sorted correctly
- [ ] Runs on CPU

**Tests**:
- Test reranking with sample docs
- Verify ranking changes
- Test batch processing
- Measure performance

**Definition of Done**: Reranker improves retrieval quality measurably

---

#### Task 1.2.4: Groq LLM Client
**Objective**: Implement LLM client for answer generation

**Actions**:
- Create `src/core/llm_client.py`:
  - Initialize Groq client
  - Generate completion with streaming option
  - Configurable parameters (temp, max_tokens, etc.)
  - Retry logic with exponential backoff
  - Rate limit handling
  - Token usage tracking
  - Error handling

**Files**: 
- `src/core/llm_client.py`

**Dependencies**: Task 1.1.4

**Acceptance Criteria**:
- [ ] Connects to Groq API
- [ ] Generates completions
- [ ] Handles rate limits
- [ ] Retries on failure
- [ ] Tracks token usage
- [ ] Configurable parameters

**Tests**:
- Test successful generation
- Test retry logic
- Test timeout handling
- Mock API for testing

**Definition of Done**: Can generate LLM responses reliably

---

### 1.3 Knowledge Ingestion Pipeline

#### Task 1.3.1: Document Loader
**Objective**: Load text and Markdown files

**Actions**:
- Create `src/services/ingestion/loader.py`:
  - Use LlamaIndex SimpleDirectoryReader
  - Support .txt and .md files
  - Extract file metadata (name, path, size, modified date)
  - Handle encoding issues (UTF-8)
  - Validate file formats
  - File hash for deduplication

**Files**: 
- `src/services/ingestion/__init__.py`
- `src/services/ingestion/loader.py`

**Dependencies**: Task 1.1.4

**Acceptance Criteria**:
- [ ] Loads .txt files
- [ ] Loads .md files
- [ ] Extracts metadata
- [ ] Handles encoding errors gracefully
- [ ] Computes file hash

**Tests**:
- Test loading sample .txt file
- Test loading sample .md file
- Test invalid encoding
- Test missing file

**Definition of Done**: Can load text and Markdown files into memory

---

#### Task 1.3.2: Document Parser and Chunker
**Objective**: Parse structure and create hierarchical chunks

**Actions**:
- Create `src/services/ingestion/chunker.py`:
  - Use LlamaIndex `SentenceSplitter` for both .txt and .md
  - **Parent-level chunking**: 1200 tokens, 100 token overlap
  - **Child-level chunking**: 400 tokens, 50 token overlap
  - Hard limits: 256-512 tokens (BGE-small-en-v1.5 max)
  - Preserve paragraph boundaries with `paragraph_separator="\n\n"`
  - **Manual parent-child linking**: Store parent_id and parent_text preview
  - Extract section titles from markdown headings
  - Maintain original text without modification

**Implementation Approach**:
```python
# 1. Create parent chunks (for context expansion)
parent_splitter = SentenceSplitter(chunk_size=1200, chunk_overlap=100)
parent_nodes = parent_splitter.get_nodes_from_documents([doc])

# 2. Create child chunks from each parent (for retrieval)
child_splitter = SentenceSplitter(
    chunk_size=400, 
    chunk_overlap=50,
    paragraph_separator="\n\n"
)

# 3. Link children to parents
for parent in parent_nodes:
    children = child_splitter.get_nodes_from_documents([parent])
    for child in children:
        child.metadata['parent_id'] = parent.id_
        child.metadata['parent_text'] = parent.text[:500]
```

**Files**: 
- `src/services/ingestion/chunker.py`

**Dependencies**: Task 1.3.1

**Acceptance Criteria**:
- [ ] Parent chunks ~1200 tokens (range: 800-1500)
- [ ] Child chunks ~400 tokens (range: 256-512)
- [ ] Parent-child relationships created
- [ ] Section titles extracted
- [ ] No loss of original content
- [ ] Works for both .txt and .md

**Tests**:
- Test parent chunking
- Test child chunking
- Verify chunk sizes within limits
- Verify parent-child links
- Test with .txt and .md files

**Definition of Done**: Documents split into two-level hierarchical chunks

---

#### Task 1.3.3: Metadata Enrichment
**Objective**: Add contextual metadata to chunks

**Actions**:
- Create `src/services/ingestion/enricher.py`:
  - Generate unique chunk IDs
  - Add document ID and title
  - Add section title
  - Add parent chunk ID
  - Add chunk index (position)
  - Add content type (text, code, formula)
  - Add timestamp
  - Add version hash

**Files**: 
- `src/services/ingestion/enricher.py`

**Dependencies**: Task 1.3.2

**Acceptance Criteria**:
- [ ] All metadata fields populated
- [ ] IDs are unique
- [ ] Parent-child links correct
- [ ] Timestamps accurate

**Tests**:
- Test enrichment on sample chunks
- Verify all fields present
- Test ID uniqueness

**Definition of Done**: Chunks have complete metadata

---

#### Task 1.3.4: Ingestion Pipeline Orchestration
**Objective**: Coordinate full ingestion workflow

**Actions**:
- Create `src/services/ingestion/pipeline.py`:
  - Load documents
  - Parse and chunk
  - Enrich metadata
  - Generate embeddings (dense)
  - Generate BM25 representations (sparse)
  - Store in Qdrant
  - Handle errors per document
  - Return ingestion report
  - Support batch processing
  - Detect and skip duplicates

**Files**: 
- `src/services/ingestion/pipeline.py`

**Dependencies**: Tasks 1.3.1, 1.3.2, 1.3.3, 1.2.1, 1.2.2, 1.2.3

**Acceptance Criteria**:
- [ ] Processes multiple documents
- [ ] Each step executes correctly
- [ ] Errors handled gracefully
- [ ] Reports statistics (docs processed, chunks created, errors)
- [ ] Prevents duplicate indexing

**Tests**:
- Test end-to-end ingestion
- Test error handling
- Test duplicate detection
- Test batch processing

**Definition of Done**: Can ingest documents from files to Qdrant

---

### 1.4 Retrieval System

#### Task 1.4.1: Hybrid Retrieval with Native RRF
**Objective**: Execute dense + BM25 search with Qdrant native RRF fusion

**Actions**:
- Create `src/services/retrieval/hybrid_retriever.py`:
  - Generate query embedding
  - Execute Qdrant hybrid query with native RRF:
    ```python
    results = client.query_points(
        collection_name="tutor_knowledge",
        query=query_embedding,  # Dense
        prefetch=[
            Prefetch(
                query=Query(text=query_text),  # BM25
                using="text",
                limit=20
            )
        ],
        limit=10,
        fusion="rrf"  # Native RRF
    )
    ```
  - Return fused results with scores
  - Include retrieval metadata

**Files**: 
- `src/services/retrieval/__init__.py`
- `src/services/retrieval/hybrid_retriever.py`

**Dependencies**: Task 1.2.2, Task 1.2.1

**Acceptance Criteria**:
- [ ] Executes hybrid query with single API call
- [ ] Native RRF fusion works
- [ ] Returns top-10 fused results
- [ ] Includes scores and metadata
- [ ] Handles empty results gracefully

**Tests**:
- Test hybrid retrieval with sample query
- Compare hybrid vs. dense-only recall
- Verify RRF fusion effect
- Test with various query types

**Definition of Done**: Hybrid retrieval returns relevant results with native RRF

---

#### Task 1.4.2: Cross-Encoder Reranking Integration
**Objective**: Apply cross-encoder reranking to hybrid results

**Actions**:
- Integrate reranker from Task 1.2.3:
  - Take hybrid results from Task 1.4.1
  - Apply cross-encoder scoring
  - Re-sort by rerank scores
  - Return top-5 final results

**Files**: 
- Update `src/services/retrieval/hybrid_retriever.py`

**Dependencies**: Task 1.4.1, Task 1.2.3

**Acceptance Criteria**:
- [ ] Reranks hybrid results
- [ ] Returns top-5 reranked
- [ ] Includes rerank scores
- [ ] Measurably improves quality

**Tests**:
- Test reranking changes order
- Compare reranked vs. non-reranked quality
- Measure Recall@5 improvement

**Definition of Done**: Reranking improves hybrid retrieval quality

---

#### Task 1.4.3: Parent Context Expansion
**Objective**: Retrieve parent sections for small chunks

**Actions**:
- Create `src/services/retrieval/context_expander.py`:
  - Check if chunk is below threshold (300 tokens)
  - Retrieve parent chunk using parent_id
  - Include surrounding context
  - Limit expanded context (1500 tokens max)
  - Maintain source traceability

**Files**: 
- `src/services/retrieval/context_expander.py`

**Dependencies**: Task 1.4.2

**Acceptance Criteria**:
- [ ] Detects small chunks
- [ ] Retrieves parent successfully
- [ ] Respects token limits
- [ ] Maintains metadata

**Tests**:
- Test expansion for small chunk
- Test no expansion for large chunk
- Verify token limits

**Definition of Done**: Small chunks expanded with parent context

---

### 1.5 LangGraph Tutoring Workflow

#### Task 1.5.1: Define Workflow State
**Objective**: Create typed state for LangGraph workflow

**Actions**:
- Create `src/services/tutoring/state.py`:
  - Define TutoringState TypedDict
  - Include all workflow fields
  - Add type hints
  - Document state transitions

**Files**: 
- `src/services/tutoring/__init__.py`
- `src/services/tutoring/state.py`

**Dependencies**: Task 1.1.4

**Acceptance Criteria**:
- [ ] State fully typed
- [ ] All fields documented
- [ ] Type checking passes

**Tests**: None (type definition)

**Definition of Done**: State defined and typed

---

#### Task 1.5.2: Query Understanding Node
**Objective**: Analyze and preprocess user question

**Actions**:
- Create `src/services/tutoring/nodes/query_understanding.py`:
  - Normalize question text
  - Generate query embedding
  - Basic intent classification (question vs. statement)
  - Store in state
  - Handle conversation context (future: resolve references)

**Files**: 
- `src/services/tutoring/nodes/__init__.py`
- `src/services/tutoring/nodes/query_understanding.py`

**Dependencies**: Task 1.5.1, Task 1.2.1

**Acceptance Criteria**:
- [ ] Normalizes text
- [ ] Generates embedding
- [ ] Updates state correctly

**Tests**:
- Test with sample questions
- Verify state updates

**Definition of Done**: Query preprocessing works

---

#### Task 1.5.3: Retrieval Node
**Objective**: Execute hybrid retrieval with reranking

**Actions**:
- Create `src/services/tutoring/nodes/retrieval.py`:
  - Call hybrid retriever
  - Apply reranking
  - Expand context if needed
  - Store retrieved chunks in state
  - Include scores and metadata

**Files**: 
- `src/services/tutoring/nodes/retrieval.py`

**Dependencies**: Task 1.5.1, Task 1.4.1, Task 1.4.2, Task 1.4.3

**Acceptance Criteria**:
- [ ] Executes retrieval pipeline
- [ ] Stores results in state
- [ ] Includes all metadata

**Tests**:
- Test with sample query
- Verify state updates

**Definition of Done**: Retrieval node returns relevant chunks

---

#### Task 1.5.4: Evidence Assessment Node
**Objective**: Determine if retrieved evidence is sufficient

**Actions**:
- Create `src/services/tutoring/nodes/evidence_check.py`:
  - Check if chunks retrieved
  - Check average rerank score threshold (> 0.4)
  - Check minimum chunks (>= 2)
  - Set evidence_sufficient flag
  - Decide: proceed or retry

**Files**: 
- `src/services/tutoring/nodes/evidence_check.py`

**Dependencies**: Task 1.5.3

**Acceptance Criteria**:
- [ ] Assesses evidence quality
- [ ] Sets sufficient flag correctly
- [ ] Provides reasoning

**Tests**:
- Test with good evidence (sufficient)
- Test with poor evidence (insufficient)
- Test with no results

**Definition of Done**: Evidence assessment works correctly

---

#### Task 1.5.5: Answer Generation Node
**Objective**: Generate grounded answer using LLM

**Actions**:
- Create `src/services/tutoring/nodes/generation.py`:
  - Format prompt based on mode (strict/teaching)
  - Include retrieved chunks as context
  - Call Groq LLM
  - Parse response
  - Store answer in state
  - Track generation metadata (tokens, cost)

**Files**: 
- `src/services/tutoring/nodes/generation.py`
- `src/services/tutoring/prompts.py`

**Dependencies**: Task 1.5.4, Task 1.2.6

**Acceptance Criteria**:
- [ ] Formats correct prompt for mode
- [ ] Generates answer
- [ ] Includes context chunks
- [ ] Handles generation errors

**Tests**:
- Test strict mode generation
- Test teaching mode generation
- Test with insufficient evidence
- Mock LLM for testing

**Definition of Done**: Generates grounded answers

---

#### Task 1.5.6: Citation Verification Node
**Objective**: Verify answer claims are supported by sources

**Actions**:
- Create `src/services/tutoring/nodes/citation_verify.py`:
  - Extract factual claims from answer
  - Check if claims match retrieved chunks
  - Verify cited sources exist
  - Compute groundedness score
  - Flag unsupported claims
  - Store verification results

**Files**: 
- `src/services/tutoring/nodes/citation_verify.py`

**Dependencies**: Task 1.5.5

**Acceptance Criteria**:
- [ ] Extracts claims
- [ ] Matches to sources
- [ ] Computes groundedness
- [ ] Flags issues

**Tests**:
- Test with well-grounded answer
- Test with hallucinated answer
- Test citation accuracy

**Definition of Done**: Citation verification detects unsupported claims

---

#### Task 1.5.7: Workflow Orchestration
**Objective**: Assemble LangGraph workflow with nodes and edges

**Actions**:
- Create `src/services/tutoring/workflow.py`:
  - Define StateGraph
  - Add all nodes
  - Define conditional edges
  - Implement retry logic (max 2)
  - Compile workflow
  - Expose run method

**Files**: 
- `src/services/tutoring/workflow.py`

**Dependencies**: Tasks 1.5.2 - 1.5.6

**Acceptance Criteria**:
- [ ] Workflow defined correctly
- [ ] Nodes connected with edges
- [ ] Conditional logic works
- [ ] Retry mechanism functions
- [ ] Workflow compiles

**Tests**:
- Test successful path
- Test retry path
- Test max retry reached
- Test insufficient evidence

**Definition of Done**: Complete workflow executes end-to-end

---

### 1.6 API Layer

#### Task 1.6.1: Define API Models
**Objective**: Create Pydantic request/response models

**Actions**:
- Create `src/models/api.py`:
  - IngestRequest
  - IngestResponse
  - QuestionRequest
  - Citation
  - AnswerResponse
  - HealthResponse
  - Add validation rules
  - Add examples for docs

**Files**: 
- `src/models/__init__.py`
- `src/models/api.py`

**Dependencies**: Task 1.1.4

**Acceptance Criteria**:
- [ ] All models defined
- [ ] Validation rules present
- [ ] Type hints correct
- [ ] Examples added

**Tests**:
- Test model validation
- Test serialization

**Definition of Done**: API models defined and validated

---

#### Task 1.6.2: Ingestion Endpoint
**Objective**: Create POST /ingest endpoint

**Actions**:
- Create `src/api/routes/ingest.py`:
  - Define POST /ingest route
  - Validate request
  - Call ingestion pipeline
  - Handle errors
  - Return response with statistics
  - Add logging

**Files**: 
- `src/api/__init__.py`
- `src/api/routes/__init__.py`
- `src/api/routes/ingest.py`

**Dependencies**: Task 1.6.1, Task 1.3.4

**Acceptance Criteria**:
- [ ] Endpoint accepts file paths
- [ ] Calls ingestion pipeline
- [ ] Returns statistics
- [ ] Handles errors gracefully
- [ ] Validates input

**Tests**:
- Test successful ingestion
- Test validation errors
- Test duplicate handling

**Definition of Done**: Can ingest documents via API

---

#### Task 1.6.3: Question Answering Endpoint
**Objective**: Create POST /ask endpoint

**Actions**:
- Create `src/api/routes/ask.py`:
  - Define POST /ask route
  - Validate request
  - Execute LangGraph workflow
  - Format response with citations
  - Handle errors
  - Track latency
  - Add logging

**Files**: 
- `src/api/routes/ask.py`

**Dependencies**: Task 1.6.1, Task 1.5.7

**Acceptance Criteria**:
- [ ] Endpoint accepts question
- [ ] Executes workflow
- [ ] Returns answer with citations
- [ ] Supports mode parameter
- [ ] Tracks timing

**Tests**:
- Test successful Q&A
- Test validation errors
- Test both modes
- Test unsupported questions

**Definition of Done**: Can ask questions via API

---

#### Task 1.6.4: Health Check Endpoint
**Objective**: Create GET /health endpoint

**Actions**:
- Create `src/api/routes/health.py`:
  - Define GET /health route
  - Check Qdrant connection
  - Check models loaded
  - Return status
  - Add timestamp

**Files**: 
- `src/api/routes/health.py`

**Dependencies**: Task 1.2.2, Task 1.2.1

**Acceptance Criteria**:
- [ ] Returns health status
- [ ] Checks Qdrant
- [ ] Checks models
- [ ] Fast response (< 1 sec)

**Tests**:
- Test healthy state
- Test Qdrant disconnected

**Definition of Done**: Health endpoint works

---

#### Task 1.6.5: FastAPI Application
**Objective**: Create main FastAPI application

**Actions**:
- Create `src/main.py`:
  - Initialize FastAPI app
  - Add middleware (CORS, timing)
  - Register routers
  - Add exception handlers
  - Configure logging
  - Add startup/shutdown events
  - Generate OpenAPI docs

**Files**: 
- `src/main.py`

**Dependencies**: Tasks 1.6.2, 1.6.3, 1.6.4

**Acceptance Criteria**:
- [ ] App starts successfully
- [ ] All routes registered
- [ ] CORS configured
- [ ] Logging works
- [ ] OpenAPI docs available
- [ ] Startup checks pass

**Tests**:
- Test app startup
- Test OpenAPI schema
- Test CORS

**Definition of Done**: API server runs and handles requests

---

### 1.7 Testing and Documentation

#### Task 1.7.1: Unit Tests
**Objective**: Create unit tests for core components

**Actions**:
- Create tests for:
  - Embedding service
  - BM25 retriever
  - RRF fusion
  - Reranker
  - Chunking
  - Metadata enrichment
  - Citation verification
- Use pytest fixtures
- Mock external services
- Aim for > 80% coverage on core logic

**Files**: 
- `tests/core/test_embedding_service.py`
- `tests/core/test_bm25_retriever.py`
- `tests/core/test_fusion.py`
- `tests/core/test_reranker.py`
- `tests/services/test_chunker.py`
- `tests/services/test_enricher.py`

**Dependencies**: All core component tasks

**Acceptance Criteria**:
- [ ] All core components tested
- [ ] Coverage > 80%
- [ ] Tests pass consistently
- [ ] Mocks used for external services

**Tests**: N/A (this is the test task)

**Definition of Done**: Unit tests pass with good coverage

---

#### Task 1.7.2: Integration Tests
**Objective**: Test end-to-end workflows

**Actions**:
- Create integration tests:
  - Full ingestion pipeline
  - Full Q&A workflow
  - API endpoints
  - Qdrant integration
- Use TestClient for API
- Set up test data
- Clean up after tests

**Files**: 
- `tests/integration/test_ingestion_pipeline.py`
- `tests/integration/test_qa_workflow.py`
- `tests/integration/test_api.py`
- `tests/fixtures/sample_documents/`

**Dependencies**: Tasks 1.3.4, 1.5.7, 1.6.5

**Acceptance Criteria**:
- [ ] End-to-end ingestion tested
- [ ] End-to-end Q&A tested
- [ ] API endpoints tested
- [ ] Tests use realistic data
- [ ] Cleanup works

**Tests**: N/A (this is the test task)

**Definition of Done**: Integration tests pass consistently

---

#### Task 1.7.3: Sample Data and Test Cases
**Objective**: Create sample documents and test questions

**Actions**:
- Create 5-10 sample documents:
  - Mix of .txt and .md
  - Various subjects (math, history, CS)
  - Different structures
  - ~1000-5000 words each
- Create 20 test question-answer pairs:
  - Factual questions
  - Conceptual questions
  - Multi-hop questions
  - Unsupported questions
  - Label expected answers

**Files**: 
- `tests/fixtures/sample_documents/*.txt`
- `tests/fixtures/sample_documents/*.md`
- `tests/fixtures/test_qa_pairs.json`

**Dependencies**: None

**Acceptance Criteria**:
- [ ] 5-10 documents created
- [ ] 20 Q&A pairs labeled
- [ ] Mix of question types
- [ ] Includes edge cases

**Tests**: N/A (test data)

**Definition of Done**: Sample data ready for testing

---

#### Task 1.7.4: Documentation
**Objective**: Create comprehensive documentation

**Actions**:
- Update README.md:
  - Project overview
  - Features
  - Architecture diagram
  - Setup instructions
  - Usage examples
  - API documentation
  - Configuration guide
  - Troubleshooting
- Create CONTRIBUTING.md
- Add docstrings to all public functions
- Generate API documentation

**Files**: 
- `README.md`
- `CONTRIBUTING.md`
- `docs/API.md`
- `docs/CONFIGURATION.md`

**Dependencies**: All previous tasks

**Acceptance Criteria**:
- [ ] README comprehensive
- [ ] Setup instructions clear
- [ ] API documented
- [ ] Configuration explained
- [ ] Examples provided

**Tests**: Manual review

**Definition of Done**: Documentation complete and accurate

---

### 1.8 End-to-End Validation

#### Task 1.8.1: Manual Testing
**Objective**: Perform manual end-to-end testing

**Actions**:
- Test complete workflow:
  1. Start Qdrant
  2. Start API server
  3. Ingest sample documents
  4. Ask test questions
  5. Verify answers and citations
  6. Test both modes
  7. Test error cases
- Document any issues
- Create test report

**Files**: 
- `tests/manual/TEST_REPORT.md`

**Dependencies**: Task 1.7.3

**Acceptance Criteria**:
- [ ] All sample docs ingest successfully
- [ ] 80%+ test questions answered correctly
- [ ] Citations are accurate
- [ ] Both modes work
- [ ] Errors handled gracefully

**Tests**: N/A (manual testing)

**Definition of Done**: System works end-to-end

---

#### Task 1.8.2: Performance Baseline
**Objective**: Measure baseline performance metrics

**Actions**:
- Measure and document:
  - Ingestion throughput (pages/hour)
  - Retrieval latency (p50, p95, p99)
  - Generation latency (p50, p95, p99)
  - End-to-end latency
  - Memory usage
  - Groq API costs per query
- Create performance report

**Files**: 
- `tests/performance/benchmark.py`
- `tests/performance/PERFORMANCE_REPORT.md`

**Dependencies**: Task 1.8.1

**Acceptance Criteria**:
- [ ] All metrics measured
- [ ] Results documented
- [ ] Baseline established for future comparison

**Tests**: Performance benchmark script

**Definition of Done**: Performance baseline documented

---

## Phase 2: Retrieval Optimization & Evaluation

### 2.1 Evaluation Framework

#### Task 2.1.1: Retrieval Evaluation
**Objective**: Implement retrieval quality metrics

**Actions**:
- Create `src/evaluation/retrieval_eval.py`:
  - Recall@k (k=1,3,5,10)
  - MRR (Mean Reciprocal Rank)
  - nDCG (Normalized Discounted Cumulative Gain)
  - Load labeled test set
  - Run evaluation on test queries
  - Compare baseline strategies

**Files**: 
- `src/evaluation/__init__.py`
- `src/evaluation/retrieval_eval.py`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] All metrics implemented correctly
- [ ] Evaluation runs on test set
- [ ] Results are reproducible

**Tests**:
- Test metric calculations
- Verify against known examples

**Definition of Done**: Retrieval metrics computed

---

#### Task 2.1.2: Answer Quality Evaluation
**Objective**: Evaluate answer correctness and groundedness

**Actions**:
- Create `src/evaluation/answer_eval.py`:
  - Answer correctness (manual labels)
  - Groundedness scoring
  - Citation accuracy
  - Integrate Ragas metrics (future)
  - Generate evaluation report

**Files**: 
- `src/evaluation/answer_eval.py`

**Dependencies**: Task 2.1.1

**Acceptance Criteria**:
- [ ] Groundedness computed
- [ ] Citation accuracy measured
- [ ] Report generated

**Tests**:
- Test with labeled examples

**Definition of Done**: Answer quality metrics available

---

#### Task 2.1.3: A/B Testing Framework
**Objective**: Compare retrieval strategies

**Actions**:
- Create framework to compare:
  - Dense-only vs. hybrid
  - Different chunk sizes
  - Different rerankers
  - Different embedding models
- Statistical significance testing
- Visualization of results

**Files**: 
- `src/evaluation/ab_testing.py`
- `scripts/run_ablation.py`

**Dependencies**: Tasks 2.1.1, 2.1.2

**Acceptance Criteria**:
- [ ] Can compare strategies
- [ ] Statistical tests included
- [ ] Results visualized

**Tests**:
- Test comparison logic

**Definition of Done**: A/B testing framework functional

---

### 2.2 Retrieval Improvements

#### Task 2.2.1: Query Expansion
**Objective**: Improve recall with query reformulation

**Actions**:
- Implement query expansion:
  - Generate synonyms
  - Add related terms
  - Use LLM for reformulation
  - Create multiple query variants
- Test impact on retrieval

**Files**: 
- `src/services/retrieval/query_expansion.py`

**Dependencies**: Task 2.1.1

**Acceptance Criteria**:
- [ ] Generates query variants
- [ ] Improves recall
- [ ] Doesn't hurt precision

**Tests**:
- Test on evaluation set
- Measure recall improvement

**Definition of Done**: Query expansion improves retrieval

---

#### Task 2.2.2: Chunk Size Tuning
**Objective**: Optimize chunk size for quality

**Actions**:
- Experiment with chunk sizes:
  - 200, 400, 600, 800 tokens
  - Measure impact on retrieval
  - Measure impact on answer quality
- Select optimal size

**Files**: 
- `scripts/tune_chunk_size.py`

**Dependencies**: Task 2.1.3

**Acceptance Criteria**:
- [ ] Multiple sizes tested
- [ ] Optimal size identified
- [ ] Results documented

**Tests**:
- Evaluation on test set

**Definition of Done**: Optimal chunk size determined

---

#### Task 2.2.3: Metadata Filtering
**Objective**: Enable filtering by document, section, etc.

**Actions**:
- Add filter parameters to API:
  - Filter by document
  - Filter by section
  - Filter by content type
- Implement in retrieval
- Test filtering

**Files**: 
- Update `src/models/api.py`
- Update `src/services/retrieval/hybrid_retriever.py`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] Filters work correctly
- [ ] API accepts filter params
- [ ] Retrieval respects filters

**Tests**:
- Test each filter type
- Test filter combinations

**Definition of Done**: Metadata filtering works

---

### 2.3 Advanced Features

#### Task 2.3.1: Conversation Context Management
**Objective**: Implement proper conversation history

**Actions**:
- Create `src/services/context/conversation_manager.py`:
  - Store conversation history (in-memory with TTL)
  - Resolve references ("it", "that", etc.)
  - Include previous Q&A in prompt
  - Limit context window
- Update workflow to use context

**Files**: 
- `src/services/context/__init__.py`
- `src/services/context/conversation_manager.py`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] Conversation history stored
- [ ] References resolved
- [ ] Previous context included
- [ ] Works across multiple turns

**Tests**:
- Test multi-turn conversation
- Test reference resolution

**Definition of Done**: Multi-turn conversation works

---

#### Task 2.3.2: Langfuse Integration
**Objective**: Add tracing and monitoring

**Actions**:
- Integrate Langfuse:
  - Trace workflow steps
  - Log retrieval results
  - Log generation inputs/outputs
  - Track costs and latency
- Add dashboards

**Files**: 
- Update `src/core/llm_client.py`
- Update `src/services/tutoring/workflow.py`
- `src/utils/tracing.py`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] All steps traced
- [ ] Viewable in Langfuse UI
- [ ] Costs tracked

**Tests**:
- Verify traces appear

**Definition of Done**: Langfuse tracing active

---

## Phase 3: Adaptive Tutoring & Learning

### 3.1 Student Modeling

#### Task 3.1.1: PostgreSQL Setup
**Objective**: Add PostgreSQL for student data

**Actions**:
- Add PostgreSQL to docker-compose
- Create database schema
- Set up SQLAlchemy models
- Create migration system (Alembic)

**Files**: 
- Update `docker-compose.yml`
- `src/models/db.py`
- `alembic/versions/*.py`

**Dependencies**: Phase 2 complete

**Acceptance Criteria**:
- [ ] PostgreSQL running
- [ ] Schema created
- [ ] Migrations work

**Tests**:
- Test database connection
- Test CRUD operations

**Definition of Done**: PostgreSQL integrated

---

#### Task 3.1.2: Student Progress Tracking
**Objective**: Track concept mastery over time

**Actions**:
- Implement progress tracking:
  - Track topics asked about
  - Track mastery level
  - Update based on interactions
  - Provide progress API

**Files**: 
- `src/services/learning/progress_tracker.py`
- `src/api/routes/progress.py`

**Dependencies**: Task 3.1.1

**Acceptance Criteria**:
- [ ] Progress tracked
- [ ] Mastery computed
- [ ] API returns progress

**Tests**:
- Test progress updates
- Test mastery calculation

**Definition of Done**: Progress tracking works

---

#### Task 3.1.3: Adaptive Difficulty
**Objective**: Adjust explanation difficulty based on mastery

**Actions**:
- Implement difficulty adaptation:
  - Detect student mastery level
  - Adjust prompt for explanation level
  - Provide beginner/intermediate/advanced
- Test adaptation

**Files**: 
- `src/services/tutoring/adaptive.py`
- Update prompts

**Dependencies**: Task 3.1.2

**Acceptance Criteria**:
- [ ] Difficulty adjusts
- [ ] Explanations appropriate for level
- [ ] Tested with users

**Tests**:
- Test each difficulty level
- Verify prompt changes

**Definition of Done**: Adaptive difficulty works

---

### 3.2 Teaching Features

#### Task 3.2.1: Quiz Generation
**Objective**: Generate quizzes from notes

**Actions**:
- Implement quiz generation:
  - Generate MCQ questions
  - Generate short answer questions
  - Base on retrieved content
  - Provide correct answers
- Add quiz API

**Files**: 
- `src/services/tutoring/quiz_generator.py`
- `src/api/routes/quiz.py`

**Dependencies**: Phase 2 complete

**Acceptance Criteria**:
- [ ] Generates valid questions
- [ ] Questions based on notes
- [ ] Multiple formats supported

**Tests**:
- Test quiz generation
- Verify question quality

**Definition of Done**: Quiz generation works

---

#### Task 3.2.2: Worked Examples
**Objective**: Generate step-by-step solutions

**Actions**:
- Implement worked example generation:
  - Detect when example needed
  - Generate step-by-step solution
  - Use retrieved content as basis
- Add to teaching mode

**Files**: 
- Update `src/services/tutoring/prompts.py`
- `src/services/tutoring/examples.py`

**Dependencies**: Phase 2 complete

**Acceptance Criteria**:
- [ ] Generates worked examples
- [ ] Steps are clear
- [ ] Grounded in notes

**Tests**:
- Test example generation
- Verify step quality

**Definition of Done**: Worked examples available

---

## Phase 4: Production Readiness

### 4.1 Security

#### Task 4.1.1: Authentication
**Objective**: Add JWT-based authentication

**Actions**:
- Implement authentication:
  - User registration/login
  - JWT token generation
  - Token validation middleware
  - Protect endpoints
- Add user model

**Files**: 
- `src/api/auth.py`
- `src/api/middleware/auth.py`

**Dependencies**: Task 3.1.1

**Acceptance Criteria**:
- [ ] Users can register/login
- [ ] Tokens issued
- [ ] Protected endpoints require auth

**Tests**:
- Test registration
- Test login
- Test protected endpoints

**Definition of Done**: Authentication works

---

#### Task 4.1.2: Rate Limiting
**Objective**: Prevent abuse with rate limits

**Actions**:
- Implement rate limiting:
  - Per-user limits
  - Per-IP limits
  - Different limits for endpoints
  - Return 429 on limit

**Files**: 
- `src/api/middleware/rate_limit.py`

**Dependencies**: Task 4.1.1

**Acceptance Criteria**:
- [ ] Limits enforced
- [ ] Configurable
- [ ] Returns correct status

**Tests**:
- Test limit enforcement
- Test limit reset

**Definition of Done**: Rate limiting active

---

### 4.2 Monitoring

#### Task 4.2.1: Structured Logging
**Objective**: Improve logging for production

**Actions**:
- Implement structured logging:
  - JSON format
  - Request ID tracking
  - Correlation IDs
  - Log aggregation ready
- Add log levels

**Files**: 
- `src/utils/logging.py`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] Logs in JSON
- [ ] Request tracking works
- [ ] Searchable logs

**Tests**:
- Verify log format

**Definition of Done**: Structured logging active

---

#### Task 4.2.2: Metrics and Alerts
**Objective**: Add Prometheus metrics

**Actions**:
- Implement metrics:
  - Request duration
  - Error rates
  - API costs
  - Qdrant queries
- Add Prometheus endpoint
- Create Grafana dashboard

**Files**: 
- `src/api/middleware/metrics.py`
- `docker/grafana/dashboards/*.json`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] Metrics exposed
- [ ] Dashboard created
- [ ] Alerts configured

**Tests**:
- Verify metrics collection

**Definition of Done**: Monitoring active

---

### 4.3 Deployment

#### Task 4.3.1: Docker Production Images
**Objective**: Create production Docker images

**Actions**:
- Create production Dockerfile:
  - Multi-stage build
  - Minimal image size
  - Security best practices
  - Health checks
- Create docker-compose for prod

**Files**: 
- `Dockerfile`
- `docker-compose.prod.yml`

**Dependencies**: Phase 1 complete

**Acceptance Criteria**:
- [ ] Images build successfully
- [ ] Images optimized
- [ ] Health checks work

**Tests**:
- Test image build
- Test container startup

**Definition of Done**: Production images ready

---

#### Task 4.3.2: Kubernetes Manifests (Optional)
**Objective**: Support Kubernetes deployment

**Actions**:
- Create K8s manifests:
  - Deployment
  - Service
  - ConfigMap
  - Secrets
  - Ingress
- Add Helm chart

**Files**: 
- `k8s/*.yaml`
- `helm/tutor/`

**Dependencies**: Task 4.3.1

**Acceptance Criteria**:
- [ ] Manifests valid
- [ ] Deploys successfully
- [ ] Scales correctly

**Tests**:
- Test deployment

**Definition of Done**: K8s deployment works

---

## Task Summary by Phase

### Phase 1 (MVP): 26 tasks
- Project setup: 4 tasks
- Core components: 6 tasks
- Ingestion: 4 tasks
- Retrieval: 3 tasks
- LangGraph workflow: 6 tasks
- API: 5 tasks
- Testing: 4 tasks
- Validation: 2 tasks

### Phase 2 (Optimization): 8 tasks
- Evaluation: 3 tasks
- Improvements: 3 tasks
- Advanced features: 2 tasks

### Phase 3 (Adaptive Learning): 5 tasks
- Student modeling: 3 tasks
- Teaching features: 2 tasks

### Phase 4 (Production): 6 tasks
- Security: 2 tasks
- Monitoring: 2 tasks
- Deployment: 2 tasks

**Total: 45 tasks across 4 phases**

---

## Critical Path for MVP (Phase 1)

The following tasks are on the critical path and must be completed in order:

1. Project setup (1.1.1 → 1.1.4)
2. Core components (1.2.1 → 1.2.6)
3. Ingestion pipeline (1.3.1 → 1.3.4)
4. Retrieval system (1.4.1 → 1.4.3)
5. LangGraph workflow (1.5.1 → 1.5.7)
6. API layer (1.6.1 → 1.6.5)
7. Testing (1.7.1 → 1.7.4)
8. Validation (1.8.1 → 1.8.2)

Estimated time for MVP: **2-3 weeks of focused development**

---

## Approval Checklist

- [ ] Task breakdown reviewed
- [ ] Phase priorities confirmed
- [ ] MVP scope agreed upon
- [ ] Task dependencies understood
- [ ] Acceptance criteria clear
- [ ] Testing strategy approved
- [ ] Ready to begin implementation

**Next Steps After Approval**:
1. Create project steering rules
2. Begin Phase 1, Task 1.1.1
3. Implement iteratively with testing
4. Review after MVP completion
