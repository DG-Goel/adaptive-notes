# RAG System Best Practices

## Core Principles

### 1. Source Grounding is Mandatory
Every answer must be traceable to source material. This is non-negotiable for the tutor system.

**Implementation Requirements:**
- Preserve document metadata through entire pipeline
- Maintain chunk-to-document relationships
- Include source references in all intermediate steps
- Verify citations before returning answers

### 2. Admit Ignorance
When information is not available in the notes, say so clearly. Never hallucinate.

**Good Responses:**
- "I don't have enough information in your notes to answer this question."
- "Your notes don't cover this topic. The closest related information I found is..."
- "I can only partially answer based on your notes: [partial answer]. For a complete answer, additional material would be needed."

**Bad Responses:**
- Generating answers not supported by sources
- Providing citations to non-existent documents
- Mixing model knowledge with source material without clear distinction

### 3. Quality Over Speed
Retrieval quality is more important than latency. Better to take 5 seconds and return the right context than 1 second with wrong results.

## Ingestion Pipeline Best Practices

### Chunk Size Strategy
- **Target**: 400 tokens average
- **Range**: 200-800 tokens
- **Rationale**: Balance between context completeness and retrieval precision

**Chunking Rules:**
1. Never split code blocks mid-function
2. Never split mathematical formulas
3. Never split tables or lists
4. Keep section headings with their content
5. Preserve paragraph boundaries when possible

### Metadata Enrichment
Every chunk must include:
```python
{
    "doc_id": "unique_document_identifier",
    "doc_title": "Human readable document name",
    "doc_path": "/path/to/original/file.txt",
    "section_title": "Current section heading",
    "parent_id": "parent_chunk_id_or_null",
    "chunk_index": 0,  # Position in document
    "content_type": "text",  # text, code, formula, table
    "indexed_at": "2026-11-11T10:30:00Z",
    "version_hash": "sha256_of_content"
}
```

### Deduplication Strategy
- Compute hash of (content + doc_path)
- Check for existing hash before indexing
- Support explicit overwrite flag
- Log skipped duplicates

## Retrieval Best Practices

### Hybrid Search Configuration
```python
# Dense retrieval
dense_top_k = 20  # Cast wide net
similarity_metric = "cosine"

# BM25 sparse retrieval  
bm25_top_k = 20  # Same size for balance
bm25_k1 = 1.5  # Term frequency saturation
bm25_b = 0.75  # Length normalization

# RRF Fusion
rrf_k = 60  # Standard parameter, tune if needed

# Reranking
rerank_top_k = 5  # Final results returned
```

### When to Expand Context
Expand parent context when:
- Retrieved chunk < 300 tokens
- Rerank score < 0.6 (low confidence)
- Chunk is missing critical context (based on metadata)

**Expansion Limits:**
- Maximum expanded context: 1500 tokens
- Always include original chunk
- Fetch parent and optionally siblings
- Maintain source attribution

### Query Preprocessing
```python
def preprocess_query(query: str, conversation_history: List[dict]) -> str:
    """
    Preprocess query for better retrieval.
    
    Steps:
    1. Normalize whitespace
    2. Resolve references using conversation history ("it", "that", etc.)
    3. Expand abbreviations if needed
    4. Keep original intent
    """
    # Note: Don't over-process, keep semantic meaning
```

## Generation Best Practices

### Prompt Engineering

**Strict Mode Template:**
```python
STRICT_PROMPT = """You are an AI tutor. Answer the question using ONLY the provided context from the student's notes.

Context from notes:
{context_chunks}

Question: {question}

Critical Rules:
1. ONLY use information explicitly stated in the context above
2. Cite sources using [Document Name, Section] format
3. If the context doesn't contain enough information, respond: "I don't have enough information in your notes to answer this question."
4. Do NOT add external knowledge, examples, or explanations not in the context
5. Be precise and accurate
6. If partially answered, clearly state what's missing

Answer:"""
```

**Teaching Mode Template:**
```python
TEACHING_PROMPT = """You are an AI tutor. Answer the question primarily using the provided context, but you may add explanations and examples to help understanding.

Context from student's notes:
{context_chunks}

Question: {question}

Guidelines:
1. Use the context as the PRIMARY source - cite as [Document, Section]
2. You may add clarifying explanations and examples
3. Clearly distinguish: 
   - "From your notes: ..." (grounded content)
   - "To help understand: ..." (additional explanation)
4. If notes don't cover the question, state that clearly first
5. Be pedagogical - break down complex concepts
6. Adapt explanation to student level when possible

Answer:"""
```

