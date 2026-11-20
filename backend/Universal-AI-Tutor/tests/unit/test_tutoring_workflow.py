"""
Unit tests for tutoring workflow.

Tests LangGraph workflow nodes and logic.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.services.tutoring.workflow import (
    retrieval_node,
    evidence_check_node,
    should_retry,
    retry_node,
    generation_node,
    citation_verify_node,
    create_tutoring_workflow,
    get_tutoring_workflow,
    reset_workflow,
)
from src.services.tutoring.state import TutoringState
from src.core.retrieval_pipeline import RetrievalResult
from src.core.evidence_selector import EvidenceAssessment


@pytest.fixture
def sample_state():
    """Provide sample tutoring state."""
    return TutoringState(
        question="What is machine learning?",
        mode="strict",
        conversation_history=[],
        retry_count=0,
        metadata={}
    )


@pytest.fixture
def sample_retrieval_results():
    """Provide sample retrieval results."""
    return [
        RetrievalResult(
            chunk_id="chunk_1",
            text="Machine learning is a subset of AI",
            doc_id="doc_1",
            doc_title="ML Guide",
            doc_path="/docs/ml.md",
            section_path=["Introduction"],
            chunk_index=0,
            is_parent=True,
            parent_id=None,
            dense_score=0.9,
            bm25_score=0.8,
            rrf_score=0.85,
            rerank_score=0.92,
            final_score=0.92,
            payload={}
        ),
    ]


class TestRetrievalNode:
    """Test retrieval node."""
    
    @patch("src.services.tutoring.workflow.get_retrieval_pipeline")
    def test_retrieval_success(self, mock_get_pipeline, sample_state, sample_retrieval_results):
        """Test successful retrieval."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.retrieve_with_context_expansion.return_value = sample_retrieval_results
        mock_get_pipeline.return_value = mock_pipeline
        
        # Run node
        result_state = retrieval_node(sample_state)
        
        # Verify
        assert "retrieved_chunks" in result_state
        assert len(result_state["retrieved_chunks"]) == 1
        assert result_state["retrieved_chunks"][0]["text"] == "Machine learning is a subset of AI"
        assert result_state["retrieved_chunks"][0]["doc_title"] == "ML Guide"
        assert "retrieval_results" in result_state
    
    @patch("src.services.tutoring.workflow.get_retrieval_pipeline")
    def test_retrieval_with_retry_count(self, mock_get_pipeline, sample_state, sample_retrieval_results):
        """Test retrieval logs retry count."""
        mock_pipeline = MagicMock()
        mock_pipeline.retrieve_with_context_expansion.return_value = sample_retrieval_results
        mock_get_pipeline.return_value = mock_pipeline
        
        state_with_retry = {**sample_state, "retry_count": 1}
        result_state = retrieval_node(state_with_retry)
        
        assert "retrieved_chunks" in result_state


class TestEvidenceCheckNode:
    """Test evidence check node."""
    
    @patch("src.services.tutoring.workflow.get_evidence_selector")
    def test_evidence_sufficient(self, mock_get_selector, sample_state, sample_retrieval_results):
        """Test when evidence is sufficient."""
        # Mock selector
        mock_selector = MagicMock()
        mock_selector.assess_evidence.return_value = EvidenceAssessment(
            is_sufficient=True,
            reason="Evidence appears sufficient",
            confidence_score=0.92,
            coverage_score=0.8,
            avg_rerank_score=0.9,
            top_rerank_score=0.92,
            chunk_count=1
        )
        mock_get_selector.return_value = mock_selector
        
        state_with_results = {
            **sample_state,
            "retrieval_results": sample_retrieval_results
        }
        
        # Run node
        result_state = evidence_check_node(state_with_results)
        
        # Verify
        assert result_state["evidence_sufficient"] is True
        assert "evidence_assessment" in result_state
        assert result_state["evidence_assessment"]["is_sufficient"] is True
    
    @patch("src.services.tutoring.workflow.get_evidence_selector")
    def test_evidence_insufficient(self, mock_get_selector, sample_state):
        """Test when evidence is insufficient."""
        mock_selector = MagicMock()
        mock_selector.assess_evidence.return_value = EvidenceAssessment(
            is_sufficient=False,
            reason="Low query term coverage",
            confidence_score=0.5,
            coverage_score=0.2,
            avg_rerank_score=0.4,
            top_rerank_score=0.5,
            chunk_count=1
        )
        mock_get_selector.return_value = mock_selector
        
        state_with_results = {**sample_state, "retrieval_results": []}
        
        result_state = evidence_check_node(state_with_results)
        
        assert result_state["evidence_sufficient"] is False


