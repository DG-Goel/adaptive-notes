"""
Configuration management for Universal AI Tutor.

Uses Pydantic Settings for environment variable validation and type safety.
All configuration loaded from .env file or environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    debug: bool = Field(default=True, description="Enable debug mode")

    # Qdrant Vector Database
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")
    qdrant_collection_name: str = Field(default="tutor_knowledge")

    # Groq API
    groq_api_key: str = Field(
        default="", description="Groq API key (get from https://console.groq.com)"
    )
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    groq_max_retries: int = Field(default=3, ge=1, le=10)
    groq_timeout_seconds: int = Field(default=30, ge=5, le=120)
    
    # LLM Provider
    llm_provider: Literal["mock", "groq"] = Field(
        default="mock", 
        description="LLM provider: 'mock' for testing, 'groq' for real API"
    )

    # Embedding Model
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_device: Literal["cpu", "cuda"] = Field(default="cpu")
    embedding_batch_size: int = Field(default=32, ge=1, le=128)
    embedding_max_length: int = Field(default=512, ge=128, le=512)

    # Reranker Model
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker_device: Literal["cpu", "cuda"] = Field(default="cpu")
    reranker_batch_size: int = Field(default=16, ge=1, le=64)

    # Retrieval Configuration
    dense_top_k: int = Field(default=20, ge=1, le=100)
    bm25_top_k: int = Field(default=20, ge=1, le=100)
    rrf_k: int = Field(default=60, ge=1, le=100)
    rerank_top_k: int = Field(default=5, ge=1, le=20)

    # Generation Configuration
    generation_temperature_strict: float = Field(default=0.3, ge=0.0, le=2.0)
    generation_temperature_teaching: float = Field(default=0.5, ge=0.0, le=2.0)
    generation_max_tokens: int = Field(default=800, ge=100, le=2000)
    generation_top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    generation_frequency_penalty: float = Field(default=0.3, ge=0.0, le=2.0)

    # Chunking Configuration
    parent_chunk_size: int = Field(default=1200, ge=400, le=2048)
    parent_chunk_overlap: int = Field(default=100, ge=0, le=200)
    child_chunk_size: int = Field(default=400, ge=200, le=800)
    child_chunk_overlap: int = Field(default=50, ge=0, le=100)
    child_chunk_min: int = Field(default=256, ge=100, le=400)
    child_chunk_max: int = Field(default=480, ge=400, le=512)

    # Performance
    embedding_cache_size: int = Field(default=10000, ge=100, le=100000)
    conversation_cache_size: int = Field(default=1000, ge=10, le=10000)
    conversation_ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    # API Configuration
    api_host: str = Field(default="127.0.0.1", description="API host (use 127.0.0.1 for localhost only)")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_reload: bool = Field(default=True)
    api_workers: int = Field(default=1, ge=1, le=16)
    
    # Security Configuration
    allowed_notes_dir: str = Field(default="./notes", description="Directory containing notes (restricts file access)")
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="Maximum file size in MB")
    max_question_length: int = Field(default=2000, ge=100, le=10000, description="Maximum question length in characters")

    @field_validator("child_chunk_max")
    @classmethod
    def validate_chunk_max_within_embedding_limit(cls, v: int, info) -> int:
        """Ensure child_chunk_max doesn't exceed embedding model limit."""
        embedding_max = info.data.get("embedding_max_length", 512)
        if v >= embedding_max:
            raise ValueError(
                f"child_chunk_max ({v}) must be less than embedding_max_length ({embedding_max})"
            )
        return v

    @field_validator("child_chunk_size")
    @classmethod
    def validate_chunk_size_range(cls, v: int, info) -> int:
        """Ensure child_chunk_size is between min and max."""
        chunk_min = info.data.get("child_chunk_min", 256)
        chunk_max = info.data.get("child_chunk_max", 480)
        if not (chunk_min <= v <= chunk_max):
            raise ValueError(
                f"child_chunk_size ({v}) must be between "
                f"child_chunk_min ({chunk_min}) and child_chunk_max ({chunk_max})"
            )
        return v

    def get_generation_temperature(self, mode: Literal["strict", "teaching"]) -> float:
        """Get temperature for given tutoring mode."""
        if mode == "strict":
            return self.generation_temperature_strict
        return self.generation_temperature_teaching


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded once and cached for the application lifetime.
    Use this function instead of creating Settings() directly.

    Returns:
        Settings: Validated application settings

    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    return Settings()  # type: ignore[call-arg]
