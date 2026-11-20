# Universal AI Tutor — Project Summary

## 📋 Document Overview

**Status**: Specification Complete — Awaiting Approval to Begin Implementation  
**Date**: November 11, 2026  
**Version**: 1.0

---

## 🎯 Project Vision

Build a **production-ready, subject-independent AI tutoring platform** that transforms text-based educational notes into an intelligent, source-grounded AI teacher capable of teaching ANY subject with verified citations and adaptive explanations.

### Core Differentiators
- ✅ **Universal**: No subject-specific assumptions (works for math, CS, history, etc.)
- ✅ **Source-Grounded**: All answers traceable to uploaded notes with citations
- ✅ **Production-Ready**: Professional engineering, testing, and monitoring
- ✅ **Retrieval-Optimized**: Hybrid search + reranking + context expansion
- ✅ **Intelligent**: LangGraph-based deterministic tutoring workflows

---

## 📚 Documentation Structure

This specification consists of four main documents:

### 1. **requirements.md** — What We're Building
- Functional and non-functional requirements
- User stories and success criteria
- System boundaries and constraints
- Quality attributes and risk mitigation

### 2. **design.md** — How We're Building It
- System architecture and layer design
- Component specifications and interactions
- Data models and API design
- Technology choices and tradeoffs
- Deployment and monitoring strategy

### 3. **tasks.md** — Implementation Roadmap
- **Phase 1**: Functional RAG Foundation (MVP) — 26 tasks
- **Phase 2**: Retrieval Optimization & Evaluation — 8 tasks
- **Phase 3**: Adaptive Tutoring & Learning — 5 tasks
- **Phase 4**: Production Readiness — 6 tasks
- Each task includes objectives, dependencies, acceptance criteria, and tests

### 4. **Steering Files** — Development Standards
- `.kiro/steering/python-quality.md` — Code quality and style standards
- `.kiro/steering/testing-guidelines.md` — Testing philosophy and practices
- `.kiro/steering/rag-best-practices.md` — RAG-specific implementation guidelines

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI REST API                             │
│         (Ingestion, Query, Health Check Endpoints)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   LangGraph Tutoring Workflow                    │
│  Query Understanding → Retrieval → Evidence Check →              │
│  Generation → Citation Verification → Response                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Core Components (Python Services)                   │
│  • LlamaIndex Ingestion (Hierarchical Chunking)                 │
│  • Embedding Service (BGE-small-en-v1.5)                        │
│  • Hybrid Retrieval (Dense + BM25 + RRF Fusion)                 │
│  • Cross-Encoder Reranking                                      │
│  • Groq LLM Client (Answer Generation)                          │
│  • Citation Verifier                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Data Layer                                    │
│  • Qdrant Vector DB (Dense + BM25 Sparse)                       │
│  • Future: PostgreSQL (Student Progress)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend & API
- **Python 3.11+** with type hints
- **FastAPI** for REST API
- **Pydantic** for validation and settings
- **Uvicorn** ASGI server

### Knowledge Processing
- **LlamaIndex** for structure-aware ingestion and hierarchical chunking
- Supports .txt and .md initially (PDF/images future)

### Retrieval & Search
- **Qdrant** vector database (dense + sparse/BM25)
- **BGE-small-en-v1.5** embeddings (384-dim, CPU-friendly)
- **cross-encoder/ms-marco-MiniLM-L-6-v2** reranking
- Reciprocal Rank Fusion (RRF) for hybrid search

### LLM & Orchestration
- **Groq API** for fast LLM inference (llama-3.1-70b-versatile)
- **LangGraph** for deterministic tutoring workflows
- Configurable prompt templates for strict vs. teaching modes

### Future Enhancements
- **PostgreSQL** for student progress and conversation history
- **Ragas** for RAG evaluation
- **Langfuse** for LLM tracing and monitoring
- **Ollama** support for local inference

---

## 🚀 Phase 1 MVP — Feature List

### ✅ Core Capabilities (First Milestone)

1. **Document Ingestion**
   - Upload .txt and .md files
   - Preserve document structure (headings, sections, code blocks)
   - Hierarchical chunking (200-800 tokens)
   - Metadata enrichment (doc_id, section, parent_id, timestamps)
   - Dense and BM25 indexing
   - Qdrant storage with deduplication

