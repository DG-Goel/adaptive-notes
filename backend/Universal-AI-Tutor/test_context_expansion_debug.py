"""
Direct debug script for context expansion testing.
"""

import logging
import sys

# Set up DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

# Ensure universal_ai_tutor logger is DEBUG
logging.getLogger("universal_ai_tutor").setLevel(logging.DEBUG)

from src.core.retrieval_pipeline import get_retrieval_pipeline
from src.core.embedding_service import get_embedding_service

print("\n=== Testing Context Expansion ===\n")

# Create pipeline
pipeline = get_retrieval_pipeline()
embedding_service = get_embedding_service()

# Test retrieval
query = "What are the types of machine learning?"
print(f"Query: {query}\n")

# Without expansion
print("--- Retrieval WITHOUT expansion ---")
results_without = pipeline.retrieve(query, top_k=5)
print(f"\nRetrieved {len(results_without)} results without expansion:")
for i, r in enumerate(results_without):
    tokens = embedding_service.estimate_tokens(r.text)
    rerank_str = f"{r.rerank_score:.3f}" if r.rerank_score is not None else "None"
    parent_str = r.parent_id[:12] + "..." if r.parent_id else "None"
    print(f"  {i+1}. chunk_id={r.chunk_id[:12]}... is_parent={r.is_parent} parent_id={parent_str} tokens={tokens} rerank_score={rerank_str}")

# With expansion
print("\n--- Retrieval WITH expansion ---")
results_with = pipeline.retrieve_with_context_expansion(
    query,
    top_k=5,
    expand_parents=True
)
print(f"\nRetrieved {len(results_with)} results with expansion:")
for i, r in enumerate(results_with):
    tokens = embedding_service.estimate_tokens(r.text)
    has_separator = "---" in r.text
    rerank_str = f"{r.rerank_score:.3f}" if r.rerank_score is not None else "None"
    parent_str = r.parent_id[:12] + "..." if r.parent_id else "None"
    print(f"  {i+1}. chunk_id={r.chunk_id[:12]}... is_parent={r.is_parent} parent_id={parent_str} tokens={tokens} has_separator={has_separator} rerank_score={rerank_str}")

# Check for expansions
expansion_count = sum(1 for r in results_with if "---" in r.text)
print(f"\nExpansions performed: {expansion_count}/{len(results_with)}")

if expansion_count == 0:
    print("\n⚠️ NO EXPANSIONS OCCURRED")
    print("\nDiagnosing why:")
    for i, r in enumerate(results_without):
        tokens = embedding_service.estimate_tokens(r.text)
        print(f"\nChunk {i+1}:")
        print(f"  is_parent={r.is_parent}, parent_id={r.parent_id}")
        print(f"  tokens={tokens}, rerank_score={r.rerank_score}")
        if not r.is_parent and r.parent_id:
            should_expand_size = tokens < 300
            should_expand_conf = r.rerank_score and r.rerank_score < 0.6
            print(f"  Should expand (size)? {should_expand_size} (< 300 tokens)")
            print(f"  Should expand (conf)? {should_expand_conf} (< 0.6 rerank)")
            if should_expand_size or should_expand_conf:
                print(f"  ✅ SHOULD EXPAND")
            else:
                print(f"  ❌ Does not meet expansion criteria")
        elif r.is_parent:
            print(f"  ℹ️ Parent chunk - not eligible for expansion")
        elif not r.parent_id:
            print(f"  ℹ️ No parent_id - cannot expand")
else:
    print(f"\n✅ SUCCESS: {expansion_count} chunk(s) expanded")
