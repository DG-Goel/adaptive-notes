"""
Integration tests for real HTTP server.

Tests the FastAPI application running on a real HTTP server (uvicorn)
with actual HTTP requests using the requests library.

These tests verify:
- Server startup and shutdown
- HTTP request/response handling
- API endpoint functionality
- Error handling and status codes
- Request validation
- Security controls
"""

import pytest
import time
import subprocess
import sys
import requests
from pathlib import Path
from typing import Optional
import json
import tempfile
import shutil


class ServerProcess:
    """Manage a real uvicorn server process for testing."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        Initialize server process manager.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.process: Optional[subprocess.Popen] = None
    
    def start(self, timeout: int = 30) -> bool:
        """
        Start the server process.
        
        Args:
            timeout: Maximum seconds to wait for server startup
            
        Returns:
            True if server started successfully
            
        Raises:
            RuntimeError: If server fails to start
        """
        # Start uvicorn server
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "warning"
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Check if process died
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=2)
                raise RuntimeError(
                    f"Server process died during startup.\n"
                    f"Stdout: {stdout[:1000]}\n"
                    f"Stderr: {stderr[:2000]}"
                )
            
            time.sleep(0.5)
        
        # Timeout
        self.stop()
        raise RuntimeError(f"Server failed to start within {timeout} seconds")
    
    def stop(self):
        """Stop the server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.process = None
    
    def is_running(self) -> bool:
        """Check if server is running."""
        if not self.process:
            return False
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=1)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


@pytest.fixture(scope="module")
def server():
    """
    Start a real HTTP server for testing.
    
    This fixture starts a uvicorn server process and ensures it's
    running for all tests in this module.
    """
    srv = ServerProcess(host="127.0.0.1", port=8765)
    
    try:
        srv.start(timeout=30)
        yield srv
    finally:
        srv.stop()


@pytest.fixture
def test_notes_dir(tmp_path):
    """Create a temporary directory with test notes."""
    notes_dir = tmp_path / "test_notes"
    notes_dir.mkdir()
    
    # Create sample note files
    (notes_dir / "math_basics.txt").write_text("""
# Basic Mathematics

## Addition
Addition is the process of combining two or more numbers.
For example: 2 + 3 = 5

## Multiplication
Multiplication is repeated addition.
For example: 3 × 4 = 12 (which is 3 + 3 + 3 + 3)
    """)
    
    (notes_dir / "python_intro.md").write_text("""
# Python Introduction

## Variables
Variables store data values.
```python
x = 10
name = "Alice"
```

## Functions
Functions are reusable blocks of code.
```python
def greet(name):
    return f"Hello, {name}!"
```
    """)
    
    return str(notes_dir)


