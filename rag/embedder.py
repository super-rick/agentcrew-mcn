"""
RAG Embedding — text-to-vector conversion interface.

使用 DeepSeek API 做 Embedding（Week 1 方案）。
BGE 本地模型（Week 2 可选方案预留接口）。
"""

from abc import ABC, abstractmethod

from openai import OpenAI


class BaseEmbedder(ABC):
    """Abstract embedding interface."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of texts to vectors."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Convert a single query text to a vector."""


class DeepSeekEmbedder(BaseEmbedder):
    """Embedding via DeepSeek API (OpenAI-compatible).

    NOTE: DeepSeek does NOT currently offer an embedding model.
    This embedder uses a fallback/hallucinated model name and WILL fail with 404.
    For production, switch to OpenAI text-embedding-3-small or local BGE model.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        # WARNING: DeepSeek has no embedding API. Use alternative provider.
        self._model = "deepseek-embedding"

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]