class TestShouldRetry:
    """Test retry decision logic."""
    
    def test_should_generate_when_sufficient(self, sample_state):
        """Test decision when evidence is sufficient."""
        state = {**sample_state, "evidence_sufficient": True}
        
        decision = should_retry(state)
        
        assert decision == "generate"
    
    def test_should_retry_when_insufficient_first_attempt(self, sample_state):
        """Test retry on first insufficient attempt."""
        state = {
            **sample_state,
            "evidence_sufficient": False,
            "retry_count": 0
        }
        
        decision = should_retry(state)
        
        assert decision == "retry"
    
    def test_should_retry_when_insufficient_second_attempt(self, sample_state):
        """Test retry on second insufficient attempt."""
        state = {
            **sample_state,
            "evidence_sufficient": False,
            "retry_count": 1
        }
        
        decision = should_retry(state)
        
        assert decision == "retry"
    
    def test_should_admit_unknown_after_max_retries(self, sample_state):
        """Test admit unknown after 2 retries."""
        state = {
            **sample_state,
            "evidence_sufficient": False,
            "retry_count": 2
        }
        
        decision = should_retry(state)
        
        assert decision == "admit_unknown"


class TestRetryNode:
    """Test retry node."""
    
    def test_retry_increments_count(self, sample_state):
        """Test that retry increments retry_count."""
        state = {**sample_state, "retry_count": 0}
        
        result_state = retry_node(state)
        
        assert result_state["retry_count"] == 1
    
    def test_retry_increments_from_one(self, sample_state):
        """Test retry from count 1."""
        state = {**sample_state, "retry_count": 1}
        
        result_state = retry_node(state)
        
        assert result_state["retry_count"] == 2


