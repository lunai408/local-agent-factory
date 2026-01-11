"""
Centralized model provider configuration for Agno agents.

Usage:
    from utils.models import get_llm_model, get_embedder

    # Get model using environment configuration
    model = get_llm_model()

    # Get model with override (for specific agents needing different sizes)
    model = get_llm_model(model_id="gpt-4-turbo")

    # Get embedder
    embedder = get_embedder()

Environment Variables:
    MODEL_PROVIDER: "openai" (default) or "local"
    OPENAI_MODEL_ID: OpenAI model ID (default: gpt-4)
    OLLAMA_BASE_URL: Ollama server URL (default: http://127.0.0.1:11434)
    OLLAMA_INFER_MODEL: Ollama LLM model (default: ministral-3:3b)
    OLLAMA_EMBED_MODEL: Ollama embedding model (default: nomic-embed-text)
    OLLAMA_EMBED_DIMENSIONS: Embedding dimensions (default: 768)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Union

from dotenv import load_dotenv

load_dotenv()


class ModelProvider(str, Enum):
    """Supported model providers."""

    OPENAI = "openai"
    LOCAL = "local"


def _normalize_ollama_host(host: str) -> str:
    """Ensure Ollama host has http:// prefix."""
    if not host.startswith(("http://", "https://")):
        return f"http://{host}"
    return host


@dataclass
class ModelConfig:
    """Model provider configuration with environment-based defaults."""

    # Provider selection
    provider: ModelProvider = field(
        default_factory=lambda: ModelProvider(
            os.getenv("MODEL_PROVIDER", "openai").lower()
        )
    )

    # OpenAI configuration
    openai_model_id: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL_ID", "gpt-4")
    )

    # Local (Ollama) configuration
    # Prefer OLLAMA_BASE_URL (docker-compose)
    ollama_host: str = field(
        default_factory=lambda: _normalize_ollama_host(
            os.getenv("OLLAMA_BASE_URL", "127.0.0.1:11434")
        )
    )
    ollama_model_id: str = field(
        default_factory=lambda: os.getenv("OLLAMA_INFER_MODEL", "ministral-3:3b")
    )
    ollama_embed_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    )
    ollama_embed_dimensions: int = field(
        default_factory=lambda: int(os.getenv("OLLAMA_EMBED_DIMENSIONS", "768"))
    )

    @property
    def is_local(self) -> bool:
        """Check if using local provider."""
        return self.provider == ModelProvider.LOCAL

    @property
    def default_model_id(self) -> str:
        """Get the default model ID for the current provider."""
        if self.is_local:
            return self.ollama_model_id
        return self.openai_model_id


# Lazy imports to avoid loading both providers at startup
def _get_openai_chat():
    from agno.models.openai import OpenAIChat

    return OpenAIChat


def _get_ollama():
    from agno.models.ollama import Ollama

    return Ollama


def _get_openai_embedder():
    from agno.knowledge.embedder.openai import OpenAIEmbedder

    return OpenAIEmbedder


def _get_ollama_embedder():
    from agno.knowledge.embedder.ollama import OllamaEmbedder

    return OllamaEmbedder


# Type aliases
LLMModel = Union["OpenAIChat", "Ollama"]  # type: ignore
Embedder = Union["OpenAIEmbedder", "OllamaEmbedder"]  # type: ignore

# Module-level config instance (created once, reused)
_config: ModelConfig | None = None


def get_model_config() -> ModelConfig:
    """Get the model configuration singleton."""
    global _config
    if _config is None:
        _config = ModelConfig()
    return _config


def get_llm_model(model_id: str | None = None) -> LLMModel:
    """
    Get an LLM model instance based on the configured provider.

    Args:
        model_id: Optional model ID override. If not provided, uses the
                  default model for the current provider.

    Returns:
        Configured model instance (OpenAIChat or Ollama)

    Examples:
        # Use default model from environment
        model = get_llm_model()

        # Override with specific model
        model = get_llm_model(model_id="gpt-4-turbo")

        # For local, override with different Ollama model
        model = get_llm_model(model_id="llama3.1:8b")
    """
    config = get_model_config()

    if config.is_local:
        Ollama = _get_ollama()
        return Ollama(
            id=model_id or config.ollama_model_id,
            host=config.ollama_host,
        )
    else:
        OpenAIChat = _get_openai_chat()
        return OpenAIChat(
            id=model_id or config.openai_model_id,
        )


def get_embedder() -> Embedder:
    """
    Get an embedder instance based on the configured provider.

    Returns:
        Configured embedder instance (OpenAIEmbedder or OllamaEmbedder)

    Examples:
        embedder = get_embedder()
        vector_db = SurrealVDb(embedder=embedder, ...)
    """
    config = get_model_config()

    if config.is_local:
        OllamaEmbedder = _get_ollama_embedder()
        return OllamaEmbedder(
            id=config.ollama_embed_model,
            dimensions=config.ollama_embed_dimensions,
            host=config.ollama_host,
        )
    else:
        OpenAIEmbedder = _get_openai_embedder()
        return OpenAIEmbedder()


def reset_config() -> None:
    """Reset the configuration singleton (useful for testing)."""
    global _config
    _config = None
