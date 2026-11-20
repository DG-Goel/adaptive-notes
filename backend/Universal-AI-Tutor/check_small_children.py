"""Find small child chunks."""
from src.core.vector_store import get_vector_store
from src.core.embedding_service import get_embedding_service

vs = get_vector_store()
es = get_embedding_service()

result = vs.client.scroll('tutor_knowledge', limit=500, with_payload=True, with_vectors=False)
chunks = result[0]

children = [c for c in chunks if not c.payload.get('is_parent', False)]
print(f"Total children: {len(children)}\n")

# Check token counts (not just char length)
small_children = []
for c in children:
    text = c.payload.get('text', '')
    tokens = es.estimate_tokens(text)
    if tokens < 300:
        small_children.append((c, text, tokens))

print(f"Small children (<300 tokens): {len(small_children)}\n")

for c, text, tokens in small_children[:15]:
    parent_id = c.payload.get('parent_id', 'None')
    parent_str = parent_id[:12] + "..." if parent_id != 'None' else 'None'
    print(f"SMALL CHILD: id={c.id[:12]}... tokens={tokens} parent_id={parent_str}")
    print(f"  Text preview: {text[:80]}...")
    print()
