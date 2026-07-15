from __future__ import annotations
"""
Analyst Agent — AI 数据分析员工。

负责：
1. 效果分析（analyze）— 聚合发布历史数据，统计各平台表现
2. 报告生成（report）— 调用 LLM 生成可读的效果报告
3. 策略建议（recommend）— 基于数据生成内容策略优化建议

核心流程：
    execute(task) →
      根据 task_type:
        "analyze"   → _collect_data → _calculate_stats → 返回 AnalysisResult
        "report"    → analyze 数据 → LLM → 生成报告文本
        "recommend" → analyze 数据 → LLM → 生成策略建议
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from agents.base import BaseAgent, Task, TaskResult
from llm.client import LLMClient


class AnalystAgent(BaseAgent):
    """Content performance analysis agent — the AI data analyst employee."""

    name = "analyst"
    description = "负责内容效果数据分析、报告生成和策略优化建议"

    def __init__(
        self,
        llm_client: LLMClient,
        config: dict | None = None,
        publisher_agent: BaseAgent | None = None,
    ):
        super().__init__(llm_client, config)
        self.publisher_agent = publisher_agent

    def get_system_prompt(self) -> str:
        return (
            "你是一个专业的内容运营数据分析师。"
            "你通过分析各平台发布数据，识别内容表现趋势和优化机会。"
            "你的分析结论应当数据驱动、可执行、有具体行动建议。"
            "你使用中文输出，语言简洁专业。"
        )

    # ── Public API ──────────────────────────────────────────

    def execute(self, task: Task) -> TaskResult:
        """Execute an analyst task.

        Task params:
            task_type (str): analyze | report | recommend
            days (int): 分析最近多少天的数据，默认 7
            platforms (list[str], optional): 指定平台过滤
        """
        started_at = datetime.now()
        task_type = task.task_type
        days = task.params.get("days", 7)
        platforms = task.params.get("platforms")

        try:
            # Step 1: Collect and aggregate data
            history = self._get_post_history()
            filtered = self._filter_by_days(history, days)
            if platforms:
                filtered = [r for r in filtered if r.get("platform") in platforms]

            analysis = self._calculate_metrics(filtered, days)

            if task_type == "analyze":
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    data={
                        "analysis_type": "analyze",
                        "period_days": days,
                        **analysis,
                    },
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    agent_name=self.name,
                )

            elif task_type == "report":
                report_text = self._generate_report(analysis)
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    data={
                        "analysis_type": "report",
                        "period_days": days,
                        "report": report_text,
                        **analysis,
                    },
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    agent_name=self.name,
                )

            elif task_type == "recommend":
                recommend_text = self._generate_recommendations(analysis)
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    data={
                        "analysis_type": "recommend",
                        "period_days": days,
                        "recommendations": recommend_text,
                        **analysis,
                    },
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    agent_name=self.name,
                )

            else:
                raise ValueError(f"Unknown task_type for analyst: {task_type}")

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                agent_name=self.name,
            )

    # ── Data Collection ─────────────────────────────────────

    def _get_post_history(self) -> list[dict]:
        """Retrieve post history from publisher agent or fallback file."""
        if self.publisher_agent and hasattr(self.publisher_agent, "get_post_history"):
            return self.publisher_agent.get_post_history(limit=500)
        return []

    @staticmethod
    def _filter_by_days(records: list[dict], days: int) -> list[dict]:
        """Keep only records from the last N days."""
        if not records:
            return []
        cutoff = datetime.now() - timedelta(days=days)
        result = []
        for r in records:
            posted_str = r.get("posted_at")
            if not posted_str:
                continue
            try:
                posted_dt = datetime.fromisoformat(posted_str)
                if posted_dt >= cutoff:
                    result.append(r)
            except (ValueError, TypeError):
                continue
        return result

    # ── Metrics Calculation ─────────────────────────────────

    def _calculate_metrics(self, records: list[dict], days: int) -> dict[str, Any]:
        """Aggregate post records into structured metrics.

        Returns dict with:
            total_posts, success_count, fail_count, success_rate
            platform_stats: [{platform, total, success, fail, rate}, ...]
            daily_counts: [{date, total, success, fail}, ...]
            recent_fails: [failed records, ...]
        """
        total = len(records)
        success = sum(1 for r in records if r.get("success"))
        failed = total - success
        success_rate = (success / total * 100) if total else 0.0

        # Per-platform stats
        platform_buckets: dict[str, dict] = defaultdict(
            lambda: {"total": 0, "success": 0, "fail": 0}
        )
        for r in records:
            plat = r.get("platform", "unknown")
            platform_buckets[plat]["total"] += 1
            if r.get("success"):
                platform_buckets[plat]["success"] += 1
            else:
                platform_buckets[plat]["fail"] += 1

        platform_stats = []
        for plat, pb in sorted(platform_buckets.items()):
            p_rate = (pb["success"] / pb["total"] * 100) if pb["total"] else 0.0
            platform_stats.append({
                "platform": plat,
                "total": pb["total"],
                "success": pb["success"],
                "fail": pb["fail"],
                "success_rate": round(p_rate, 1),
            })

        # Daily counts (last `days` days, fill gaps with zero)
        now = datetime.now()
        daily_map: dict[str, dict] = defaultdict(
            lambda: {"total": 0, "success": 0, "fail": 0}
        )
        for r in records:
            posted_str = r.get("posted_at")
            if not posted_str:
                continue
            try:
                d = datetime.fromisoformat(posted_str).strftime("%Y-%m-%d")
                daily_map[d]["total"] += 1
                if r.get("success"):
                    daily_map[d]["success"] += 1
                else:
                    daily_map[d]["fail"] += 1
            except (ValueError, TypeError):
                continue

        daily_counts = []
        for i in range(days - 1, -1, -1):
            day_label = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            d = daily_map.get(day_label, {"total": 0, "success": 0, "fail": 0})
            daily_counts.append({
                "date": day_label,
                "total": d["total"],
                "success": d["success"],
                "fail": d["fail"],
            })

        # Recent failures (up to 5)
        recent_fails = [
            {
                "platform": r.get("platform"),
                "error": r.get("error_message"),
                "posted_at": r.get("posted_at"),
            }
            for r in records
            if not r.get("success")
        ][-5:]

        # Count errors by type for common failures
        error_counts: dict[str, int] = defaultdict(int)
        for r in records:
            if not r.get("success") and r.get("error_message"):
                err = r["error_message"]
                key = err.split(":")[0].strip() if ":" in err else err[:80]
                error_counts[key] += 1

        return {
            "total_posts": total,
            "success_count": success,
            "fail_count": failed,
            "success_rate": round(success_rate, 1),
            "platform_stats": platform_stats,
            "daily_counts": daily_counts,
            "recent_fails": recent_fails,
            "error_summary": dict(
                sorted(error_counts.items(), key=lambda x: -x[1])
            ),
        }

    # ── LLM-powered generation ──────────────────────────────

    def _generate_report(self, metrics: dict[str, Any]) -> str:
        """Generate a human-readable performance report via LLM."""
        prompt = self._build_report_prompt(metrics)
        messages = self._build_messages(prompt)
        return self.llm_client.chat(messages)

    def _generate_recommendations(self, metrics: dict[str, Any]) -> str:
        """Generate strategy optimisation recommendations via LLM."""
        prompt = self._build_recommend_prompt(metrics)
        messages = self._build_messages(prompt)
        return self.llm_client.chat(messages)

    # ── Prompt Builders ─────────────────────────────────────

    def _build_report_prompt(self, metrics: dict) -> str:
        """Build the LLM prompt for report generation."""
        plat_rows = "\n".join(
            f"  - {p['platform']}: 共发布 {p['total']} 篇, "
            f"成功 {p['success']} 篇, 失败 {p['fail']} 篇, "
            f"成功率 {p['success_rate']}%"
            for p in (metrics.get("platform_stats") or [])
        )

        daily_rows = "\n".join(
            f"  - {d['date']}: 发布 {d['total']} 篇 "
            f"(成功 {d['success']}, 失败 {d['fail']})"
            for d in (metrics.get("daily_counts") or [])
        )

        fail_rows = "\n".join(
            f"  - [{f.get('platform', '?')}] {f.get('error', '未知错误')}"
            for f in (metrics.get("recent_fails") or [])
        )

        return (
            "请根据以下发布数据生成一份内容运营周报。\n\n"
            f"## 总览\n"
            f"- 统计周期: 过去 {metrics.get('period_days', '?')} 天\n"
            f"- 发布总数: {metrics['total_posts']} 篇\n"
            f"- 成功: {metrics['success_count']} 篇 ({metrics['success_rate']}%)\n"
            f"- 失败: {metrics['fail_count']} 篇\n\n"
            f"## 各平台表现\n{plat_rows if plat_rows else '  (无数据)'}\n\n"
            f"## 每日发布\n{daily_rows if daily_rows else '  (无数据)'}\n\n"
            f"## 近期失败\n{fail_rows if fail_rows else '  (无失败记录)'}\n\n"
            "请生成周报，包含：\n"
            "1. 核心发现（3-5 条关键结论）\n"
            "2. 各平台表现评价\n"
            "3. 失败原因分析与改进建议\n"
            "4. 下一步行动计划\n\n"
            "格式：Markdown，标题层级分明，数据引用准确。"
        )

    def _build_recommend_prompt(self, metrics: dict) -> str:
        """Build the LLM prompt for strategy recommendations."""
        plat_rows = "\n".join(
            f"  - {p['platform']}: {p['total']} 篇, "
            f"成功率 {p['success_rate']}%"
            for p in (metrics.get("platform_stats") or [])
        )

        return (
            "你是一个内容运营策略顾问。请根据以下发布数据给出优化建议。\n\n"
            f"## 当前数据\n"
            f"- 统计周期: 过去 {metrics.get('period_days', '?')} 天\n"
            f"- 发布总数: {metrics['total_posts']} 篇\n"
            f"- 成功率: {metrics['success_rate']}%\n\n"
            f"## 各平台\n{plat_rows if plat_rows else '  (无数据)'}\n\n"
            "请从以下维度给出具体可执行的策略建议：\n"
            "1. 平台策略 — 哪些平台应加大/减少投入\n"
            "2. 发布频率 — 建议的节奏\n"
            "3. 内容方向 — 什么内容类型效果更好\n"
            "4. 发布时机 — 最佳发布时间建议\n"
            "5. 技术改进 — 降低发布失败率的措施\n\n"
            "建议应数据驱动、具体可执行，给出优先级排序。"
        )