2. **Intelligent Retrieval**
   - Hybrid search (dense + BM25)
   - RRF fusion of results
   - Cross-encoder reranking
   - Parent context expansion for small chunks
   - Configurable top-k results

3. **Tutoring Modes**
   - **Strict Mode**: Answer only from notes, cite sources, admit gaps
   - **Teaching Mode**: Use notes + add explanations, distinguish sources

4. **LangGraph Q&A Workflow**
   - Query understanding and preprocessing
   - Hybrid retrieval with reranking
   - Evidence sufficiency assessment
   - Retry logic for insufficient evidence
   - Grounded answer generation
   - Citation verification
   - Response formatting

5. **REST API**
   - `POST /api/v1/ingest` — Upload and index documents
   - `POST /api/v1/ask` — Ask questions with mode selection
   - `GET /api/v1/health` — Health check
   - Auto-generated OpenAPI documentation

6. **Quality Assurance**
   - Comprehensive unit tests (80%+ coverage)
   - Integration tests for end-to-end workflows
   - Evaluation framework (Recall@k, MRR, groundedness)
   - Performance benchmarking
   - Sample test data and Q&A pairs

---

## 📊 Success Criteria

### Phase 1 MVP Acceptance
- [ ] Ingest 10+ text documents successfully
- [ ] Answer 20 test questions with > 80% correctness
- [ ] Provide verifiable citations for all answers
- [ ] Handle 5 unsupported questions correctly (admit gaps)
- [ ] End-to-end latency < 10 seconds
- [ ] Pass 90% of unit and integration tests
- [ ] Complete API documentation
- [ ] Reproducible Docker setup

### Quality Targets
- **Retrieval**: Recall@5 > 80%, MRR > 0.7
- **Generation**: Answer faithfulness > 90%, citation accuracy > 95%
- **Performance**: Retrieval < 2s (p95), end-to-end < 10s (p95)
- **Testing**: Core logic > 80% coverage, critical paths 100%

---

## 🛠️ Development Environment

### Requirements
- **OS**: Windows (or Linux/Mac)
- **Memory**: 16 GB RAM
- **GPU**: Optional NVIDIA RTX 3050 4GB (CPU-friendly by default)
- **Python**: 3.11+
- **Docker**: For local Qdrant

### Setup (Quick Start)
```powershell
# Clone and setup
cd c:\Projects\Universal-AI-Tutor
pip install -e .

# Configure environment
copy .env.example .env
# Edit .env with your GROQ_API_KEY

# Start Qdrant
docker compose up -d

# Run API server
uvicorn src.main:app --reload

# Run tests
pytest
```

---

## 📈 Development Phases

### Phase 1: Functional RAG Foundation (2-3 weeks)
**Goal**: Working MVP with ingestion, retrieval, and answer generation

**Key Deliverables**:
- Complete ingestion pipeline
- Hybrid retrieval with reranking
- LangGraph Q&A workflow
- FastAPI endpoints
- Comprehensive tests
- Documentation

**Tasks**: 26 (See tasks.md for breakdown)

### Phase 2: Retrieval Optimization (1-2 weeks)
**Goal**: Improve retrieval quality and establish systematic evaluation

**Key Deliverables**:
- Evaluation framework (Recall@k, MRR, nDCG, groundedness)
- Query expansion
- Chunk size tuning
- Metadata filtering
- Conversation context management
- Langfuse tracing integration

**Tasks**: 8

### Phase 3: Adaptive Tutoring (2-3 weeks)
**Goal**: Student memory, progress tracking, adaptive learning

**Key Deliverables**:
- PostgreSQL for student data
- Progress tracking and concept mastery
- Adaptive difficulty levels
- Quiz generation
- Worked examples generation

**Tasks**: 5

### Phase 4: Production Readiness (2 weeks)
**Goal**: Security, monitoring, scalability, deployment

**Key Deliverables**:
- JWT authentication
- Rate limiting
- Structured logging and metrics
- Prometheus/Grafana dashboards
- Production Docker images
- Kubernetes manifests (optional)

**Tasks**: 6

---

