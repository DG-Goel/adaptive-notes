# Retrieval Evaluation Setup

## Current Status

**Environment Issue Detected:** The current Python environment has a dependency conflict between Keras 3 and the transformers library. This prevents running the benchmark script.

```
ValueError: Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers. 
Please install the backwards-compatible tf-keras package with `pip install tf-keras`.
```

## Resolution Options

### Option 1: Install tf-keras (Recommended)
```bash
pip install tf-keras
```

### Option 2: Downgrade Keras
```bash
pip install "keras<3"
```

### Option 3: Use Docker environment
The issue may not exist in a clean Docker environment or different Python version.

## Running the Benchmark

Once the dependency issue is resolved:

```bash
# Run the full benchmark
python tests/evaluation/run_retrieval_benchmark.py
```

This will:
1. Ingest all sample documents from `tests/fixtures/sample_documents/`
2. Run 55 evaluation questions through 4 retrieval configurations
3. Generate `tests/evaluation/benchmark_results.json` with detailed metrics
4. Generate `tests/evaluation/BENCHMARK_REPORT.md` with summary

## Evaluation Dataset

- **File:** `tests/evaluation/evaluation_dataset.json`
- **Questions:** 55 human-reviewable questions
- **Categories:** factual, conceptual, procedural, comparative, applicative
- **Difficulty Levels:** easy, medium, hard
- **Documents:** math_calculus.md, physics_mechanics.md, programming_python.md, theory_algorithms.md, history_wwii.txt

## Retrieval Configurations Tested

| Config | Description |
|--------|-------------|
| A_dense_only | Dense vector search only (bi-encoder) |
| B_bm25_only | BM25 sparse search only (keyword matching) |
| C_hybrid | Dense + BM25 with RRF fusion |
| D_hybrid_rerank | Hybrid + cross-encoder reranking |

## Metrics Computed

- **Recall@5:** Percentage of relevant documents retrieved in top-5
- **Precision@5:** Percentage of retrieved documents that are relevant
- **MRR (Mean Reciprocal Rank):** Rank position of first relevant result
- **NDCG@5:** Normalized Discounted Cumulative Gain (accounts for ranking quality)
- **Average Retrieval Time:** Latency in milliseconds

## Implementation Notes

The benchmark script (`run_retrieval_benchmark.py`) uses:
- `RetrievalPipeline` for consistent retrieval across configurations
- Heuristic matching to identify relevant chunks (matches by document, section, and keywords)
- In production, explicit chunk IDs would be included in the evaluation dataset

## Known Limitations

1. **Relevance Matching:** Uses heuristic (section name + keyword matching) rather than explicit chunk IDs
   - This is sufficient for comparative benchmarking
   - For absolute quality assessment, manual annotation of relevant chunk IDs would be needed

2. **Ground Truth:** Expected answers are provided for human review but not automatically evaluated
   - Full RAG system evaluation would require answer quality metrics (e.g., semantic similarity, LLM-as-judge)
   - Current benchmark focuses on retrieval quality only

3. **Sample Size:** 55 questions provide reasonable signal for comparative analysis
   - Larger evaluation sets (100-200 questions) would give more stable metrics
   - Coverage is good across domains and difficulty levels

## Next Steps After Resolution

1. Fix the dependency issue (install tf-keras or downgrade keras)
2. Run: `python tests/evaluation/run_retrieval_benchmark.py`
3. Review: `tests/evaluation/BENCHMARK_REPORT.md`
4. Analyze: Which configuration performs best for this dataset?
5. Compare: Trade-offs between retrieval quality and latency

## Expected Results

Based on RAG literature and system design:
- **A_dense_only:** Good semantic matching, may miss exact keyword matches
- **B_bm25_only:** Good for exact matches, weaker on semantic variations
- **C_hybrid:** Best of both worlds, should outperform single methods
- **D_hybrid_rerank:** Highest quality but slowest, cross-encoder adds precision

Typical expected ranges (vary by dataset):
- Recall@5: 0.60-0.85
- Precision@5: 0.40-0.70
- MRR: 0.50-0.80
- NDCG@5: 0.55-0.75
- Time: 50-500ms depending on configuration

## Contact

For questions about the evaluation setup or results interpretation, refer to:
- `testing-guidelines.md` in `.kiro/steering/`
- `rag-best-practices.md` in `.kiro/steering/`
