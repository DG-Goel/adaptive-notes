"""
LLM client for Universal AI Tutor.

Provides interface to language models (currently mocked for MVP).
"""

import os
import logging
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass
from abc import ABC, abstractmethod

from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for LLM generation."""
    
    temperature: float = 0.3
    max_tokens: int = 800
    top_p: float = 0.9
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    metadata: Dict[str, Any]


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            
        Returns:
            GenerationResult with generated text and metadata
        """
        pass
    
    @abstractmethod
    def generate_with_context(
        self,
        question: str,
        context_chunks: List[str],
        mode: Literal["strict", "teaching"] = "strict",
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate answer using retrieved context.
        
        Args:
            question: User's question
            context_chunks: Retrieved text chunks for context
            mode: Generation mode (strict or teaching)
            config: Generation configuration
            
        Returns:
            GenerationResult with answer
        """
        pass


class MockLLMClient(LLMClient):
    """
    Mock LLM client for MVP development and testing.
    
    Returns deterministic responses based on question keywords.
    No real API calls are made.
    """
    
    def __init__(self, model: str = "mock-llm-v1"):
        """
        Initialize mock LLM client.
        
        Args:
            model: Model identifier for logging
        """
        self.model = model
        self.call_count = 0
        
        logger.info(f"MockLLMClient initialized with model={model}")
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate mock response from prompt.
        
        Args:
            prompt: Input prompt
            config: Generation configuration (ignored in mock)
            
        Returns:
            GenerationResult with mock response
        """
        self.call_count += 1
        
        # Simple keyword-based response
        response = self._generate_mock_response(prompt)
        
        # Estimate token counts
        prompt_tokens = len(prompt.split())
        completion_tokens = len(response.split())
        
        logger.debug(
            f"Mock generation #{self.call_count}",
            extra={
                "prompt_length": len(prompt),
                "response_length": len(response),
            }
        )
        
        return GenerationResult(
            text=response,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason="stop",
            metadata={"mock": True, "call_count": self.call_count}
        )
    
    def generate_with_context(
        self,
        question: str,
        context_chunks: List[str],
        mode: Literal["strict", "teaching"] = "strict",
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate mock answer using context.
        
        Args:
            question: User's question
            context_chunks: Retrieved context (used in mock response)
            mode: Generation mode
            config: Generation configuration (ignored in mock)
            
        Returns:
            GenerationResult with mock answer
        """
        self.call_count += 1
        
        # Build prompt (for token estimation)
        context_text = "\n\n".join(context_chunks)
        prompt = self._build_prompt(question, context_text, mode)
        
        # Generate mock response based on question and context
        response = self._generate_contextual_response(
            question, context_chunks, mode
        )
        
        # Estimate tokens
        prompt_tokens = len(prompt.split())
        completion_tokens = len(response.split())
        
        logger.info(
            f"Mock contextual generation #{self.call_count}",
            extra={
                "question_length": len(question),
                "context_chunks": len(context_chunks),
                "mode": mode,
                "response_length": len(response),
            }
        )
        
        return GenerationResult(
            text=response,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason="stop",
            metadata={
                "mock": True,
                "call_count": self.call_count,
                "mode": mode,
                "context_chunks_count": len(context_chunks),
            }
        )
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate simple mock response based on prompt."""
        prompt_lower = prompt.lower()
        
        # Keyword-based responses
        if "machine learning" in prompt_lower:
            return "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
        elif "python" in prompt_lower:
            return "Python is a high-level programming language known for its readability and versatility."
        elif "algorithm" in prompt_lower:
            return "An algorithm is a step-by-step procedure for solving a problem or accomplishing a task."
        else:
            return "This is a mock response. In production, this would be a real LLM-generated answer."
    
    def _generate_contextual_response(
        self,
        question: str,
        context_chunks: List[str],
        mode: str
    ) -> str:
        """Generate mock response using question and context."""
        question_lower = question.lower()
        
        # Check if we have context
        if not context_chunks:
            return "I don't have enough information in your notes to answer this question."
        
        # Extract key terms from question
        key_terms = self._extract_key_terms(question_lower)
        
        # Check if context contains relevant information
        context_text = " ".join(context_chunks).lower()
        relevant_terms = [term for term in key_terms if term in context_text]
        
        if not relevant_terms:
            return "I don't have enough information in your notes to answer this question."
        
        # Generate answer based on mode
        if mode == "strict":
            # Strict mode: cite sources, stay close to context
            answer = f"Based on your notes:\n\n"
            
            # Include relevant snippet from first context chunk
            first_chunk = context_chunks[0]
            snippet = first_chunk[:200] + "..." if len(first_chunk) > 200 else first_chunk
            answer += f"{snippet}\n\n"
            
            # Add citation
            answer += "[Source: Document 1]"
            
        else:  # teaching mode
            # Teaching mode: more expansive, add explanations
            answer = f"From your notes: "
            
            # Include context
            first_chunk = context_chunks[0]
            snippet = first_chunk[:200] + "..." if len(first_chunk) > 200 else first_chunk
            answer += f"{snippet}\n\n"
            
            # Add teaching explanation
            answer += "To help understand: This concept is important because it forms a foundation for further learning. "
            answer += f"The key points to remember are: {', '.join(relevant_terms[:3])}."
        
        return answer
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from question (simple implementation)."""
        # Remove common words
        stop_words = {"what", "is", "the", "how", "why", "when", "where", "can", "you", "a", "an", "and", "or", "but"}
        words = text.split()
        key_terms = [w for w in words if w not in stop_words and len(w) > 3]
        return key_terms
    
    def _build_prompt(self, question: str, context: str, mode: str) -> str:
        """Build prompt for token estimation."""
        if mode == "strict":
            template = f"""You are an AI tutor. Answer using ONLY the provided context.

Context:
{context}

Question: {question}

Answer:"""
        else:  # teaching
            template = f"""You are an AI tutor. Answer primarily using the context, but add explanations.

Context:
{context}

Question: {question}

Answer:"""
        
        return template
    
    def reset_call_count(self):
        """Reset call counter (useful for testing)."""
        self.call_count = 0


class GroqLLMClient(LLMClient):
    """
    Real Groq LLM client.
    
    Requires GROQ_API_KEY environment variable.
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        """
        Initialize Groq LLM client.
        
        Args:
            model: Groq model identifier
            api_key: Groq API key (if not provided, reads from GROQ_API_KEY env var)
            
        Raises:
            ValueError: If no API key is provided or found in environment
        """
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("groq package is required. Install with: pip install groq")
        
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "No Groq API key provided. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.call_count = 0
        
        logger.info(f"GroqLLMClient initialized with model={model}")
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate text using Groq API.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            
        Returns:
            GenerationResult with generated text and metadata
            
        Raises:
            RuntimeError: If API call fails
        """
        self.call_count += 1
        cfg = config or GenerationConfig()
        
        try:
            logger.debug(f"Groq API call #{self.call_count}", extra={"prompt_length": len(prompt)})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                top_p=cfg.top_p,
                frequency_penalty=cfg.frequency_penalty,
                presence_penalty=cfg.presence_penalty,
                stop=cfg.stop_sequences,
            )
            
            text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            logger.info(
                f"Groq generation #{self.call_count} complete",
                extra={
                    "model": self.model,
                    "finish_reason": finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            )
            
            return GenerationResult(
                text=text,
                model=self.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=finish_reason,
                metadata={"call_count": self.call_count}
            )
            
        except Exception as e:
            logger.error(f"Groq API call failed: {e}", exc_info=True)
            raise RuntimeError(f"Groq generation failed: {str(e)}") from e
    
    def generate_with_context(
        self,
        question: str,
        context_chunks: List[str],
        mode: Literal["strict", "teaching"] = "strict",
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate answer using retrieved context via Groq.
        
        Args:
            question: User's question
            context_chunks: Retrieved text chunks for context
            mode: Generation mode (strict or teaching)
            config: Generation configuration
            
        Returns:
            GenerationResult with answer
        """
        self.call_count += 1
        
        # Build context text
        context_text = "\n\n".join(context_chunks)
        
        # Build prompt based on mode
        prompt = self._build_prompt(question, context_text, mode)
        
        # Generate using Groq
        try:
            logger.debug(
                f"Groq contextual generation #{self.call_count}",
                extra={
                    "question_length": len(question),
                    "context_chunks": len(context_chunks),
                    "mode": mode,
                }
            )
            
            cfg = config or GenerationConfig()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                top_p=cfg.top_p,
                frequency_penalty=cfg.frequency_penalty,
                presence_penalty=cfg.presence_penalty,
                stop=cfg.stop_sequences,
            )
            
            text = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            logger.info(
                f"Groq contextual generation #{self.call_count} complete",
                extra={
                    "model": self.model,
                    "mode": mode,
                    "finish_reason": finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            )
            
            return GenerationResult(
                text=text,
                model=self.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                finish_reason=finish_reason,
                metadata={
                    "call_count": self.call_count,
                    "mode": mode,
                    "context_chunks_count": len(context_chunks),
                }
            )
            
        except Exception as e:
            logger.error(f"Groq contextual generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Groq generation failed: {str(e)}") from e
    
    def _build_prompt(self, question: str, context: str, mode: str) -> str:
        """Build prompt for Groq API."""
        if mode == "strict":
            template = f"""You are an AI tutor. Answer the question using ONLY the provided context from the student's notes.

Context from notes:
{context}

Question: {question}

Critical Rules:
1. ONLY use information explicitly stated in the context above
2. Cite sources using [Document Name] format
3. If the context doesn't contain enough information, respond: "I don't have enough information in your notes to answer this question."
4. Do NOT add external knowledge or examples not in the context
5. Be precise and accurate

Answer:"""
        else:  # teaching mode
            template = f"""You are an AI tutor. Answer the question primarily using the provided context, but you may add clarifying explanations and examples to help understanding.

Context from student's notes:
{context}

Question: {question}

Guidelines:
1. Use the context as the PRIMARY source - cite as [Document Name]
2. You may add clarifying explanations and examples
3. Clearly distinguish: 
   - "From your notes: ..." (grounded content)
   - "To help understand: ..." (additional explanation)
4. If notes don't cover the question, state that clearly first
5. Be pedagogical - break down complex concepts

Answer:"""
        
        return template
    
    def reset_call_count(self):
        """Reset call counter (useful for testing)."""
        self.call_count = 0


# Singleton instance
_llm_client_instance: Optional[LLMClient] = None


def get_llm_client(provider: str = "mock", **kwargs) -> LLMClient:
    """
    Get LLM client instance (singleton).
    
    Args:
        provider: LLM provider - "mock" or "groq" (default: "mock")
        **kwargs: Configuration parameters for client
        
    Returns:
        LLMClient instance
        
    Examples:
        # Mock client (default)
        client = get_llm_client()
        
        # Groq client (requires GROQ_API_KEY env var)
        client = get_llm_client(provider="groq")
        
        # Groq with explicit API key
        client = get_llm_client(provider="groq", api_key="your-key")
    """
    global _llm_client_instance
    
    # Check if we need to create or recreate the client
    needs_creation = _llm_client_instance is None
    
    # Check if provider changed (recreate singleton if different provider requested)
    if _llm_client_instance is not None:
        current_provider = "mock" if isinstance(_llm_client_instance, MockLLMClient) else "groq"
        if current_provider != provider:
            logger.info(f"LLM provider changed from {current_provider} to {provider}, recreating client")
            _llm_client_instance = None
            needs_creation = True
    
    if needs_creation:
        if provider == "mock":
            logger.info("Creating global MockLLMClient instance")
            _llm_client_instance = MockLLMClient(**kwargs)
        elif provider == "groq":
            logger.info("Creating global GroqLLMClient instance")
            _llm_client_instance = GroqLLMClient(**kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Use 'mock' or 'groq'.")
    
    return _llm_client_instance


def reset_llm_client():
    """Reset singleton instance (useful for testing)."""
    global _llm_client_instance
    _llm_client_instance = None