### Generation Parameters
```python
# Strict mode - more deterministic
strict_config = {
    "temperature": 0.3,
    "max_tokens": 800,
    "top_p": 0.9,
    "frequency_penalty": 0.3,
    "presence_penalty": 0.0
}

# Teaching mode - more creative
teaching_config = {
    "temperature": 0.5,
    "max_tokens": 1000,
    "top_p": 0.9,
    "frequency_penalty": 0.3,
    "presence_penalty": 0.1
}
```

## Citation Verification

### Post-Generation Verification
```python
def verify_answer_grounding(
    answer: str,
    retrieved_chunks: List[dict],
    mode: str
) -> dict:
    """
    Verify answer is grounded in retrieved sources.
    
    Returns:
        {
            "grounded": bool,
            "groundedness_score": float,  # 0.0-1.0
            "unsupported_claims": List[str],
            "citation_accuracy": float,  # 0.0-1.0
            "warnings": List[str]
        }
    """
    # Extract factual claims from answer
    claims = extract_claims(answer)
    
    # Match each claim to source chunks
    supported_count = 0
    unsupported = []
    
    for claim in claims:
        if is_supported_by_sources(claim, retrieved_chunks):
            supported_count += 1
        else:
            unsupported.append(claim)
    
    groundedness_score = supported_count / len(claims) if claims else 1.0
    
    # Verify citations reference actual sources
    citations = extract_citations(answer)
    valid_citations = [c for c in citations 
                      if citation_exists(c, retrieved_chunks)]
    citation_accuracy = len(valid_citations) / len(citations) if citations else 1.0
    
    # Strict mode should have near-perfect grounding
    if mode == "strict" and groundedness_score < 0.95:
        warnings = ["Answer contains unsupported claims in strict mode"]
    else:
        warnings = []
    
    return {
        "grounded": groundedness_score >= 0.9,
        "groundedness_score": groundedness_score,
        "unsupported_claims": unsupported,
        "citation_accuracy": citation_accuracy,
        "warnings": warnings
    }
```

### Citation Format Standards
```python
# Good citation formats:
"According to your Geometry Notes (Right Triangles section), the Pythagorean theorem states..."
"[Geometry Notes, Right Triangles] a² + b² = c²"
"From Chapter 3 of your Physics Notes: ..."

# Bad citation formats:
"Source says..." (vague)
"[1]" (unclear reference)
"According to the notes..." (which notes?)
```

## Evidence Sufficiency Assessment

### Criteria for Sufficient Evidence
```python
def is_evidence_sufficient(
    retrieved_chunks: List[dict],
    rerank_scores: List[float],
    query: str
) -> tuple[bool, str]:
    """
    Determine if retrieved evidence is sufficient to answer query.
    
    Returns:
        (is_sufficient, reason)
    """
    # No results
    if not retrieved_chunks:
        return False, "No relevant content found"
    
    # Too few results
    if len(retrieved_chunks) < 2:
        return False, "Insufficient relevant content (< 2 chunks)"
    
    # Low confidence scores
    avg_score = sum(rerank_scores) / len(rerank_scores)
    if avg_score < 0.4:
        return False, f"Low relevance scores (avg: {avg_score:.2f})"
    
    # Top result very low confidence
    if rerank_scores[0] < 0.5:
        return False, f"Top result low confidence: {rerank_scores[0]:.2f}"
    
    # Check coverage (heuristic: question tokens in results)
    query_terms = set(query.lower().split())
    result_terms = set()
    for chunk in retrieved_chunks:
        result_terms.update(chunk['text'].lower().split())
    
    coverage = len(query_terms & result_terms) / len(query_terms)
    if coverage < 0.3:
        return False, f"Low query term coverage: {coverage:.2f}"
    
    return True, "Evidence appears sufficient"
```

### Retry Strategy
```python
# LangGraph workflow decision
if not evidence_sufficient and retry_count < 2:
    # Reformulate query and retry
    reformulated_query = expand_query(original_query)
    retry_retrieval(reformulated_query)
elif not evidence_sufficient and retry_count >= 2:
    # Give up, admit insufficient information
    return "I don't have enough information in your notes to answer this question."
else:
    # Proceed to generation
    generate_answer(retrieved_chunks)
```

## Conversation Context Management

### Context Window Strategy
```python
def build_conversation_context(
    current_question: str,
    history: List[dict],
    max_context_tokens: int = 1000
) -> str:
    """
    Build conversation context for current question.
    
    Include most recent Q&A pairs up to token limit.
    """
    context_parts = []
    tokens_used = 0
    
    # Start with most recent
    for qa_pair in reversed(history):
        pair_text = f"Previous Q: {qa_pair['question']}\nA: {qa_pair['answer']}\n\n"
        pair_tokens = estimate_tokens(pair_text)
        
        if tokens_used + pair_tokens > max_context_tokens:
            break
        
        context_parts.insert(0, pair_text)
        tokens_used += pair_tokens
    
    return "".join(context_parts)
```