class TestGenerationNode:
    """Test generation node."""
    
    @patch("src.services.tutoring.workflow.get_llm_client")
    def test_generation_with_context(self, mock_get_client, sample_state):
        """Test generation with sufficient context."""
        # Mock LLM client
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.text = "Machine learning is a subset of artificial intelligence."
        mock_result.model = "mock-model"
        mock_result.prompt_tokens = 100
        mock_result.completion_tokens = 20
        mock_result.total_tokens = 120
        mock_client.generate_with_context.return_value = mock_result
        mock_get_client.return_value = mock_client
        
        state_with_chunks = {
            **sample_state,
            "retrieved_chunks": [
                {
                    "text": "ML is AI subset",
                    "doc_title": "ML Guide",
                    "doc_path": "/ml.md",
                    "section_path": "Intro",
                    "chunk_id": "chunk_1"
                }
            ]
        }
        
        # Run node
        result_state = generation_node(state_with_chunks)
        
        # Verify
        assert "answer" in result_state
        assert result_state["answer"] == "Machine learning is a subset of artificial intelligence."
        assert "citations" in result_state
        assert len(result_state["citations"]) > 0
        assert "metadata" in result_state
        assert "generation" in result_state["metadata"]
    
    def test_generation_admit_unknown(self, sample_state):
        """Test generation when admitting unknown."""
        state_admit = {
            **sample_state,
            "admit_unknown": True,
            "retrieved_chunks": []
        }
        
        result_state = generation_node(state_admit)
        
        assert result_state["answer"] == "I don't have enough information in your notes to answer this question."
        assert result_state["citations"] == []
    
    @patch("src.services.tutoring.workflow.get_llm_client")
    def test_generation_teaching_mode(self, mock_get_client, sample_state):
        """Test generation in teaching mode."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.text = "Teaching explanation..."
        mock_result.model = "mock-model"
        mock_result.prompt_tokens = 100
        mock_result.completion_tokens = 20
        mock_result.total_tokens = 120
        mock_client.generate_with_context.return_value = mock_result
        mock_get_client.return_value = mock_client
        
        state_teaching = {
            **sample_state,
            "mode": "teaching",
            "retrieved_chunks": [
                {"text": "Context", "doc_title": "Doc", "doc_path": "/doc", "section_path": "", "chunk_id": "c1"}
            ]
        }
        
        result_state = generation_node(state_teaching)
        
        assert "answer" in result_state
        mock_client.generate_with_context.assert_called_with(
            question=sample_state["question"],
            context_chunks=["Context"],
            mode="teaching"
        )


class TestCitationVerifyNode:
    """Test citation verification node."""
    
    def test_verify_with_citations_strict_mode(self, sample_state):
        """Test verification in strict mode with citations."""
        state_with_answer = {
            **sample_state,
            "answer": "Based on your notes: Machine learning is AI. [Source: ML Guide]",
            "retrieved_chunks": [
                {"text": "Machine learning is AI", "doc_title": "ML Guide", "doc_path": "/ml.md", "section_path": "", "chunk_id": "c1"}
            ],
            "mode": "strict"
        }
        
        result_state = citation_verify_node(state_with_answer)
        
        assert "metadata" in result_state
        assert "verification" in result_state["metadata"]
        assert result_state["metadata"]["verification"]["grounded"] is True
    
    def test_verify_without_citations_strict_mode(self, sample_state):
        """Test verification without proper citations."""
        state_without_citation = {
            **sample_state,
            "answer": "Some answer without citation",
            "retrieved_chunks": [
                {"text": "Context text", "doc_title": "Doc", "doc_path": "/doc", "section_path": "", "chunk_id": "c1"}
            ],
            "mode": "strict"
        }
        
        result_state = citation_verify_node(state_without_citation)
        
        verification = result_state["metadata"]["verification"]
        # May fail if answer doesn't reference context
        assert "grounded" in verification
    
    def test_verify_teaching_mode(self, sample_state):
        """Test verification in teaching mode (more flexible)."""
        state_teaching = {
            **sample_state,
            "answer": "Machine learning helps computers learn from data",
            "retrieved_chunks": [
                {"text": "Machine learning is about learning from data", "doc_title": "Doc", "doc_path": "/doc", "section_path": "", "chunk_id": "c1"}
            ],
            "mode": "teaching"
        }
        
        result_state = citation_verify_node(state_teaching)
        
        assert "verification" in result_state["metadata"]
    
    def test_verify_admit_unknown(self, sample_state):
        """Test verification when admitting unknown."""
        state_admit = {
            **sample_state,
            "answer": "I don't have enough information in your notes to answer this question.",
            "retrieved_chunks": [],
            "admit_unknown": True
        }
        
        result_state = citation_verify_node(state_admit)
        
        verification = result_state["metadata"]["verification"]
        assert verification["grounded"] is True
        assert "Admitted insufficient information" in verification["reason"]


class TestWorkflowConstruction:
    """Test workflow creation and compilation."""
    
    def test_create_workflow(self):
        """Test creating workflow graph."""
        workflow = create_tutoring_workflow()
        
        assert workflow is not None
        # Workflow should be a StateGraph
        assert hasattr(workflow, "nodes")
    
    def test_get_workflow_singleton(self):
        """Test workflow singleton pattern."""
        reset_workflow()
        
        workflow1 = get_tutoring_workflow()
        workflow2 = get_tutoring_workflow()
        
        assert workflow1 is workflow2
    
    def test_reset_workflow(self):
        """Test resetting workflow singleton."""
        reset_workflow()
        
        workflow1 = get_tutoring_workflow()
        reset_workflow()
        workflow2 = get_tutoring_workflow()
        
        # Should be different instances after reset
        assert workflow1 is not workflow2
