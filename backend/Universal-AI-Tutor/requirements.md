# Universal AI Tutor — Requirements Specification

## Document Information
- **Version**: 1.0
- **Date**: November 11, 2026
- **Status**: Draft for Approval

---

## 1. Executive Summary

The Universal AI Tutor is a production-oriented, subject-independent intelligent learning platform that transforms text-based educational notes into an AI-powered teaching assistant. The system must support ANY educational subject through source-grounded question answering, clear explanations, and eventually adaptive learning.

### Key Differentiators
- **Universal**: No subject-specific assumptions (mathematics, CS, history, etc.)
- **Source-Grounded**: All answers traced to uploaded notes with citations
- **Production-Ready**: Professional engineering, testing, monitoring, and scalability
- **Retrieval-Optimized**: Hybrid search + reranking + context expansion
- **Intelligent Orchestration**: LangGraph-based deterministic tutoring workflows

---

## 2. Core Requirements

### 2.1 Functional Requirements

#### FR-1: Knowledge Ingestion
- **FR-1.1**: Accept text files (.txt) and Markdown files (.md) for ingestion
- **FR-1.2**: Parse and preserve document structure (headings, sections, lists, code blocks)
- **FR-1.3**: Create hierarchical chunk representations with parent-child relationships
- **FR-1.4**: Enrich chunks with contextual metadata (document, chapter, section, topic)
- **FR-1.5**: Generate dense embeddings using BGE-small-en-v1.5
- **FR-1.6**: Create BM25 sparse representations for keyword matching
- **FR-1.7**: Store indexed content in Qdrant with metadata
- **FR-1.8**: Support deterministic reindexing without duplicates
- **FR-1.9**: Preserve source traceability for all indexed content
- **FR-1.10**: Future support for PDFs, slides, images (architecture only, not implemented)

#### FR-2: Question Answering
- **FR-2.1**: Accept natural language questions via REST API
- **FR-2.2**: Perform hybrid retrieval (dense + BM25)
- **FR-2.3**: Fuse results using Reciprocal Rank Fusion (RRF)
- **FR-2.4**: Rerank using cross-encoder (ms-marco-MiniLM-L-6-v2)
- **FR-2.5**: Expand retrieved chunks with parent context when needed
- **FR-2.6**: Assess evidence sufficiency before generation
- **FR-2.7**: Generate grounded answers using Groq API
- **FR-2.8**: Verify answer citations match retrieved evidence
- **FR-2.9**: Return answers with source references and confidence
- **FR-2.10**: Handle questions not answered by notes explicitly

#### FR-3: Tutoring Modes
- **FR-3.1**: **Strict Notes Mode**: Answer only from notes, cite sources, admit gaps
- **FR-3.2**: **Teaching Mode**: Use notes as primary source, add explanations and examples, distinguish model knowledge from notes
- **FR-3.3**: Support mode selection via API parameter

#### FR-4: Multi-Turn Conversation
- **FR-4.1**: Maintain conversation context across multiple questions
- **FR-4.2**: Resolve references to previous questions and answers
- **FR-4.3**: Support follow-up questions and clarifications
- **FR-4.4**: Store conversation history per session

#### FR-5: API and Interface
- **FR-5.1**: FastAPI REST endpoints for ingestion and queries
- **FR-5.2**: Async request handling where beneficial
- **FR-5.3**: Request/response validation using Pydantic
- **FR-5.4**: Auto-generated API documentation (OpenAPI/Swagger)
- **FR-5.5**: Structured error responses with appropriate HTTP status codes

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: Retrieval latency < 2 seconds (p95)
- **NFR-1.2**: End-to-end answer generation < 10 seconds (p95)
- **NFR-1.3**: Support concurrent requests (at least 10 simultaneous users)
- **NFR-1.4**: Ingestion throughput: 1000 pages per hour minimum

#### NFR-2: Quality
- **NFR-2.1**: Answer correctness > 85% on evaluation set
- **NFR-2.2**: Answer groundedness/faithfulness > 90%
- **NFR-2.3**: Citation accuracy > 95%
- **NFR-2.4**: Recall@5 > 80% for known questions

#### NFR-3: Reliability
- **NFR-3.1**: API uptime > 99% during operation
- **NFR-3.2**: Graceful handling of LLM API failures with retries
- **NFR-3.3**: Rate limit compliance for external APIs
- **NFR-3.4**: Deterministic behavior for identical inputs
- **NFR-3.5**: Database connection resilience

