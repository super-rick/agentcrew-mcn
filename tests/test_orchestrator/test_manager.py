from __future__ import annotations
import pytest
"""Tests for the orchestrator."""

from unittest.mock import MagicMock

from orchestrator.manager import Orchestrator, PipelineResult
from agents.base import Task
from agents.writer import WriterAgent
from agents.publisher import PublisherAgent


class TestOrchestrator:
    """Test suite for Orchestrator."""

    def test_initialization(self):
        orch = Orchestrator()
        assert len(orch.agents) == 0
        assert len(orch.task_history) == 0

    def test_register_agent(self, mock_llm_client):
        orch = Orchestrator()
        writer = WriterAgent(mock_llm_client)
        orch.register_agent(writer)
        assert "writer" in orch.agents

    def test_get_agent(self, mock_llm_client):
        orch = Orchestrator()
        writer = WriterAgent(mock_llm_client)
        orch.register_agent(writer)
        assert orch.get_agent("writer") == writer

    def test_get_agent_not_found(self):
        orch = Orchestrator()
        with pytest.raises(KeyError):
            orch.get_agent("nonexistent")

    def test_create_task(self):
        orch = Orchestrator()
        task = orch.create_task("write", {"topic": "Test"})
        assert task.task_type == "write"
        assert task.params["topic"] == "Test"
        assert task.status == "pending"
        assert len(task.task_id) == 8  # UUID first 8 chars

    def test_create_task_default_params(self):
        orch = Orchestrator()
        task = orch.create_task("publish")
        assert task.params == {}

    def test_pipeline_result_to_dict(self):
        result = PipelineResult(
            success=True,
            pipeline_id="test_123",
            task_type="write",
            duration_seconds=1.5,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["pipeline_id"] == "test_123"
        assert d["task_type"] == "write"
        assert d["duration_seconds"] == 1.5

    def test_repr(self, mock_llm_client):
        orch = Orchestrator()
        assert "agents=[]" in repr(orch)
        writer = WriterAgent(mock_llm_client)
        orch.register_agent(writer)
        assert "writer" in repr(orch)
