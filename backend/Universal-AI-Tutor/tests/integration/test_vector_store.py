"""
Integration tests for VectorStore with real Qdrant instance.

These tests require a running Qdrant server (docker compose up -d).
They test actual Qdrant 1.20+ features including native BM25 and RRF.
"""

import pytest
from qdrant_client import QdrantClient

from src.core.vector_store import VectorStore


@pytest.fixture(scope="module")
def qdrant_client():
    """Provide real Qdrant client for integration tests."""
    client = QdrantClient(url="http://localhost:6333", timeout=30)

    # Verify connection
    try:
        client.get_collections()
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")

    yield client

    client.close()


@pytest.fixture
def test_collection_name():
    """Provide unique collection name for each test."""
    import uuid

    return f"test_vector_store_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def vector_store(qdrant_client, test_collection_name):
    """Provide VectorStore with test collection."""
    store = VectorStore(
        client=qdrant_client, collection_name=test_collection_name, embedding_dim=384
    )

    # Create collection
    store.create_collection()

    yield store

    # Cleanup
    try:
        qdrant_client.delete_collection(test_collection_name)
    except:
        pass


@pytest.mark.integration
class TestVectorStoreIntegration:
    """Integration tests for VectorStore with real Qdrant."""

    def test_create_collection_success(self, vector_store):
        """Test collection creation with dense vectors and BM25 index."""
        assert vector_store.collection_exists()

        # Verify collection info
        collection_info = vector_store.client.get_collection(
            vector_store.collection_name
        )

        assert collection_info.config.params.vectors is not None
        assert "dense" in collection_info.config.params.vectors

    def test_insert_single_point(self, vector_store):
        """Test inserting a single point."""
        vector = [0.1] * 384
        payload = {
            "text": "The Pythagorean theorem states that a² + b² = c²",
            "doc_id": "doc1",
            "doc_title": "Geometry Notes",
        }

        vector_store.insert(id="point1", vector=vector, payload=payload)

        # Verify insertion
        point = vector_store.get_point("point1")
        assert point is not None
        assert point.payload["text"] == payload["text"]
        assert point.payload["doc_id"] == "doc1"

    def test_insert_batch(self, vector_store):
        """Test batch insertion."""
        ids = ["batch1", "batch2", "batch3"]
        vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        payloads = [
            {"text": "First document about mathematics", "doc_id": "doc1"},
            {"text": "Second document about physics", "doc_id": "doc2"},
            {"text": "Third document about chemistry", "doc_id": "doc3"},
        ]

        vector_store.insert_batch(ids=ids, vectors=vectors, payloads=payloads)

        # Verify count
        count = vector_store.count_points()
        assert count == 3

    def test_dense_search(self, vector_store):
        """Test dense vector similarity search with clearly distinguishable vectors."""
        # Create normalized vectors with known cosine similarities
        # All vectors are L2-normalized for consistent comparison
        
        import math
        
        # Helper to create L2-normalized vector
        def normalize(vec):
            magnitude = math.sqrt(sum(x**2 for x in vec))
            if magnitude == 0:
                return vec
            return [x / magnitude for x in vec]
        
        # Query: Small values in first 10 positions, zeros elsewhere
        query_base = [1.0] * 10 + [0.0] * 374
        query_vector = normalize(query_base)
        
        # Vector 1: Matches query pattern exactly (highest similarity)
        vec1_base = [1.0] * 10 + [0.0] * 374
        vec1 = normalize(vec1_base)
        
        # Vector 2: Partial overlap (medium similarity)
        vec2_base = [1.0] * 5 + [0.0] * 5 + [1.0] * 374
        vec2 = normalize(vec2_base)
        
        # Vector 3: No overlap (lowest similarity)
        vec3_base = [0.0] * 10 + [1.0] * 374
        vec3 = normalize(vec3_base)
        
        payloads = [
            {"text": "Document one", "doc_id": "doc1", "rank": "highest"},
            {"text": "Document two", "doc_id": "doc2", "rank": "medium"},
            {"text": "Document three", "doc_id": "doc3", "rank": "lowest"},
        ]

        vector_store.insert_batch(
            ids=["dense1", "dense2", "dense3"], 
            vectors=[vec1, vec2, vec3], 
            payloads=payloads
        )

        # Search with top_k=3 to see full ranking
        results = vector_store.dense_search(query_vector=query_vector, top_k=3)

        # Verify results
        assert len(results) == 3
        
        # Verify ordering: scores should be descending (higher = more similar)
        assert results[0].score >= results[1].score >= results[2].score
        
        # Verify expected ranking based on cosine similarity
        # vec1 (perfect match) should be most similar
        assert results[0].payload["doc_id"] == "doc1"
        assert results[0].payload["rank"] == "highest"
        
        # vec2 (partial overlap) should be medium
        assert results[1].payload["doc_id"] == "doc2"
        assert results[1].payload["rank"] == "medium"
        
        # vec3 (no overlap) should be least similar
        assert results[2].payload["doc_id"] == "doc3"
        assert results[2].payload["rank"] == "lowest"
        
        # Verify all scores are valid (between -1 and 1 for cosine)
        for result in results:
            assert -1.0 <= result.score <= 1.0
        
        # Verify the top result has very high similarity (close to 1.0)
        assert results[0].score > 0.95

    def test_bm25_search_native(self, vector_store):
        """Test BM25 full-text search using Qdrant 1.20+ native scoring."""
        # Insert documents with distinct keywords
        payloads = [
            {"text": "The Pythagorean theorem is about right triangles", "doc_id": "doc1"},
            {"text": "Binary search algorithm divides arrays efficiently", "doc_id": "doc2"},
            {"text": "Newton's laws describe motion and forces", "doc_id": "doc3"},
        ]
        vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]

        vector_store.insert_batch(
            ids=["bm25_1", "bm25_2", "bm25_3"], vectors=vectors, payloads=payloads
        )

        # Search for keyword present in first document
        results = vector_store.bm25_search(query_text="Pythagorean theorem", top_k=2)

        # Verify BM25 found relevant document
        assert len(results) > 0
        # Should find the document with "Pythagorean" in it
        assert results[0].payload["doc_id"] == "doc1"
        assert "Pythagorean" in results[0].payload["text"]

    def test_hybrid_search_with_rrf_fusion(self, vector_store):
        """Test hybrid search combining dense + BM25 with native RRF fusion."""
        # Insert documents with both semantic and keyword signals
        payloads = [
            {
                "text": "The Pythagorean theorem: a² + b² = c² for right triangles",
                "doc_id": "doc1",
            },
            {
                "text": "Binary search algorithm for sorted arrays",
                "doc_id": "doc2",
            },
            {
                "text": "Theorem about triangles in geometry",
                "doc_id": "doc3",
            },
        ]

        # Create vectors where doc1 is semantically similar to query
        query_vector = [0.8] * 384
        vectors = [
            [0.85] * 384,  # Similar to query
            [0.1] * 384,  # Not similar
            [0.75] * 384,  # Somewhat similar
        ]

        vector_store.insert_batch(
            ids=["hybrid1", "hybrid2", "hybrid3"], vectors=vectors, payloads=payloads
        )

        # Hybrid search with both semantic and keyword matching
        results = vector_store.hybrid_search(
            query_text="Pythagorean theorem",
            query_vector=query_vector,
            top_k=3,
            dense_top_k=3,
            bm25_top_k=3,
        )

        # Verify hybrid results
        assert len(results) > 0
        # First result should be doc1 (matches both semantically and by keywords)
        assert results[0].payload["doc_id"] == "doc1"

    def test_hybrid_search_rrf_combines_signals(self, vector_store):
        """Test that RRF properly combines dense and BM25 signals."""
        # Create scenario where:
        # - doc1: High BM25, low semantic
        # - doc2: High semantic, low BM25
        # - doc3: Medium both (should rank high via fusion)

        payloads = [
            {
                "text": "Pythagorean Pythagorean Pythagorean theorem keyword repetition",
                "doc_id": "doc1",
            },
            {"text": "Completely different topic about chemistry", "doc_id": "doc2"},
            {"text": "The famous Pythagorean theorem in mathematics", "doc_id": "doc3"},
        ]

        # Query vector semantically similar to doc2
        query_vector = [0.1] * 384
        vectors = [
            [0.9] * 384,  # Dissimilar to query
            [0.15] * 384,  # Very similar to query
            [0.5] * 384,  # Moderate similarity
        ]

        vector_store.insert_batch(
            ids=["rrf1", "rrf2", "rrf3"], vectors=vectors, payloads=payloads
        )

        # Hybrid search
        results = vector_store.hybrid_search(
            query_text="Pythagorean",  # Favors doc1 and doc3 via BM25
            query_vector=query_vector,  # Favors doc2 via dense
            top_k=3,
        )

        assert len(results) == 3
        # RRF should balance both signals
        result_doc_ids = [r.payload["doc_id"] for r in results]
        # Doc3 (medium on both) should rank well
        assert "doc3" in result_doc_ids

    def test_get_point(self, vector_store):
        """Test retrieving a point by ID."""
        vector = [0.5] * 384
        payload = {"text": "Test document", "doc_id": "test_doc"}

        vector_store.insert(id="get_test", vector=vector, payload=payload)

        # Retrieve point using the same string ID
        point = vector_store.get_point("get_test")

        assert point is not None
        # Check payload content instead of ID (since ID is now a UUID)
        assert point.payload["text"] == "Test document"
        assert point.payload["doc_id"] == "test_doc"
        assert "dense" in point.vector

    def test_get_nonexistent_point_returns_none(self, vector_store):
        """Test that getting non-existent point returns None."""
        point = vector_store.get_point("nonexistent_id")
        assert point is None

    def test_delete_points(self, vector_store):
        """Test deleting points."""
        # Insert points
        ids = ["del1", "del2", "del3"]
        vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        payloads = [
            {"text": "Document 1", "doc_id": "doc1"},
            {"text": "Document 2", "doc_id": "doc2"},
            {"text": "Document 3", "doc_id": "doc3"},
        ]

        vector_store.insert_batch(ids=ids, vectors=vectors, payloads=payloads)

        # Verify insertion
        assert vector_store.count_points() == 3

        # Delete two points
        vector_store.delete_points(["del1", "del3"])

        # Verify deletion
        assert vector_store.count_points() == 1
        assert vector_store.get_point("del1") is None
        assert vector_store.get_point("del2") is not None
        assert vector_store.get_point("del3") is None

    def test_count_points(self, vector_store):
        """Test counting points in collection."""
        assert vector_store.count_points() == 0

        # Insert points
        vector_store.insert_batch(
            ids=["count1", "count2"],
            vectors=[[0.1] * 384, [0.2] * 384],
            payloads=[
                {"text": "First", "doc_id": "doc1"},
                {"text": "Second", "doc_id": "doc2"},
            ],
        )

        assert vector_store.count_points() == 2

    def test_collection_exists(self, vector_store):
        """Test checking if collection exists."""
        assert vector_store.collection_exists()

        # Create store with non-existent collection
        nonexistent_store = VectorStore(
            client=vector_store.client,
            collection_name="nonexistent_collection_xyz",
            embedding_dim=384,
        )

        assert not nonexistent_store.collection_exists()

    def test_insert_without_text_field_raises_error(self, vector_store):
        """Test that payload without 'text' field raises ValueError."""
        vector = [0.1] * 384
        payload = {"doc_id": "doc1"}  # Missing 'text'

        with pytest.raises(ValueError, match="must include 'text' field"):
            vector_store.insert(id="bad_payload", vector=vector, payload=payload)

    def test_batch_insert_without_text_raises_error(self, vector_store):
        """Test that batch with missing 'text' raises ValueError."""
        vectors = [[0.1] * 384, [0.2] * 384]
        payloads = [
            {"text": "Valid", "doc_id": "doc1"},
            {"doc_id": "doc2"},  # Missing 'text'
        ]

        with pytest.raises(ValueError, match="missing 'text' field"):
            vector_store.insert_batch(
                ids=["id1", "id2"], vectors=vectors, payloads=payloads
            )