#### NFR-4: Maintainability
- **NFR-4.1**: Type hints throughout Python codebase
- **NFR-4.2**: Modular architecture with clear separation of concerns
- **NFR-4.3**: Configuration via environment variables
- **NFR-4.4**: Comprehensive structured logging
- **NFR-4.5**: Code coverage > 80% for critical paths
- **NFR-4.6**: Clear documentation for all public APIs

#### NFR-5: Security
- **NFR-5.1**: No API keys or secrets in version control
- **NFR-5.2**: Input validation and sanitization
- **NFR-5.3**: Future-ready authentication architecture
- **NFR-5.4**: SQL injection prevention (for future PostgreSQL)
- **NFR-5.5**: Rate limiting on API endpoints

#### NFR-6: Resource Constraints
- **NFR-6.1**: CPU-compatible embeddings (no GPU required)
- **NFR-6.2**: Memory footprint < 8 GB during normal operation
- **NFR-6.3**: Optional GPU acceleration for faster batch embedding
- **NFR-6.4**: Cost-conscious LLM usage (prefer efficient models)

---

## 3. System Boundaries

### In Scope (Phase 1)
- Text file ingestion (.txt, .md)
- Hybrid retrieval with reranking
- LangGraph orchestrated Q&A
- Source-grounded answer generation
- Basic conversation context
- REST API with FastAPI
- Local Qdrant vector database
- Groq API for LLM generation
- Automated testing
- Evaluation framework

### In Scope (Future Phases)
- PDF, image, video ingestion
- Advanced adaptive learning
- Student progress tracking (PostgreSQL)
- Quiz generation and assessment
- Multi-modal retrieval
- Langfuse tracing
- Advanced graph retrieval
- Local Ollama support
- Multi-tenancy and authentication
- Production deployment

### Out of Scope
- Real-time collaboration features
- Mobile applications
- Custom LLM fine-tuning
- Speech/audio interface
- Gamification features
- Integration with existing LMS platforms
- Subject-specific tutoring logic

---

## 4. User Stories

### US-1: Upload and Index Notes
**As a** teacher or student  
**I want to** upload my course notes in text or Markdown format  
**So that** the AI tutor can answer questions based on my specific materials

**Acceptance Criteria:**
- Upload endpoint accepts .txt and .md files
- Files are parsed preserving structure
- Content is indexed in Qdrant
- Duplicate uploads are handled gracefully
- Progress/status is returned

### US-2: Ask Questions About Notes
**As a** student  
**I want to** ask natural language questions about uploaded notes  
**So that** I can get accurate answers with source references

**Acceptance Criteria:**
- Question endpoint accepts natural language queries
- System retrieves relevant passages
- Answer is generated with citations
- Sources are traceable to original documents
- Response time < 10 seconds

### US-3: Handle Unknown Questions
**As a** student  
**I want to** receive honest responses when information isn't in the notes  
**So that** I'm not misled by fabricated answers

**Acceptance Criteria:**
- System detects insufficient evidence
- Clear message indicates unavailable information
- No hallucinated facts or sources
- Suggestions for related available topics (optional)

### US-4: Follow-Up Questions
**As a** student  
**I want to** ask follow-up questions in a conversation  
**So that** I can explore topics in depth

**Acceptance Criteria:**
- System maintains conversation context
- References to "it", "that concept", etc. are resolved
- Previous Q&A pairs inform current response
- Conversation history is retrievable

### US-5: Choose Tutoring Mode
**As a** student  
**I want to** select between strict and teaching modes  
**So that** I can control whether the tutor uses only my notes or adds general knowledge

**Acceptance Criteria:**
- Mode parameter in API request
- Strict mode answers only from notes
- Teaching mode adds explanations
- Mode affects answer generation prompt
- Distinction between sources is clear

---

## 5. Technical Constraints

### Hardware Environment
- **Development Machine**: Windows, 16 GB RAM, NVIDIA RTX 3050 4 GB
- **Inference**: Prefer CPU-compatible or hosted API solutions
- **GPU**: Optional for faster batch processing, not required

