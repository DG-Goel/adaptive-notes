"""
LangGraph tutoring workflow.

Orchestrates the complete Q&A flow: retrieval → evidence check → generation → verification.
"""

import logging
import re
from typing import Literal
from langgraph.graph import StateGraph, END

from src.services.tutoring.state import TutoringState
from src.core.retrieval_pipeline import get_retrieval_pipeline
from src.core.evidence_selector import get_evidence_selector
from src.core.llm_client import get_llm_client
from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)


def retrieval_node(state: TutoringState) -> TutoringState:
    """
    Retrieve relevant context chunks.
    
    Performs hybrid retrieval with reranking and context expansion.
    """
    question = state["question"].strip()
    retry_count = state.get("retry_count", 0)
    
    logger.info(
        f"Retrieval node (attempt {retry_count + 1})",
        extra={"question_length": len(question)}
    )
    
    # Get retrieval pipeline
    pipeline = get_retrieval_pipeline()
    
    # Retrieve with context expansion
    scope = {}
    if state.get('notes_file'):
        from src.api.security import get_allowed_notes_directory
        scope['doc_path'] = str(get_allowed_notes_directory() / state['notes_file'])
    results = pipeline.retrieve_with_context_expansion(
        query=question,
        top_k=state.get('top_k', 5),
        expand_parents=True,
        **scope,
    )
    
    # Convert results to dict format for LLM
    chunks = [
        {
            "text": r.text,
            "doc_title": r.doc_title,
            "doc_path": r.doc_path,
            "section_path": " > ".join(r.section_path) if r.section_path else "",
            "chunk_id": r.chunk_id,
            "score": r.final_score,
        }
        for r in results
    ]
    
    logger.info(
        f"Retrieved {len(chunks)} chunks",
        extra={"avg_score": sum(r.final_score for r in results) / len(results) if results else 0}
    )
    
    return {
        **state,
        "retrieved_chunks": chunks,
        "retrieval_results": results,
    }


def evidence_check_node(state: TutoringState) -> TutoringState:
    """
    Assess whether retrieved evidence is sufficient.
    
    Checks chunk count, relevance scores, and query coverage.
    """
    question = state["question"]
    retrieval_results = state.get("retrieval_results", [])
    
    logger.info("Evidence check node")
    
    # Get evidence selector
    selector = get_evidence_selector()
    
    # Assess evidence
    assessment = selector.assess_evidence(
        query=question,
        retrieved_results=retrieval_results
    )
    
    logger.info(
        f"Evidence assessment: {assessment.is_sufficient}",
        extra={
            "reason": assessment.reason,
            "confidence": assessment.confidence_score,
            "coverage": assessment.coverage_score,
        }
    )
    
    return {
        **state,
        "evidence_sufficient": assessment.is_sufficient,
        "evidence_assessment": {
            "is_sufficient": assessment.is_sufficient,
            "reason": assessment.reason,
            "confidence_score": assessment.confidence_score,
            "coverage_score": assessment.coverage_score,
            "avg_rerank_score": assessment.avg_rerank_score,
            "chunk_count": assessment.chunk_count,
        }
    }


def should_retry(state: TutoringState) -> Literal["retry", "generate", "admit_unknown"]:
    """
    Decide whether to retry retrieval, generate answer, or admit unknown.
    
    Logic:
    - If evidence sufficient: proceed to generation
    - If evidence insufficient and retries < 2: retry
    - If evidence insufficient and retries >= 2: admit unknown
    """
    sufficient = state.get("evidence_sufficient", False)
    retry_count = state.get("retry_count", 0)
    
    if sufficient:
        logger.info("Evidence sufficient, proceeding to generation")
        return "generate"
    elif retry_count < 2:
        logger.info(f"Evidence insufficient, retry {retry_count + 1}/2")
        return "retry"
    else:
        logger.info("Evidence insufficient after 2 retries, admitting unknown")
        return "admit_unknown"


def retry_node(state: TutoringState) -> TutoringState:
    """
    Prepare for retrieval retry.
    
    Increments retry count for next retrieval attempt.
    """
    retry_count = state.get("retry_count", 0)
    
    logger.info(f"Retry node: incrementing retry_count to {retry_count + 1}")
    
    return {
        **state,
        "retry_count": retry_count + 1,
    }


def generation_node(state: TutoringState) -> TutoringState:
    """
    Generate answer from retrieved context.
    
    Uses LLM to generate grounded answer with citations.
    """
    question = state["question"]
    chunks = state.get("retrieved_chunks", [])
    mode = state.get("mode", "strict")
    admit_unknown = state.get("admit_unknown", False)
    
    logger.info(
        "Generation node",
        extra={"mode": mode, "chunks": len(chunks), "admit_unknown": admit_unknown}
    )
    
    # If admitting unknown, return standard message
    if admit_unknown:
        answer = "I don't have enough information in your notes to answer this question."
        citations = []
        
        logger.info("Admitting insufficient information")
        
        return {
            **state,
            "answer": answer,
            "citations": citations,
        }
    
    # Get LLM client (uses configured provider from settings)
    settings = get_settings()
    llm_client = get_llm_client(
        provider=settings.llm_provider, 
        model=settings.groq_model,
        api_key=settings.groq_api_key
    )
    
    # Extract text from chunks
    context_texts = [chunk["text"] for chunk in chunks]
    
    # Generate answer
    result = llm_client.generate_with_context(
        question=question,
        context_chunks=context_texts,
        mode=mode
    )
    
    # Extract citations from chunks
    citations = [
        {
            "doc_title": chunk["doc_title"],
            "doc_path": chunk["doc_path"],
            "section_path": chunk["section_path"],
            "chunk_id": chunk["chunk_id"],
        }
        for chunk in chunks[:3]  # Top 3 sources
    ]
    
    logger.info(
        "Answer generated",
        extra={
            "answer_length": len(result.text),
            "citations_count": len(citations),
            "tokens": result.total_tokens,
        }
    )
    
    return {
        **state,
        "answer": result.text,
        "citations": citations,
        "metadata": {
            **state.get("metadata", {}),
            "generation": {
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
            }
        }
    }