### Reference Resolution
```python
def resolve_references(question: str, history: List[dict]) -> str:
    """
    Resolve pronouns and references to previous conversation.
    
    Examples:
    - "What about it?" -> "What about [previous topic]?"
    - "Explain that more" -> "Explain [previous concept] more"
    """
    if not history:
        return question
    
    # Simple heuristic for MVP
    reference_words = ["it", "that", "this", "those", "them"]
    
    question_lower = question.lower()
    if any(word in question_lower for word in reference_words):
        # Get last question's main topic
        last_question = history[-1]["question"]
        # Append for context
        return f"{question} (referring to: {last_question})"
    
    return question
```

## Performance Optimization

### Caching Strategy
```python
# Cache query embeddings (common questions)
@lru_cache(maxsize=1000)
def get_query_embedding(query: str) -> List[float]:
    return embedding_service.embed(query)

# Cache frequent retrievals
class RetrievalCache:
    def __init__(self, ttl_seconds: int = 300, max_size: int = 500):
        self.cache = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
    
    def get(self, query: str, top_k: int) -> Optional[List[dict]]:
        key = f"{query}:{top_k}"
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
        return None
    
    def set(self, query: str, top_k: int, results: List[dict]):
        if len(self.cache) >= self.max_size:
            # Evict oldest
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = f"{query}:{top_k}"
        self.cache[key] = (results, time.time())
```

### Batch Processing
```python
# Batch embed multiple documents
def ingest_documents_batch(file_paths: List[str], batch_size: int = 32):
    """Process multiple documents efficiently."""
    all_chunks = []
    
    # Parse all documents first
    for path in file_paths:
        chunks = parse_and_chunk(path)
        all_chunks.extend(chunks)
    
    # Batch embed
    texts = [chunk['text'] for chunk in all_chunks]
    embeddings = embedding_service.embed_batch(texts, batch_size=batch_size)
    
    # Assign embeddings
    for chunk, embedding in zip(all_chunks, embeddings):
        chunk['embedding'] = embedding
    
    # Batch insert to Qdrant
    vector_store.insert_batch(all_chunks)
```

## Error Handling Patterns

### Retrieval Errors
```python
try:
    results = vector_store.search(query_embedding, top_k=20)
except QdrantConnectionError as e:
    logger.error(f"Qdrant connection failed: {e}", exc_info=True)
    raise ServiceUnavailableError(
        "Vector database is temporarily unavailable. Please try again."
    ) from e
except QdrantTimeoutError as e:
    logger.warning(f"Qdrant timeout: {e}")
    # Retry once
    results = vector_store.search(query_embedding, top_k=20)
```

### Generation Errors
```python
try:
    answer = llm_client.generate(prompt, **config)
except GroqRateLimitError as e:
    logger.warning(f"Groq rate limit hit: {e}")
    # Wait and retry with exponential backoff
    time.sleep(2 ** retry_count)
    answer = llm_client.generate(prompt, **config)
except GroqAPIError as e:
    logger.error(f"Groq API error: {e}", exc_info=True)
    raise GenerationError(
        "Failed to generate answer due to API error. Please try again."
    ) from e
```

## Quality Metrics to Track

### Retrieval Metrics
- **Recall@k**: % of relevant docs in top-k results
- **MRR**: Mean Reciprocal Rank of first relevant result  
- **nDCG**: Normalized Discounted Cumulative Gain
- **Latency**: p50, p95, p99 retrieval time

### Generation Metrics
- **Answer Correctness**: Manual labels on test set
- **Groundedness**: % of answer grounded in sources
- **Citation Accuracy**: % of citations that are correct
- **Completeness**: Does answer address full question?

### System Metrics
- **End-to-end latency**: Question to answer time
- **API cost**: Cost per query (Groq tokens)
- **Cache hit rate**: % of queries served from cache
- **Error rate**: % of requests that fail

## Testing Checklist

For each RAG component, verify:

**Ingestion:**
- [ ] Chunks respect token limits
- [ ] Metadata preserved
- [ ] Parent-child relationships correct
- [ ] Duplicates handled
- [ ] Source traceability maintained

**Retrieval:**
- [ ] Hybrid search returns relevant results
- [ ] Reranking improves quality
- [ ] Context expansion works correctly
- [ ] Metadata filtering functions
- [ ] Performance within limits

**Generation:**
- [ ] Answers grounded in sources (strict mode)
- [ ] Citations accurate and verifiable
- [ ] Unsupported questions handled correctly
- [ ] Both modes work as intended
- [ ] No hallucinations

**End-to-End:**
- [ ] Full workflow completes successfully
- [ ] Quality metrics meet thresholds
- [ ] Error handling works
- [ ] Conversation context maintained
- [ ] Performance acceptable