### Technology Stack (Fixed)
- **Python**: 3.11+
- **API Framework**: FastAPI
- **Validation**: Pydantic
- **Indexing**: LlamaIndex
- **Vector DB**: Qdrant
- **Orchestration**: LangGraph
- **Embeddings**: BGE-small-en-v1.5 (initial)
- **Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2 (initial)
- **LLM**: Groq API (initial)
- **Future DB**: PostgreSQL for student data

### External Dependencies
- Groq API for LLM inference (requires API key)
- Hugging Face models for embeddings and reranking
- Qdrant server (local Docker or remote)

---

## 6. Data Requirements

### 6.1 Input Data
- **Format**: Plain text (.txt), Markdown (.md)
- **Size**: Individual files up to 10 MB
- **Volume**: Support 100+ documents, 10,000+ pages
- **Encoding**: UTF-8
- **Structure**: Preserve headings, lists, code blocks, tables, formulas

### 6.2 Processed Data
- **Chunks**: 200-800 tokens, context-aware boundaries
- **Embeddings**: 384-dimensional vectors (BGE-small)
- **Metadata**: Document ID, section, parent chunk, source location, timestamp
- **Indexes**: Dense (HNSW) + BM25 (inverted)

### 6.3 Output Data
- **Answers**: Natural language text
- **Citations**: Document name, section, excerpt, confidence
- **Metadata**: Retrieved chunks, rerank scores, generation cost

---

## 7. Quality Attributes

### Correctness
- Answers must be factually grounded in source material
- Citations must be verifiable and accurate
- No fabricated information in strict mode

### Usability
- Clear API documentation
- Intuitive request/response format
- Helpful error messages

### Testability
- Unit tests for all core functions
- Integration tests for API endpoints
- Evaluation harness for retrieval and generation quality

### Extensibility
- Model provider abstraction (Groq → Ollama)
- Embedding model swapping
- Future multimodal ingestion
- Plugin architecture for advanced retrieval

---

## 8. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Groq API rate limits | High | Medium | Implement exponential backoff, request queuing, usage monitoring |
| Poor retrieval quality | High | Medium | Hybrid search, reranking, systematic evaluation, tuning |
| Hallucination in answers | High | Medium | Evidence sufficiency check, citation verification, groundedness scoring |
| Memory constraints (16 GB) | Medium | Low | CPU embeddings, batch processing, streaming where possible |
| Slow ingestion for large docs | Medium | Medium | Async processing, progress tracking, incremental indexing |
| Context window limits | Medium | Medium | Chunk size tuning, context pruning, hierarchical retrieval |
| Citation inaccuracy | High | Low | Post-generation verification, confidence thresholds |

---

## 9. Success Criteria

### Minimum Viable Product (Phase 1)
- [ ] Ingest 10+ text documents successfully
- [ ] Answer 20 test questions with > 80% correctness
- [ ] Provide verifiable citations for all answers
- [ ] Handle 5 unsupported questions correctly
- [ ] End-to-end latency < 10 seconds
- [ ] Pass 90% of unit and integration tests
- [ ] Complete API documentation
- [ ] Reproducible Docker setup

### Future Success Metrics
- Recall@5 > 80%
- MRR > 0.7
- Answer faithfulness > 90%
- Student satisfaction > 4.0/5.0
- Production uptime > 99%

---

## 10. Dependencies and Assumptions

### Assumptions
- User has Groq API access and key
- Docker Desktop available for local Qdrant
- Python 3.11+ installed
- Network access for downloading models
- Notes are in English (initial phase)

### External Dependencies
- Groq API availability and pricing
- Hugging Face model availability
- Qdrant compatibility with Windows
- LangGraph stability and updates

---

## 11. Glossary

- **Chunk**: A semantically coherent segment of text (200-800 tokens)
- **Dense Retrieval**: Semantic similarity search using embeddings
- **BM25**: Sparse keyword-based retrieval algorithm
- **RRF**: Reciprocal Rank Fusion for combining retrieval results
- **Reranking**: Reordering retrieved results by relevance using cross-encoder
- **Grounding**: Ensuring answers are supported by source evidence
- **Parent Context**: Full section/document containing a retrieved chunk
- **Faithfulness**: Degree to which answer content comes from sources
- **Hallucination**: Model-generated content not supported by sources

---

## Approval Checklist

- [ ] Requirements reviewed by stakeholder
- [ ] Technical stack confirmed
- [ ] Resource constraints validated
- [ ] Success criteria agreed upon
- [ ] Risks acknowledged
- [ ] Ready to proceed to design phase
