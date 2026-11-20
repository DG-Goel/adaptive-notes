"""
FastAPI application for Universal AI Tutor.

Provides REST API endpoints for document ingestion and Q&A.

SECURITY NOTES:
- File paths are validated and restricted to allowed directory
- Input validation on all requests
- Localhost binding by default (configure API_HOST in .env)
- File size and type restrictions enforced
- Sensitive data redacted in logs
"""

import logging
import os
import time
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.schemas import (
    IngestRequest,
    IngestResponse,
    AskRequest,
    AskResponse,
    Citation,
    HealthResponse,
    ErrorResponse,
)
from src.api.security import (
    validate_file_paths,
    validate_question,
    print_security_warnings,
    log_security_event,
)
from src.services.ingestion_service import get_ingestion_service
from src.services.tutoring.workflow import get_tutoring_workflow
from src.services.tutoring.state import TutoringState
from src.core.vector_store import get_vector_store
from src.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting Universal AI Tutor API")
    
    # Print security warnings
    print_security_warnings()
    
    # Initialize components
    try:
        vector_store = get_vector_store()
        
        # Ensure collection exists
        if not vector_store.collection_exists():
            logger.info("Creating Qdrant collection")
            vector_store.create_collection()
        
        # Initialize workflow
        workflow = get_tutoring_workflow()
        
        logger.info("API startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Universal AI Tutor API")


# Create FastAPI app
app = FastAPI(
    title="Universal AI Tutor API",
    description="RAG-based tutoring system with source-grounded answers",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else None,
            status_code=500
        ).model_dump()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns API status and component health.
    """
    try:
        vector_store = get_vector_store()
        collection_exists = vector_store.collection_exists()
        
        components = {
            "vector_store": "healthy" if collection_exists else "unhealthy",
            "workflow": "healthy",
        }
        
        return HealthResponse(
            status="healthy" if all(v == "healthy" for v in components.values()) else "degraded",
            version="1.0.0",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            components={"error": str(e)}
        )


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest) -> IngestResponse:
    """
    Ingest documents into the knowledge base.
    
    Parses, chunks, embeds, and indexes documents.
    
    SECURITY:
    - File paths are validated against allowed directory
    - File size and type restrictions enforced
    - Path traversal attempts blocked
    
    Args:
        request: IngestRequest with file paths and options
        
    Returns:
        IngestResponse with ingestion results
        
    Raises:
        HTTPException: If validation fails or ingestion fails
    """
    logger.info(
        f"Ingestion request",
        extra={
            "file_count": len(request.file_paths),
            "overwrite": request.overwrite
        }
    )
    
    # Validate file paths
    valid_paths, validation_errors = validate_file_paths(request.file_paths)
    
    if validation_errors and not valid_paths:
        # All files failed validation
        log_security_event("invalid_file_paths", {
            "error_count": len(validation_errors),
            "errors": validation_errors[:5]  # Log first 5 errors
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "File validation failed",
                "validation_errors": validation_errors
            }
        )
    
    if validation_errors:
        # Some files failed, log warning but continue with valid ones
        logger.warning(
            f"Some files failed validation: {len(validation_errors)}/{len(request.file_paths)}",
            extra={"validation_errors": validation_errors[:5]}
        )
    
    start_time = time.time()
    
    try:
        # Get ingestion service
        ingestion_service = get_ingestion_service()
        
        # Ingest documents (use validated paths)
        result = ingestion_service.ingest_documents(
            file_paths=valid_paths,
            overwrite=request.overwrite
        )
        
        processing_time = time.time() - start_time
        
        # Determine status
        if result.successful == result.total_files:
            response_status = "success"
        elif result.successful > 0:
            response_status = "partial"
        else:
            response_status = "failed"
        
        # Collect errors (include validation errors)
        errors = validation_errors.copy()
        errors.extend([
            f"{r.doc_id}: {r.error}" 
            for r in result.results 
            if not r.success and r.error
        ])
        
        logger.info(
            f"Ingestion complete: {result.successful}/{len(valid_paths)} succeeded",
            extra={
                "processing_time": processing_time,
                "chunks_indexed": result.total_chunks_indexed,
                "validation_errors": len(validation_errors)
            }
        )
        
        return IngestResponse(
            status=response_status,
            total_files=len(request.file_paths),  # Original count
            successful=result.successful,
            failed=result.failed + len(validation_errors),
            total_chunks_indexed=result.total_chunks_indexed,
            processing_time_seconds=processing_time,
            errors=errors if errors else []
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/api/v1/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Ask a question and get an answer.
    
    Executes the tutoring workflow: retrieval → evidence check → generation → verification.
    
    SECURITY:
    - Question validated for length and suspicious patterns
    - Input sanitization applied
    
    Args:
        request: AskRequest with question and options
        
    Returns:
        AskResponse with answer and citations
        
    Raises:
        HTTPException: If validation fails or Q&A fails
    """
    # Validate question
    is_valid, error_msg = validate_question(request.question)
    if not is_valid:
        log_security_event("invalid_question", {
            "error": error_msg,
            "question_length": len(request.question) if request.question else 0
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    logger.info(
        f"Question asked",
        extra={
            "question_length": len(request.question),
            "mode": request.mode,
            "top_k": request.top_k
        }
    )
    
    start_time = time.time()
    
    try:
        # Get workflow
        workflow = get_tutoring_workflow()
        
        # Prepare initial state
        initial_state: TutoringState = {
            "question": request.question.strip(),  # Sanitize
            "mode": request.mode,
            "conversation_history": request.conversation_history,
            "top_k": request.top_k,
            "notes_file": request.notes_file,
            "retry_count": 0,
            "metadata": {},
        }
        
        # Execute workflow
        final_state = workflow.invoke(initial_state)
        
        processing_time = time.time() - start_time
        
        # Extract results
        answer = final_state.get("answer", "")
        raw_citations = final_state.get("citations", [])
        metadata = final_state.get("metadata", {})
        
        # Convert citations to schema
        citations = [
            Citation(
                doc_title=c.get("doc_title", ""),
                doc_path=c.get("doc_path", ""),
                section_path=c.get("section_path", ""),
                chunk_id=c.get("chunk_id", "")
            )
            for c in raw_citations
        ]
        
        # Add processing time to metadata
        metadata["processing_time_seconds"] = processing_time
        
        # Add evidence assessment if available
        if "evidence_assessment" in final_state:
            metadata["evidence_assessment"] = final_state["evidence_assessment"]
        
        logger.info(
            f"Answer generated",
            extra={
                "answer_length": len(answer),
                "citations_count": len(citations),
                "processing_time": processing_time
            }
        )
        
        return AskResponse(
            answer=answer,
            citations=citations,
            mode=request.mode,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": "Universal AI Tutor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Use settings for host/port (defaults to localhost for security)
    host = os.getenv("API_HOST", "127.0.0.1")  # Default to localhost, not 0.0.0.0
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
