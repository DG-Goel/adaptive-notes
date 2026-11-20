"""
Smoke test for Universal AI Tutor - Quick end-to-end validation.

Tests document ingestion and question answering with citations.
"""

import sys
import os
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

from src.services.ingestion_service import IngestionService
from src.services.tutoring.workflow import get_tutoring_workflow
from src.core.vector_store import get_vector_store
from src.config import get_settings


def main():
    print("=" * 70)
    print("SMOKE TEST: Universal AI Tutor")
    print("=" * 70)
    
    # Check settings
    settings = get_settings()
    print(f"\n1. Configuration:")
    print(f"   - LLM Provider: {settings.llm_provider}")
    print(f"   - Collection: {settings.qdrant_collection_name}")
    print(f"   - Embedding Model: {settings.embedding_model}")
    
    # Ensure vector store collection exists
    print(f"\n2. Setting up vector store...")
    vector_store = get_vector_store()
    if not vector_store.collection_exists():
        vector_store.create_collection()
        print("[OK] Created collection")
    else:
        print("[OK] Collection already exists")
    
    # Ingest test note
    print(f"\n3. Ingesting test note...")
    note_path = "test_notes/sample_note.md"
    
    if not os.path.exists(note_path):
        print(f"   [ERROR] Test note not found: {note_path}")
        return False
    
    ingestion_service = IngestionService()
    result = ingestion_service.ingest_documents(
        file_paths=[note_path],
        overwrite=True
    )
    
    print(f"   [OK] Ingested {result.successful} document(s)")
    print(f"   - Chunks indexed: {result.total_chunks_indexed}")
    print(f"   - Processing time: {result.processing_time_seconds:.2f}s")
    
    # Ask a question
    print(f"\n4. Asking question...")
    workflow = get_tutoring_workflow()
    
    question = "What are the built-in data types in Python?"
    print(f"   Question: {question}")
    
    # Prepare state for workflow
    initial_state = {
        "question": question,
        "mode": "strict",
        "conversation_history": [],
        "retry_count": 0,
        "metadata": {},
    }
    
    # Execute workflow
    final_state = workflow.invoke(initial_state)
    
    print(f"\n5. Response:")
    
    answer = final_state.get("answer", "")
    citations = final_state.get("citations", [])
    metadata = final_state.get("metadata", {})
    
    if answer:
        print(f"   Answer: {answer[:200]}...")
        print(f"   Citations: {len(citations)} found")
        
        if citations:
            print(f"\n   Citation details:")
            for i, citation in enumerate(citations[:3], 1):
                print(f"   {i}. Doc: {citation.get('doc_title', 'unknown')}")
                print(f"      Chunk: {citation.get('chunk_id', 'unknown')}")
                if 'score' in citation:
                    print(f"      Score: {citation.get('score', 0):.3f}")
        
        print(f"\n   Metadata:")
        if 'retrieval_time_ms' in metadata:
            print(f"   - Retrieval time: {metadata['retrieval_time_ms']}ms")
        if 'generation_time_ms' in metadata:
            print(f"   - Generation time: {metadata['generation_time_ms']}ms")
        
        # Verify citations have metadata
        if citations:
            first_citation = citations[0]
            has_metadata = 'chunk_id' in first_citation and 'doc_title' in first_citation
            if has_metadata:
                print(f"   [OK] Citations include metadata")
            else:
                print(f"   [WARNING] Citations missing some metadata")
        
        print(f"\n" + "=" * 70)
        print("[SUCCESS] SMOKE TEST PASSED")
        print("=" * 70)
        return True
    else:
        error = final_state.get("error", "Unknown error")
        print(f"   [ERROR] Failed: {error}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
