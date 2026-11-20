"""
Diagnostic: Check what's retrieved from my_personal_notes for Plato question.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_settings
from src.core.retrieval_pipeline import get_retrieval_pipeline

def main():
    print("=== Retrieval Diagnosis ===\n")
    
    # 1. Get settings and check collection
    settings = get_settings()
    print(f"1. Collection from settings: {settings.qdrant_collection_name}\n")
    
    # 2. Initialize pipeline and check collection
    pipeline = get_retrieval_pipeline()
    
    # Get point count from vector store
    try:
        from qdrant_client import QdrantClient
        # Parse URL to get host and port
        url_parts = settings.qdrant_url.replace("http://", "").split(":")
        host = url_parts[0]
        port = int(url_parts[1]) if len(url_parts) > 1 else 6333
        
        client = QdrantClient(host=host, port=port)
        collection_info = client.get_collection(settings.qdrant_collection_name)
        point_count = collection_info.points_count
        print(f"2. Collection '{settings.qdrant_collection_name}' has {point_count} points\n")
    except Exception as e:
        print(f"2. Could not get point count: {e}\n")
    
    # 3. Retrieve for Plato question
    query = "Explain Plato's concept of time in simple language"
    print(f"3. Retrieving for query: '{query}'\n")
    
    results = pipeline.retrieve(query=query, top_k=5)
    
    # 4. Print results
    print(f"4. Retrieved {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        # Access attributes correctly (RetrievalResult is a dataclass)
        filename = Path(result.doc_path).name if hasattr(result, 'doc_path') else "unknown"
        score = result.score if hasattr(result, 'score') else 0.0
        text = result.text if hasattr(result, 'text') else ""
        
        print(f"--- Result {i} ---")
        print(f"Source: {filename}")
        print(f"Score: {score:.4f}")
        print(f"Text preview (first 300 chars):")
        print(text[:300])
        print()
    
    # 5. Assessment
    print("5. Assessment:")
    if not results:
        print("❌ NO results retrieved")
    else:
        relevant_count = sum(1 for r in results if "plato" in r.text.lower() or "time" in r.text.lower())
        corrupted_count = sum(1 for r in results if "inirnlvo" in r.text or len([c for c in r.text if c.isalpha()]) < len(r.text) * 0.7)
        
        print(f"   - {relevant_count}/{len(results)} results contain 'plato' or 'time'")
        print(f"   - {corrupted_count}/{len(results)} results appear corrupted")
        
        if relevant_count >= 3:
            print("   ✅ Retrieval returned relevant philosophy content")
        else:
            print("   ❌ Retrieval did NOT return relevant philosophy content")

if __name__ == "__main__":
    main()
