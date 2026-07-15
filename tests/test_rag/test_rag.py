from __future__ import annotations
"""Tests for the RAG module."""

from unittest.mock import MagicMock, patch

from rag.embedder import DeepSeekEmbedder
from rag.knowledge_base import KnowledgeBase, Document
from rag.retriever import Retriever


class TestEmbedder:
    """Test suite for embedder."""

    def test_deepseek_embedder_needs_api_key(self):
        """DeepSeekEmbedder requires an API key."""
        embedder = DeepSeekEmbedder(api_key="test-key")
        assert embedder is not None
        assert embedder._model == "deepseek-embedding"


class TestKnowledgeBase:
    """Test suite for KnowledgeBase (with mocked ChromaDB)."""

    @patch("chromadb.PersistentClient")
    def test_initialization(self, mock_chroma):
        embedder = MagicMock()
        kb = KnowledgeBase(
            persist_dir="/tmp/test_chroma",
            embedder=embedder,
            collection_name="test_kb",
        )
        assert kb.collection_name == "test_kb"
        assert kb.persist_dir == "/tmp/test_chroma"
        mock_chroma.assert_called_once()

    @patch("chromadb.PersistentClient")
    def test_get_stats_empty(self, mock_chroma):
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

        embedder = MagicMock()
        kb = KnowledgeBase("/tmp/test", embedder, "test")
        stats = kb.get_stats()
        assert stats["document_count"] == 0
        assert stats["collection_name"] == "test"


class TestRetriever:
    """Test suite for Retriever."""

    def test_initialization(self):
        kb = MagicMock()
        retriever = Retriever(kb)
        assert retriever.kb == kb

    def test_format_context_empty(self):
        retriever = Retriever(MagicMock())
        result = retriever.format_context([])
        assert "未找到" in result

    def test_format_context_with_results(self):
        from rag.knowledge_base import SearchResult
        kb = MagicMock()
        retriever = Retriever(kb)

        results = [
            SearchResult(text="Test content here", score=0.95, metadata={"source": "blog"}),
        ]
        result = retriever.format_context(results)
        assert "Test content" in result
        assert "blog" in result
