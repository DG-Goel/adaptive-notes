"""
Summarization module for Adaptive Notes Pipeline.

Provides intelligent summarization of document chunks using local Ollama models.
"""

from app.summarization.ollama_provider import OllamaSummarizer
from app.summarization.models import SummarizationResult, ChunkSummary

__all__ = ["OllamaSummarizer", "SummarizationResult", "ChunkSummary"]
