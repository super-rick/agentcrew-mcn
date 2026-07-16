"""
RAG Embedding — text-to-vector conversion interface.

OpenAI 兼容协议实现，通过 factory 函数支持多协议扩展。
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from openai import OpenAI


class BaseEmbedder(ABC):
    """Abstract embedding interface — implement for new protocols."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of texts to vectors."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Convert a single query text to a vector."""


class OpenAIEmbedder(BaseEmbedder):
    """Embedding via any OpenAI-compatible API.

    Works with:
    - OpenAI (api.openai.com) — text-embedding-3-small / text-embedding-ada-002
    - SiliconFlow (api.siliconflow.cn) — BAAI/bge-large-zh-v1.5
    - Any /v1/embeddings-compatible endpoint
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]


def create_embedder(embedding_config: dict) -> BaseEmbedder:
    """Factory: create an embedder from configuration.

    Args:
        embedding_config: dict with keys:
            - provider: "openai" (more protocols in the future)
            - model: model name string
            - api_key: API key (supports ${ENV_VAR} resolution)
            - base_url: API base URL

    Returns:
        An embedder instance matching the configured provider.

    Extensibility:
        Add new provider branches here. Each branch creates its own embedder
        class (implementing BaseEmbedder). The rest of the RAG pipeline is
        protocol-agnostic.
    """
    provider = embedding_config.get("provider", "openai")
    api_key = embedding_config.get("api_key", "")
    base_url = embedding_config.get("base_url", "https://api.openai.com/v1")
    model = embedding_config.get("model", "text-embedding-3-small")

    # Resolve ${ENV_VAR} placeholders
    api_key = _resolve_env(api_key)

    # Fallback: if no embedding-specific API key, try the LLM key
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    if provider == "openai":
        if not api_key:
            raise ValueError(
                "No embedding API key configured. "
                "Set EMBEDDING_API_KEY env var or configure rag.embedding.api_key in config.yaml"
            )
        return OpenAIEmbedder(api_key=api_key, base_url=base_url, model=model)

    # Future providers — add elif branches here:
    # elif provider == "local":
    #     from rag.embedder_local import LocalBgeEmbedder
    #     return LocalBgeEmbedder(model_name=model)
    # elif provider == "grpc":
    #     from rag.embedder_grpc import GrpcEmbedder
    #     return GrpcEmbedder(endpoint=embedding_config["endpoint"])

    raise ValueError(f"Unsupported embedding provider: {provider}")


def _resolve_env(value: str) -> str:
    """Resolve ${ENV_VAR} placeholders in a config value."""
    if not isinstance(value, str) or "${" not in value:
        return value
    import re

    def _replace(match):
        var_name = match.group(1)
        return os.environ.get(var_name, "")

    return re.sub(r"\$\{([^}]+)\}", _replace, value)