## ⚠️ Critical Design Decisions

### 1. Chunking Strategy
- **Target**: 400 tokens average (200-800 range)
- **Method**: LlamaIndex SemanticSplitterNodeParser or HierarchicalNodeParser
- **Rationale**: Balance context completeness and retrieval precision

### 2. Hybrid Retrieval
- **Dense**: Top-20 via cosine similarity
- **BM25**: Top-20 via keyword matching
- **Fusion**: RRF with k=60
- **Reranking**: Top-5 after cross-encoder
- **Rationale**: Combines semantic and keyword matching for robustness

### 3. Two Tutoring Modes
- **Strict**: Only notes, cite sources, admit gaps → no hallucinations
- **Teaching**: Notes + explanations → better learning experience
- **Rationale**: User controls hallucination vs. helpfulness tradeoff

### 4. Evidence Assessment
- Check before generation: sufficient chunks, good scores, term coverage
- Retry up to 2 times with query reformulation
- Admit ignorance if still insufficient
- **Rationale**: Prevent low-quality answers from poor retrieval

### 5. Citation Verification
- Post-generation check: claims match sources, citations valid
- Compute groundedness score
- Flag unsupported claims
- **Rationale**: Ensure answer-source alignment

---

## 🔒 Non-Negotiable Principles

1. **Source Grounding is Mandatory**
   - Every answer must be traceable to source material
   - Citations must be accurate and verifiable
   - Never fabricate sources or facts

2. **Admit Ignorance**
   - When information is not in notes, say so explicitly
   - No hallucinations in strict mode
   - Clear distinction in teaching mode

3. **Preserve Traceability**
   - Maintain source metadata through entire pipeline
   - Every chunk traceable to original document and position
   - Parent-child relationships preserved

4. **Test Everything**
   - 80%+ coverage for core logic
   - 100% for critical paths (retrieval, generation, citation)
   - Both success and failure cases
   - Real evaluation metrics, not just unit tests

5. **Security by Default**
   - No secrets in version control
   - Input validation on all endpoints
   - Rate limiting and timeouts
   - Groq API cost tracking

---

## 📝 Open Questions (Pending Approval)

### Q1: Chunking Parameters
**Question**: Exact token size (200-800 target)?  
**Recommendation**: 400 tokens mean, 256-512 hard limits (BGE-small max is 512)  
**Decision**: ✅ **APPROVED**

### Q2: BM25 Implementation
**Question**: Use Qdrant sparse vectors or separate index?  
**Recommendation**: Qdrant native full-text index with built-in BM25  
**Decision**: ✅ **APPROVED**

### Q3: Context Window Management
**Question**: How to handle when retrieved context exceeds LLM limit?  
**Recommendation**: Truncate to most relevant chunks by rerank score  
**Decision**: ✅ **APPROVED**

### Q4: Conversation Storage (Phase 1)
**Question**: Where to store conversation history in MVP?  
**Recommendation**: In-memory TTLCache (simple, no infrastructure)  
**Decision**: ✅ **APPROVED**

### Q5: Citation Format
**Question**: Inline citations [1] or named [Document, Section]?  
**Recommendation**: Named format for clarity: `[Geometry Notes, Right Triangles]`  
**Decision**: ✅ **APPROVED**

---

## 🎬 Next Steps

### Before Starting Implementation

1. **Review Documents**
   - [ ] Read requirements.md thoroughly
   - [ ] Review design.md architecture
   - [ ] Understand tasks.md breakdown
   - [ ] Review steering files for standards

2. **Approve Key Decisions**
   - [ ] Confirm technology stack choices
   - [ ] Resolve open questions above
   - [ ] Agree on success criteria
   - [ ] Confirm MVP scope

3. **Environment Setup**
   - [ ] Obtain Groq API key
   - [ ] Install Docker Desktop
   - [ ] Verify Python 3.11+ installed
   - [ ] Test Qdrant startup

4. **Begin Phase 1**
   - Start with Task 1.1.1: Initialize Project Structure
   - Follow task order in tasks.md
   - Implement with steering guidelines
   - Test continuously

### Development Workflow