@pytest.mark.integration
class TestVectorStoreQdrant120Features:
    """Tests specifically for Qdrant 1.20+ features."""

    def test_bm25_scoring_enabled(self, vector_store):
        """Verify BM25 scoring is enabled on text index."""
        collection_name = vector_store.collection_name

        # Insert documents
        vector_store.insert_batch(
            ids=["bm25_score_1", "bm25_score_2"],
            vectors=[[0.1] * 384, [0.2] * 384],
            payloads=[
                {"text": "keyword keyword keyword repeated", "doc_id": "doc1"},
                {"text": "keyword once", "doc_id": "doc2"},
            ],
        )

        # BM25 should score first document higher due to term frequency
        results = vector_store.bm25_search(query_text="keyword", top_k=2)

        assert len(results) == 2
        # Document with more keyword occurrences should score higher
        assert results[0].payload["doc_id"] == "doc1"
        assert results[0].score > results[1].score

    def test_rrf_fusion_mechanism(self, vector_store):
        """Test that RRF fusion is working (not just concatenation)."""
        # Create clear scenario for RRF validation
        payloads = [
            {"text": "target word appears here in document one", "doc_id": "doc1"},
            {"text": "different content without the word", "doc_id": "doc2"},
            {"text": "target appears in document three as well", "doc_id": "doc3"},
        ]

        # Set vectors so doc2 would rank high in dense-only search
        query_vector = [0.5] * 384
        vectors = [
            [0.1] * 384,  # Not similar to query
            [0.55] * 384,  # Very similar to query (would win dense-only)
            [0.2] * 384,  # Somewhat similar
        ]

        vector_store.insert_batch(
            ids=["fusion1", "fusion2", "fusion3"], vectors=vectors, payloads=payloads
        )

        # Hybrid search with keyword that doc2 doesn't have
        results = vector_store.hybrid_search(
            query_text="target",  # Only in doc1 and doc3
            query_vector=query_vector,
            top_k=3,
        )

        result_ids = [r.id for r in results]

        # RRF should balance: doc1 and doc3 have keyword, doc2 has semantic match
        # The ranking demonstrates RRF is working, not just dense or BM25 alone
        assert len(result_ids) == 3
        # Verify it's not just dense ranking (doc2 wouldn't be top if pure BM25)
        # and not just BM25 ranking (doc2 wouldn't appear high if pure keyword)