def citation_verify_node(state: TutoringState) -> TutoringState:
    """
    Verify answer grounding in sources.
    
    Checks that answer is properly grounded in retrieved chunks.
    For MVP, this is a simple check. Can be enhanced with NLI models later.
    """
    answer = state.get("answer", "")
    chunks = state.get("retrieved_chunks", [])
    mode = state.get("mode", "strict")
    admit_unknown = state.get("admit_unknown", False)
    
    logger.info("Citation verification node")
    
    # If admitting unknown, verification passes trivially
    if admit_unknown:
        verification = {
            "grounded": True,
            "reason": "Admitted insufficient information (correct behavior)",
            "score": 1.0
        }
    else:
        # Simple heuristic verification for MVP
        # Check if answer contains content from chunks
        chunk_texts = [c["text"].lower() for c in chunks]
        answer_lower = answer.lower()
        
        # Check for meaningful overlap - at least 3 content words from any chunk
        # Skip common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "can", "this", "that", "these", "those", "it", "its"}
        
        def get_content_words(text):
            """Extract meaningful content words."""
            # Remove punctuation and split
            words = re.findall(r'\b\w+\b', text.lower())
            return [w for w in words if len(w) > 3 and w not in common_words]
        
        answer_words = set(get_content_words(answer_lower))
        
        has_overlap = False
        for chunk_text in chunk_texts:
            chunk_words = set(get_content_words(chunk_text))
            overlap_count = len(answer_words & chunk_words)
            if overlap_count >= 3:  # At least 3 meaningful words overlap
                has_overlap = True
                break
        
        if mode == "strict":
            # Strict mode should cite sources in [Document Name] format
            # Check for citation patterns that match the prompt instruction
            has_citation = (
                ("[" in answer and "]" in answer) or  # [Document Name] format
                "From your notes" in answer or 
                "Based on your notes" in answer or
                "According to your notes" in answer
            )
            grounded = has_overlap and has_citation
            reason = "Answer grounded with citations" if grounded else "Missing proper grounding/citations"
        else:
            # Teaching mode is more flexible
            grounded = has_overlap
            reason = "Answer references source material" if grounded else "Answer lacks source connection"
        
        verification = {
            "grounded": grounded,
            "reason": reason,
            "score": 1.0 if grounded else 0.5
        }
    
    logger.info(
        f"Verification: {verification['grounded']}",
        extra={"reason": verification["reason"]}
    )
    
    return {
        **state,
        "metadata": {
            **state.get("metadata", {}),
            "verification": verification
        }
    }


# Build workflow
def create_tutoring_workflow() -> StateGraph:
    """
    Create the LangGraph tutoring workflow.
    
    Workflow structure:
    START → retrieval → evidence_check → [retry/generate/admit] → verify → END
    
    Returns:
        Compiled StateGraph workflow
    """
    logger.info("Creating tutoring workflow")
    
    # Initialize workflow
    workflow = StateGraph(TutoringState)
    
    # Add nodes
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("evidence_check", evidence_check_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("generation", generation_node)
    workflow.add_node("verify", citation_verify_node)
    
    # Define edges
    workflow.add_edge("retrieval", "evidence_check")
    
    # Conditional edges from evidence check
    workflow.add_conditional_edges(
        "evidence_check",
        should_retry,
        {
            "retry": "retry",
            "generate": "generation",
            "admit_unknown": "generation",  # Also goes to generation with admit_unknown=True
        }
    )
    
    # Retry loops back to retrieval
    workflow.add_edge("retry", "retrieval")
    
    # Generation goes to verification
    workflow.add_edge("generation", "verify")
    
    # Verification is the end
    workflow.add_edge("verify", END)
    
    # Set entry point
    workflow.set_entry_point("retrieval")
    
    logger.info("Tutoring workflow created")
    
    return workflow


# Singleton workflow instance
_workflow_app = None


def get_tutoring_workflow():
    """
    Get compiled tutoring workflow (singleton).
    
    Returns:
        Compiled LangGraph workflow
    """
    global _workflow_app
    
    if _workflow_app is None:
        logger.info("Compiling tutoring workflow")
        workflow = create_tutoring_workflow()
        _workflow_app = workflow.compile()
        logger.info("Tutoring workflow compiled successfully")
    
    return _workflow_app


def reset_workflow():
    """Reset workflow singleton (useful for testing)."""
    global _workflow_app
    _workflow_app = None
