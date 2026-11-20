"""
Simple direct check: What's in my_personal_notes collection?
"""
from qdrant_client import QdrantClient
from pathlib import Path

def main():
    print("=== Simple Qdrant Check ===\n")
    
    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6333)
    
    collection_name = "my_personal_notes"
    
    # 1. Check collection exists and count
    try:
        collection_info = client.get_collection(collection_name)
        print(f"1. Collection: {collection_name}")
        print(f"   Points: {collection_info.points_count}\n")
    except Exception as e:
        print(f"❌ Collection not found: {e}\n")
        return
    
    # 2. Retrieve a sample of points to see what's in there
    print("2. Sample of points in collection:\n")
    scroll_result = client.scroll(
        collection_name=collection_name,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    points = scroll_result[0]
    
    for i, point in enumerate(points[:5], 1):
        payload = point.payload
        doc_path = payload.get("doc_path", "unknown")
        filename = Path(doc_path).name if doc_path != "unknown" else "unknown"
        text = payload.get("text", "")
        
        print(f"--- Point {i} (ID: {point.id}) ---")
        print(f"Source: {filename}")
        print(f"Text preview (first 200 chars):")
        print(text[:200])
        print()
    
    # 3. Search for Plato-related content using basic text filter
    print("3. Searching for 'Plato' in text...\n")
    
    # Scroll through and filter (simple approach without embeddings)
    matches = []
    offset = None
    checked = 0
    
    while checked < 598 and len(matches) < 5:  # Check all points, get first 5 matches
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=50,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, offset = scroll_result
        
        for point in points:
            checked += 1
            text = point.payload.get("text", "").lower()
            if "plato" in text:
                matches.append(point)
                if len(matches) >= 5:
                    break
        
        if offset is None:  # No more points
            break
    
    print(f"Checked {checked} points, found {len(matches)} mentioning 'Plato'\n")
    
    if matches:
        print("First Plato mentions:\n")
        for i, point in enumerate(matches[:3], 1):
            payload = point.payload
            doc_path = payload.get("doc_path", "unknown")
            filename = Path(doc_path).name
            text = payload.get("text", "")
            
            # Find Plato mention
            text_lower = text.lower()
            plato_idx = text_lower.find("plato")
            snippet_start = max(0, plato_idx - 100)
            snippet_end = min(len(text), plato_idx + 200)
            snippet = text[snippet_start:snippet_end]
            
            print(f"--- Match {i} ---")
            print(f"Source: {filename}")
            print(f"Context around 'Plato':")
            print(f"...{snippet}...")
            print()
    else:
        print("❌ NO points contain 'Plato'\n")
    
    print("\n4. Assessment:")
    if len(matches) > 0:
        print(f"   ✅ Collection contains {len(matches)} chunks with Plato content")
        print(f"   ✅ Source file: {Path(matches[0].payload.get('doc_path', '')).name}")
    else:
        print("   ❌ Collection does NOT contain any Plato content")
        print("   → trial.txt may not have been ingested into this collection")

if __name__ == "__main__":
    main()
