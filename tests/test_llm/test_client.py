"""Tests for llm/client.py — multi-provider LLM client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from llm.client import LLMClient, LLMConfig, create_llm_client


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig(api_key="test-key")
        assert cfg.provider == "deepseek"
        assert cfg.model == "deepseek-chat"
        assert cfg.temperature == 0.8
        assert cfg.max_tokens == 4096
        assert cfg.base_url == "https://api.deepseek.com/v1"

    def test_custom_values(self):
        cfg = LLMConfig(
            provider="openai",
            api_key="k",
            base_url="https://custom.api/v1",
            model="custom-model",
            temperature=0.5,
            max_tokens=2048,
        )
        assert cfg.provider == "openai"
        assert cfg.model == "custom-model"
        assert cfg.temperature == 0.5
        assert cfg.max_tokens == 2048
        assert cfg.base_url == "https://custom.api/v1"

    def test_auto_derived_model(self):
        """When provider != deepseek and model is default, auto-derive."""
        cfg = LLMConfig(provider="openai", api_key="k")
        assert cfg.model == "gpt-4o"
        assert cfg.base_url == "https://api.openai.com/v1"

    def test_auto_derived_ollama(self):
        cfg = LLMConfig(provider="ollama")
        assert cfg.model == "llama3"
        assert cfg.base_url == "http://localhost:11434/v1"

    def test_anthropic_defaults(self):
        cfg = LLMConfig(provider="anthropic", api_key="sk-ant-xxx")
        assert cfg.model == "claude-sonnet-5"

    def test_deepseek_keeps_default_model(self):
        """DeepSeek default model stays."""
        cfg = LLMConfig(provider="deepseek", api_key="k")
        assert cfg.model == "deepseek-chat"


class TestCreateLLMClient:
    def test_creates_deepseek_client(self):
        with patch("openai.OpenAI"):
            client = create_llm_client("deepseek", api_key="sk-test")
            assert client._provider == "deepseek"

    def test_creates_openai_client(self):
        with patch("openai.OpenAI"):
            client = create_llm_client("openai", api_key="sk-test")
            assert client._provider == "openai"

    def test_creates_ollama_client(self):
        with patch("openai.OpenAI"):
            client = create_llm_client("ollama")
            assert client._provider == "ollama"


class TestLLMClientChat:
    """chat() — standard completion."""

    @patch("openai.OpenAI")
    def test_chat_returns_content(self, mock_openai):
        """chat() returns the message content string."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from LLM"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        result = client.chat([{"role": "user", "content": "hi"}])

        assert result == "Hello from LLM"

    @patch("openai.OpenAI")
    def test_chat_passes_parameters(self, mock_openai):
        """chat() forwards temperature, max_tokens, stop."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "ok"
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        client.chat(
            [{"role": "user", "content": "hi"}],
            temperature=0.2,
            max_tokens=100,
            stop=["END"],
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.2
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["stop"] == ["END"]

    @patch("openai.OpenAI")
    def test_chat_empty_content_returns_empty_string(self, mock_openai):
        """chat() handles None/empty content gracefully."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        result = client.chat([{"role": "user", "content": ""}])
        assert result == ""


class TestLLMClientChatWithTools:
    """chat_with_tools() — function calling."""

    @patch("openai.OpenAI")
    def test_returns_raw_response_dict(self, mock_openai):
        """chat_with_tools() returns the model_dump() of the message."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.model_dump.return_value = {"role": "assistant", "content": "using tools"}
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=mock_message),
        ]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        tools = [{"type": "function", "function": {"name": "search", "parameters": {}}}]
        result = client.chat_with_tools(
            [{"role": "user", "content": "search for X"}],
            tools=tools,
        )

        assert result == {"role": "assistant", "content": "using tools"}
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["tools"] == tools
        assert call_kwargs["tool_choice"] == "auto"

    @patch("openai.OpenAI")
    def test_custom_tool_choice(self, mock_openai):
        """tool_choice parameter is forwarded."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.model_dump.return_value = {"role": "assistant"}
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=mock_message),
        ]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        client.chat_with_tools(
            [{"role": "user", "content": "x"}],
            tools=[{"type": "function", "function": {"name": "f", "parameters": {}}}],
            tool_choice="required",
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == "required"


class TestLLMClientChatStream:
    """chat_stream() — streaming completion."""

    @patch("openai.OpenAI")
    def test_stream_yields_content_chunks(self, mock_openai):
        """chat_stream() yields content from each chunk."""
        mock_client = MagicMock()
        chunks = []
        for text in ["Hello", " ", "World"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            chunks.append(chunk)
        mock_client.chat.completions.create.return_value = chunks
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        result = list(client.chat_stream([{"role": "user", "content": "hi"}]))

        assert result == ["Hello", " ", "World"]

    @patch("openai.OpenAI")
    def test_stream_skips_none_content(self, mock_openai):
        """chat_stream() skips chunks with None content."""
        mock_client = MagicMock()
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = None
        mock_client.chat.completions.create.return_value = [chunk]
        mock_openai.return_value = mock_client

        client = LLMClient(LLMConfig(api_key="test"))
        result = list(client.chat_stream([{"role": "user", "content": "hi"}]))
        assert result == []
