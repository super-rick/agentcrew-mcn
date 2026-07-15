from __future__ import annotations
"""Tests for the Analyst Agent."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from agents.analyst import AnalystAgent
from agents.base import Task


def _make_post_record(
    platform: str = "juejin",
    success: bool = True,
    error_message: str | None = None,
    days_ago: int = 1,
    post_id: str | None = "post_001",
) -> dict:
    """Helper to build a sample post history record."""
    posted_at = (datetime.now() - timedelta(days=days_ago)).isoformat()
    return {
        "success": success,
        "platform": platform,
        "post_id": post_id,
        "post_url": f"https://{platform}.example.com/{post_id}" if post_id else None,
        "error_message": error_message,
        "posted_at": posted_at,
        "metrics": {},
    }


def _mock_publisher(records: list[dict] | None = None) -> MagicMock:
    """Create a mock publisher agent that returns given post history."""
    publisher = MagicMock()
    publisher.get_post_history.return_value = records or []
    return publisher


class TestAnalystAgent:
    """Test suite for AnalystAgent."""

    def test_initialization(self, mock_llm_client):
        """Agent should initialize with correct name and description."""
        agent = AnalystAgent(mock_llm_client)
        assert agent.name == "analyst"
        assert agent.description is not None

    def test_initialization_with_publisher(self, mock_llm_client):
        """Agent should accept a publisher agent reference."""
        publisher = _mock_publisher()
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)
        assert agent.publisher_agent is publisher

    def test_get_system_prompt(self, mock_llm_client):
        """System prompt should describe the analyst role."""
        agent = AnalystAgent(mock_llm_client)
        prompt = agent.get_system_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "数据分析" in prompt or "分析师" in prompt

    def test_execute_analyze_empty_history(self, mock_llm_client):
        """Analyze with no history should return zero counts."""
        publisher = _mock_publisher([])
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_001",
            task_type="analyze",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert result.success
        assert result.data["total_posts"] == 0
        assert result.data["success_count"] == 0
        assert result.data["fail_count"] == 0
        assert result.data["platform_stats"] == []

    def test_execute_analyze_with_data(self, mock_llm_client):
        """Analyze should aggregate post history correctly."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
            _make_post_record("juejin", True, days_ago=2),
            _make_post_record("zhihu", True, days_ago=3),
            _make_post_record("zhihu", False, "Auth failed", days_ago=1),
        ]
        publisher = _mock_publisher(records)
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_002",
            task_type="analyze",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert result.success
        assert result.data["total_posts"] == 4
        assert result.data["success_count"] == 3
        assert result.data["fail_count"] == 1
        assert result.data["success_rate"] == 75.0

        # Platform stats
        stats = {s["platform"]: s for s in result.data["platform_stats"]}
        assert stats["juejin"]["total"] == 2
        assert stats["juejin"]["success"] == 2
        assert stats["juejin"]["success_rate"] == 100.0
        assert stats["zhihu"]["total"] == 2
        assert stats["zhihu"]["success"] == 1
        assert stats["zhihu"]["success_rate"] == 50.0

    def test_execute_analyze_respects_days_filter(self, mock_llm_client):
        """Analyze should only include records within the specified days."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
            _make_post_record("juejin", True, days_ago=10),  # outside 7-day window
        ]
        publisher = _mock_publisher(records)
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_003",
            task_type="analyze",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert result.data["total_posts"] == 1

    def test_execute_analyze_with_platform_filter(self, mock_llm_client):
        """Analyze should filter by platform when specified."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
            _make_post_record("zhihu", True, days_ago=1),
        ]
        publisher = _mock_publisher(records)
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_004",
            task_type="analyze",
            params={"days": 7, "platforms": ["juejin"]},
        )
        result = agent.execute(task)
        assert result.data["total_posts"] == 1
        assert result.data["platform_stats"][0]["platform"] == "juejin"

    def test_execute_report_calls_llm(self, mock_llm_client):
        """Report should invoke LLM and include report text in result."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
            _make_post_record("zhihu", False, "API Error", days_ago=2),
        ]
        publisher = _mock_publisher(records)
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_005",
            task_type="report",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert result.success

        # LLM should have been called
        mock_llm_client.chat.assert_called_once()
        # Result should include the mocked report text
        assert result.data["report"] is not None

    def test_execute_recommend_calls_llm(self, mock_llm_client):
        """Recommend should invoke LLM and include recommendation text."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
        ]
        publisher = _mock_publisher(records)
        agent = AnalystAgent(mock_llm_client, publisher_agent=publisher)

        task = Task(
            task_id="test_ana_006",
            task_type="recommend",
            params={"days": 14},
        )
        result = agent.execute(task)
        assert result.success
        assert result.data["recommendations"] is not None

    def test_execute_without_publisher(self, mock_llm_client):
        """Agent should handle missing publisher gracefully (no history)."""
        agent = AnalystAgent(mock_llm_client, publisher_agent=None)

        task = Task(
            task_id="test_ana_007",
            task_type="analyze",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert result.success
        assert result.data["total_posts"] == 0

    def test_execute_failure_reported(self):
        """If LLM client throws on report, the analyst should capture it."""
        failing_client = MagicMock()
        failing_client.chat.side_effect = Exception("API Error")

        agent = AnalystAgent(failing_client)
        task = Task(
            task_id="test_ana_fail",
            task_type="report",
            params={"days": 7},
        )
        result = agent.execute(task)
        assert not result.success
        assert "API Error" in (result.error_message or "")

    def test_unknown_task_type(self, mock_llm_client):
        """Unknown task type should return failure."""
        agent = AnalystAgent(mock_llm_client)
        task = Task(
            task_id="test_ana_unknown",
            task_type="unknown_type",
            params={},
        )
        result = agent.execute(task)
        assert not result.success
        assert "Unknown task_type" in (result.error_message or "")

    def test_calculate_metrics_daily_counts(self, mock_llm_client):
        """_calculate_metrics should produce correct daily breakdown."""
        records = [
            _make_post_record("juejin", True, days_ago=0),
            _make_post_record("juejin", True, days_ago=1),
        ]
        agent = AnalystAgent(mock_llm_client)
        metrics = agent._calculate_metrics(records, days=3)

        assert metrics["total_posts"] == 2
        assert len(metrics["daily_counts"]) == 3  # 3 days, zero-filled
        # At least one day should have posts
        assert any(d["total"] > 0 for d in metrics["daily_counts"])

    def test_filter_by_days(self, mock_llm_client):
        """_filter_by_days should only keep records within the window."""
        records = [
            _make_post_record("juejin", True, days_ago=1),
            _make_post_record("juejin", True, days_ago=30),
        ]
        filtered = AnalystAgent._filter_by_days(records, days=7)
        assert len(filtered) == 1

    def test_filter_by_days_empty(self, mock_llm_client):
        """_filter_by_days should handle empty input."""
        assert AnalystAgent._filter_by_days([], days=7) == []

    def test_error_summary(self, mock_llm_client):
        """Error summary should group similar errors."""
        records = [
            _make_post_record("zhihu", False, "Auth failed: token expired", days_ago=1),
            _make_post_record("zhihu", False, "Auth failed: invalid cookie", days_ago=2),
            _make_post_record("juejin", False, "Rate limit exceeded", days_ago=1),
        ]
        agent = AnalystAgent(mock_llm_client)
        metrics = agent._calculate_metrics(records, days=7)

        assert metrics["fail_count"] == 3
        assert "Auth failed" in metrics["error_summary"]
        assert metrics["error_summary"]["Auth failed"] == 2
        assert metrics["error_summary"]["Rate limit exceeded"] == 1
