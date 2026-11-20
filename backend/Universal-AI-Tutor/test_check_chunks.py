"""
Check what chunks exist in Qdrant.
"""

from src.core.vector_store import get_vector_store

print("\n=== Checking Chunks in Qdrant ===\n")

vector_store = get_vector_store()

# Scroll through all chunks
offset = None
all_chunks = []

while True:
    result = vector_store.client.scroll(
        collection_name="tutor_knowledge",
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False
    )
    
    points = result[0]
    if not points:
        break
    
    all_chunks.extend(points)
    offset = result[1]
    
    if not offset:
        break

print(f"Total chunks in database: {len(all_chunks)}\n")

# Analyze chunks
parent_count = 0
child_count = 0

for chunk in all_chunks:
    is_parent = chunk.payload.get("is_parent", False)
    parent_id = chunk.payload.get("parent_id")
    chunk_type = chunk.payload.get("chunk_type")
    text_length = len(chunk.payload.get("text", ""))
    
    if is_parent:
        parent_count += 1
        print(f"PARENT: id={chunk.id[:12]}... type={chunk_type} text_len={text_length} parent_id={parent_id}")
    else:
        child_count += 1
        parent_str = parent_id[:12] + "..." if parent_id else "None"
        print(f"  CHILD: id={chunk.id[:12]}... type={chunk_type} text_len={text_length} parent_id={parent_str}")

print(f"\nSummary:")
print(f"  Parents: {parent_count}")
print(f"  Children: {child_count}")
print(f"  Total: {len(all_chunks)}")

if child_count == 0:
    print("\n⚠️ NO CHILD CHUNKS FOUND - This explains why context expansion doesn't work!")
