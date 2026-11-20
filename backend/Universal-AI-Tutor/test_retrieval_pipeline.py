"""
Test actual retrieval pipeline for Plato question.
"""
import sys
import os
from pathlib import Path

# Set collection before any imports
os.environ["QDRANT_COLLECTION_NAME"] = "my_personal_notes"

sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    from src.config import get_settings
    from src.core.retrieval_pipeline import get_retrieval_pipeline
    
    settings = get_settings()
    print(f"Collection: {settings.qdrant_collection_name}")
    print()
    
    # Get pipeline
    pipeline = get_retrieval_pipeline(collection_name="my_personal_notes")
    
    # Retrieve
    query = "Explain Plato's concept of time in simple language"
    print(f"Query: {query}")
    print()
    
    results = pipeline.retrieve(query=query, top_k=5)
    
    print(f"Retrieved {len(results)} chunks:\n")
    
    for i, result in enumerate(results, 1):
        filename = Path(result.doc_path).name
        score = result.final_score
        rerank = result.rerank_score
        text = result.text
        
        # Check relevance
        has_plato = "plato" in text.lower()
        has_time = "time" in text.lower()
        relevant = has_plato or has_time
        
        # Check readability (simple heuristic: > 70% alphabetic)
        alpha_chars = sum(1 for c in text if c.isalpha())
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        readable = (alpha_chars / total_chars > 0.7) if total_chars > 0 else False
        
        # Check for OCR corruption
        ocr_markers = ["inirnlvo", "tlio", "tlie", "witli", "tliis"]
        has_corruption = any(marker in text for marker in ocr_markers)
        
        print(f"=== Result {i} ===")
        print(f"Source: {filename}")
        print(f"Final Score: {score:.4f}")
        print(f"Rerank Score: {rerank:.4f}")
        print(f"Relevant: {'✅' if relevant else '❌'} (plato={has_plato}, time={has_time})")
        print(f"Readable: {'✅' if readable else '❌'} ({alpha_chars}/{total_chars} alpha)")
        print(f"Corruption: {'⚠️ YES' if has_corruption else '✅ Clean'}")
        print(f"\nText (first 500 chars):")
        print(text[:500])
        print()
    
    # Assessment
    print("\n=== ASSESSMENT ===")
    relevant_count = sum(1 for r in results if "plato" in r.text.lower() or "time" in r.text.lower())
    corrupted_count = sum(1 for r in results if any(m in r.text for m in ["inirnlvo", "tlio", "tlie", "witli", "tliis"]))
    
    print(f"Relevant chunks: {relevant_count}/5")
    print(f"Corrupted chunks: {corrupted_count}/5")
    
    if relevant_count >= 3:
        print("\n✅ Retrieval returning relevant content")
    else:
        print("\n❌ Retrieval NOT returning relevant content")
        print("   → Problem likely in hybrid search or reranking")
    
    if corrupted_count > 0:
        print("\n⚠️  Parent expansion introducing OCR corruption")
        print("   → Source file trial.txt contains OCR errors")
    else:
        print("\n✅ No corruption in retrieved text")

if __name__ == "__main__":
    main()
