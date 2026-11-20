"""
Integration tests for FastAPI endpoints.

Tests API with real components (mocked LLM).
"""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.vector_store import get_vector_store
from src.services.ingestion_service import get_ingestion_service


@pytest.fixture(scope="module")
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def setup_collection():
    """Ensure collection exists for tests."""
    vector_store = get_vector_store()
    if not vector_store.collection_exists():
        vector_store.create_collection()
    yield
    # Cleanup handled by other fixtures


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client, setup_collection):
        """Test health endpoint returns status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert data["version"] == "1.0.0"


@pytest.mark.integration
class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Universal AI Tutor API"


@pytest.mark.integration
class TestIngestEndpoint:
    """Test document ingestion endpoint."""
    
    def test_ingest_single_document(self, client, setup_collection):
        """Test ingesting a single document."""
        # Create temp document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Test Document

## Introduction

This is a test document for API testing.

## Content

Machine learning is a subset of artificial intelligence.
""")
            temp_path = f.name
        
        try:
            response = client.post(
                "/api/v1/ingest",
                json={
                    "file_paths": [temp_path],
                    "overwrite": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] in ["success", "partial"]
            assert data["total_files"] == 1
            assert data["successful"] >= 1
            assert data["total_chunks_indexed"] > 0
            assert data["processing_time_seconds"] > 0
        finally:
            os.unlink(temp_path)
    
    def test_ingest_invalid_file_path(self, client):
        """Test ingesting non-existent file."""
        response = client.post(
            "/api/v1/ingest",
            json={
                "file_paths": ["/nonexistent/file.txt"],
                "overwrite": False
            }
        )
        
        # Should return 200 but with failed status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["failed"] == 1
    
    def test_ingest_empty_file_list(self, client):
        """Test ingesting with empty file list."""
        response = client.post(
            "/api/v1/ingest",
            json={
                "file_paths": [],
                "overwrite": False
            }
        )
        
        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
class TestAskEndpoint:
    """Test question answering endpoint."""
    
    @pytest.fixture(autouse=True)
    def setup_knowledge_base(self, setup_collection):
        """Ingest test document before Q&A tests."""
        # Create and ingest test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# Machine Learning Guide

## Introduction

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

## Types of ML

Supervised learning uses labeled data.
Unsupervised learning finds patterns in unlabeled data.

## Applications

Machine learning is used in computer vision, NLP, and recommendation systems.
""")
            temp_path = f.name
        
        try:
            ingestion_service = get_ingestion_service()
            result = ingestion_service.ingest_documents(
                file_paths=[temp_path],
                overwrite=True
            )
            assert result.successful > 0
        finally:
            os.unlink(temp_path)
    
    def test_ask_question_strict_mode(self, client):
        """Test asking question in strict mode."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is machine learning?",
                "mode": "strict",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "citations" in data
        assert data["mode"] == "strict"
        assert "metadata" in data
        assert "processing_time_seconds" in data["metadata"]
    
    def test_ask_question_teaching_mode(self, client):
        """Test asking question in teaching mode."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is supervised learning?",
                "mode": "teaching",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert data["mode"] == "teaching"
    
    def test_ask_empty_question(self, client):
        """Test asking empty question."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "",
                "mode": "strict"
            }
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_ask_with_conversation_history(self, client):
        """Test asking with conversation history."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "Tell me more about applications",
                "mode": "strict",
                "conversation_history": [
                    {
                        "question": "What is machine learning?",
                        "answer": "ML is a subset of AI."
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
    
    def test_ask_question_not_in_notes(self, client):
        """Test asking question not covered in notes."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is quantum computing?",
                "mode": "strict",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should admit not knowing
        assert "don't have enough information" in data["answer"].lower() or \
               "insufficient" in data["answer"].lower()
    
    def test_ask_invalid_mode(self, client):
        """Test asking with invalid mode."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is ML?",
                "mode": "invalid_mode"
            }
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_ask_invalid_top_k(self, client):
        """Test asking with invalid top_k."""
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is ML?",
                "mode": "strict",
                "top_k": 100  # Too high
            }
        )
        
        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
class TestAPIEndToEnd:
    """Test complete end-to-end workflow."""
    
    def test_ingest_then_ask(self, client, setup_collection):
        """Test complete workflow: ingest → ask."""
        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("""Python is a high-level programming language.
It is widely used for web development, data science, and automation.
Python has a simple and readable syntax.""")
            temp_path = f.name
        
        try:
            # Step 1: Ingest
            ingest_response = client.post(
                "/api/v1/ingest",
                json={
                    "file_paths": [temp_path],
                    "overwrite": True
                }
            )
            
            assert ingest_response.status_code == 200
            ingest_data = ingest_response.json()
            assert ingest_data["status"] in ["success", "partial"]
            assert ingest_data["total_chunks_indexed"] > 0
            
            # Step 2: Ask question
            ask_response = client.post(
                "/api/v1/ask",
                json={
                    "question": "What is Python used for?",
                    "mode": "strict"
                }
            )
            
            assert ask_response.status_code == 200
            ask_data = ask_response.json()
            assert len(ask_data["answer"]) > 0
            
            # Answer should reference the content
            answer_lower = ask_data["answer"].lower()
            assert any(word in answer_lower for word in ["python", "programming", "development"])
            
        finally:
            os.unlink(temp_path)