1. **For Each Task**:
   - Read task description and acceptance criteria
   - Implement with type hints and docstrings
   - Write tests (unit + integration as needed)
   - Verify tests pass
   - Update documentation
   - Commit with clear message

2. **Review Checkpoints**:
   - After core components (Task 1.2.6)
   - After ingestion pipeline (Task 1.3.4)
   - After retrieval system (Task 1.4.3)
   - After LangGraph workflow (Task 1.5.7)
   - After API layer (Task 1.6.5)
   - After MVP validation (Task 1.8.2)

3. **Quality Gates**:
   - All tests must pass before proceeding
   - Code review checklist completed
   - Documentation updated
   - Performance within targets

---

## 📖 Key Files Reference

### Documentation
- `requirements.md` — Full requirements specification
- `design.md` — Architecture and design decisions
- `tasks.md` — Phased implementation roadmap
- `PROJECT_SUMMARY.md` — This document

### Steering Rules (Auto-loaded)
- `.kiro/steering/python-quality.md` — Code quality standards
- `.kiro/steering/testing-guidelines.md` — Testing philosophy
- `.kiro/steering/rag-best-practices.md` — RAG implementation guidelines

### Configuration (To be created)
- `.env.example` — Environment variable template
- `pyproject.toml` — Dependencies and project metadata
- `docker-compose.yml` — Qdrant and services
- `README.md` — Quick start guide

---

## 🚨 Important Reminders

### Before Writing Code
- ✋ **STOP**: Do NOT begin implementation until specification is approved
- ✋ **STOP**: Do NOT make real Groq API requests without explicit approval
- ✋ **STOP**: Verify all environment variables configured before testing

### During Development
- ⚠️ **Follow steering guidelines**: Type hints, docstrings, tests, error handling
- ⚠️ **Test continuously**: Write tests as you code, not after
- ⚠️ **Maintain traceability**: Every chunk needs source metadata
- ⚠️ **Verify citations**: Never fabricate sources

### Quality Standards
- ✅ **Code quality**: Type hints, docstrings, proper error handling
- ✅ **Test coverage**: 80%+ core logic, 100% critical paths
- ✅ **RAG grounding**: Citations verified, no hallucinations
- ✅ **Performance**: Retrieval < 2s, end-to-end < 10s

---

## 💡 Success Philosophy

### This Project Will Succeed By

1. **Clear Requirements**: We know exactly what we're building
2. **Solid Architecture**: Well-designed, modular, testable
3. **Incremental Development**: MVP first, then enhance
4. **Quality Focus**: Test early, test often, measure everything
5. **RAG Best Practices**: Grounding, citations, evidence assessment
6. **Production Mindset**: Security, monitoring, documentation from day one

### This Project Will Fail If

1. ❌ We skip testing or documentation
2. ❌ We allow hallucinations or fake citations
3. ❌ We overcomplicate the MVP scope
4. ❌ We ignore performance or quality metrics
5. ❌ We hardcode secrets or skip security
6. ❌ We don't measure retrieval quality

---

## 📊 Estimated Timeline

- **Specification Review**: 1-2 days
- **Phase 1 (MVP)**: 2-3 weeks
- **Phase 2 (Optimization)**: 1-2 weeks
- **Phase 3 (Adaptive)**: 2-3 weeks
- **Phase 4 (Production)**: 2 weeks

**Total**: ~8-10 weeks to production-ready system

---

## ✅ Approval Checklist

Before proceeding to implementation:

- [ ] Requirements reviewed and understood
- [ ] Architecture approved
- [ ] Technology stack confirmed
- [ ] MVP scope agreed upon
- [ ] Success criteria clear
- [ ] Open questions resolved
- [ ] Development environment ready
- [ ] Groq API key obtained
- [ ] Steering guidelines understood
- [ ] Ready to begin Task 1.1.1

---

## 🎯 Vision Statement

> "Build a universal AI tutor that teaches any subject with verified source citations, never hallucinates, and adapts to student understanding — setting the standard for RAG-based educational AI systems."

---

**Status**: ⏸️ Specification Complete — Awaiting Approval

**Next Action**: Review this summary and all specification documents, then approve to begin Phase 1 implementation.

---

*Generated: November 11, 2026*  
*Version: 1.0*  
*Project: Universal AI Tutor*