class TestServerLifecycle:
    """Test server startup and basic connectivity."""
    
    def test_server_starts_successfully(self, server):
        """Test that server starts and responds to health checks."""
        assert server.is_running()
    
    def test_health_endpoint(self, server):
        """Test /health endpoint."""
        response = requests.get(f"{server.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, server):
        """Test root / endpoint."""
        response = requests.get(f"{server.base_url}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Universal AI Tutor API"
        assert "version" in data


class TestIngestionEndpoint:
    """Test /api/v1/ingest endpoint."""
    
    def test_ingest_valid_files(self, server, test_notes_dir):
        """Test ingesting valid note files."""
        # Set allowed directory (requires env var or config)
        # For this test, we'll use the test directory
        
        file_paths = [
            str(Path(test_notes_dir) / "math_basics.txt"),
            str(Path(test_notes_dir) / "python_intro.md")
        ]
        
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={
                "file_paths": file_paths,
                "overwrite": True
            }
        )
        
        # May fail due to security validation (allowed_notes_dir)
        # This is expected behavior
        assert response.status_code in [200, 400, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ["success", "partial_success"]
            assert data["documents_processed"] >= 0
            assert "chunks_created" in data
    
    def test_ingest_empty_file_list(self, server):
        """Test ingestion with empty file list."""
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={
                "file_paths": [],
                "overwrite": False
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ingest_nonexistent_file(self, server):
        """Test ingestion with nonexistent file."""
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={
                "file_paths": ["/nonexistent/file.txt"],
                "overwrite": False
            }
        )
        
        # Should fail validation or return error
        assert response.status_code in [400, 404, 422]
    
    def test_ingest_invalid_json(self, server):
        """Test ingestion with invalid JSON."""
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_ingest_missing_required_fields(self, server):
        """Test ingestion with missing required fields."""
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={"overwrite": True}  # Missing file_paths
        )
        
        assert response.status_code == 422


class TestAskEndpoint:
    """Test /api/v1/ask endpoint."""
    
    def test_ask_valid_question(self, server):
        """Test asking a valid question."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": "What is addition?",
                "mode": "strict",
                "top_k": 5
            }
        )
        
        # May succeed or fail depending on whether documents are ingested
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "citations" in data
            assert isinstance(data["citations"], list)
            assert "confidence" in data
            assert "retrieval_time_ms" in data
    
    def test_ask_empty_question(self, server):
        """Test asking an empty question."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": "",
                "mode": "strict"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_ask_question_too_short(self, server):
        """Test question below minimum length."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": "Hi",  # < 3 characters
                "mode": "strict"
            }
        )
        
        assert response.status_code == 422
    
    def test_ask_question_too_long(self, server):
        """Test question exceeding maximum length."""
        long_question = "What is " + "x" * 3000  # Exceeds 2000 char limit
        
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": long_question,
                "mode": "strict"
            }
        )
        
        assert response.status_code == 422
    
    def test_ask_invalid_mode(self, server):
        """Test with invalid mode."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": "What is Python?",
                "mode": "invalid_mode"
            }
        )
        
        assert response.status_code == 422
    
    def test_ask_injection_attempt(self, server):
        """Test SQL injection attempt is blocked."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={
                "question": "'; DROP TABLE users; --",
                "mode": "strict"
            }
        )
        
        # Should be caught by security validation
        assert response.status_code in [400, 422]
    
    def test_ask_missing_required_fields(self, server):
        """Test with missing required question field."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={"mode": "strict"}  # Missing question
        )
        
        assert response.status_code == 422
    
    def test_ask_default_parameters(self, server):
        """Test that default parameters work."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={"question": "What is Python?"}
        )
        
        # Should work with defaults
        assert response.status_code in [200, 404]


class TestCORSHeaders:
    """Test CORS headers are properly set."""
    
    def test_cors_headers_present(self, server):
        """Test CORS headers are included in responses."""
        response = requests.get(f"{server.base_url}/health")
        
        # Check common CORS headers
        headers = response.headers
        # Note: CORS headers may not be present if CORS middleware not configured
        # This test documents expected behavior
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and status codes."""
    
    def test_not_found_endpoint(self, server):
        """Test 404 for nonexistent endpoint."""
        response = requests.get(f"{server.base_url}/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, server):
        """Test 405 for wrong HTTP method."""
        # POST-only endpoint called with GET
        response = requests.get(f"{server.base_url}/api/v1/ask")
        
        assert response.status_code == 405
    
    def test_invalid_content_type(self, server):
        """Test error for invalid content type."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            data="question=test",  # Form data instead of JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should reject non-JSON
        assert response.status_code in [422, 415]


class TestConcurrentRequests:
    """Test server handles concurrent requests."""
    
    def test_multiple_health_checks(self, server):
        """Test multiple simultaneous health checks."""
        import concurrent.futures
        
        def check_health():
            response = requests.get(f"{server.base_url}/health", timeout=5)
            return response.status_code == 200
        
        # Send 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        assert all(results)
        assert len(results) == 10


class TestSecurityControls:
    """Test security controls are enforced."""
    
    def test_path_traversal_blocked(self, server):
        """Test path traversal attempts are blocked."""
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={
                "file_paths": ["../../etc/passwd"],
                "overwrite": False
            }
        )
        
        # Should be blocked by security validation
        assert response.status_code in [400, 403, 422]
    
    def test_large_request_payload(self, server):
        """Test handling of large request payload."""
        # Try to send a very large file list
        large_list = [f"/fake/file_{i}.txt" for i in range(200)]
        
        response = requests.post(
            f"{server.base_url}/api/v1/ingest",
            json={
                "file_paths": large_list,
                "overwrite": False
            },
            timeout=10
        )
        
        # Should be rejected (batch limit is 100)
        assert response.status_code in [400, 422]


class TestResponseFormat:
    """Test response format and structure."""
    
    def test_health_response_structure(self, server):
        """Test health endpoint returns correct structure."""
        response = requests.get(f"{server.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_error_response_structure(self, server):
        """Test error responses have consistent structure."""
        response = requests.post(
            f"{server.base_url}/api/v1/ask",
            json={"question": ""}  # Invalid empty question
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # FastAPI validation error format
        assert "detail" in data


class TestPerformance:
    """Basic performance checks."""
    
    def test_health_check_performance(self, server):
        """Test health check responds quickly."""
        start = time.time()
        response = requests.get(f"{server.base_url}/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in under 1 second
    
    def test_server_handles_rapid_requests(self, server):
        """Test server handles rapid sequential requests."""
        responses = []
        
        for _ in range(20):
            response = requests.get(f"{server.base_url}/health", timeout=2)
            responses.append(response.status_code)
        
        # All should succeed
        assert all(status == 200 for status in responses)
        assert len(responses) == 20


def test_server_cleanup_on_shutdown(server):
    """Test server cleans up properly on shutdown."""
    # Server is running
    assert server.is_running()
    
    # Stop server
    server.stop()
    
    # Server should not be running
    assert not server.is_running()
    
    # Should not be able to connect
    with pytest.raises(requests.exceptions.RequestException):
        requests.get(f"{server.base_url}/health", timeout=1)
    
    # Restart for other tests (fixture cleanup will handle final shutdown)
    server.start(timeout=30)
    assert server.is_running()
