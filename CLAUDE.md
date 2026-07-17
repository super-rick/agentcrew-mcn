# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AgentCrew MCN** — AI MCN 自动推广工具。多 Agent 架构的开源内容营销自动化工具，自动完成从内容生成到跨平台分发的全流程。

核心叙事：项目自己推广自己（Dogfooding / Meta 闭环）。

## Commands

```bash
# 安装依赖（需要代理时先 export HTTP_PROXY）
pip install -r requirements.txt

# 写作
python -m cli.main write generate --topic "主题" --style technical
python -m cli.main write generate --topic "主题" --platform juejin --rag

# 发布
python -m cli.main publish post --text "内容" --platform juejin --dry-run
python -m cli.main publish post --file article.md --platform juejin --platform zhihu
python -m cli.main publish status
python -m cli.main publish history

# 调度
python -m cli.main schedule start --topic-file topics.txt --platform juejin --interval 6
python -m cli.main schedule stop
python -m cli.main schedule status

# 知识库
python -m cli.main rag ingest --file article.md --source blog
python -m cli.main rag search --query "Python 异步编程"
python -m cli.main rag stats

# Dashboard
streamlit run dashboard/app.py

# 测试
python -m pytest tests/ -v
python -m pytest tests/test_agents/test_writer.py -v
python -m pytest tests/test_agents/ -v

# 代码格式化
make fmt
make lint
```

## Architecture

### 核心概念：AI 员工（Agent）

| Agent | 职责 | 已实现 |
|-------|------|--------|
| Writer Agent | 内容生成（调用 LLM + RAG + Skills） | ✅ v0.1 |
| Publisher Agent | 跨平台内容发布（注册多个适配器） | ✅ v0.1 |
| Analyst Agent | 效果分析、策略优化 | ✅ v0.2 |

每个 Agent 继承 `BaseAgent`（`agents/base.py`），拥有独立的 Tool 和 Skill 注册表。

### Skills + Tools 抽象层

```
Tool = 原子操作（web_search, fetch_url_content, get_current_time）
Skill = Tool 的有序编排（trending_writing, technical_article, thread_writing）
```

- **Tool** (`agents/tools.py`): `Tool` 类 + `ToolRegistry`，每个 Tool 可转为 OpenAI Function Calling 格式
- **Skill** (`agents/skills.py`): `Skill` 抽象类 + `SkillRegistry`，`execute(registry, params)` 编排多个 Tool
- Agent 初始化时自动注册 BUILTIN_TOOLS 和 BUILTIN_SKILLS

### Platform 适配器模式

```
BasePlatformAdapter (platforms/base.py)
├── JuejinAdapter (platforms/juejin.py) — Cookie 认证，API 发文章/沸点
├── ZhihuAdapter (platforms/zhihu.py) — Playwright 浏览器自动化
└── DevToAdapter (platforms/devto.py) — Forem API
```

每个适配器实现 `authenticate()` + `post(content: ContentPost) → PostResult`。

### 数据流

```
CLI → Orchestrator.execute_pipeline()
  ├── WriterAgent.execute() — RAG 检索 → Skill 编排 → LLM 生成 → 平台格式化
  │   ├── _enrich_context(topic)   # RAG 检索 + Web 搜索
  │   ├── _build_messages()        # 组装 system + context + user prompt
  │   └── format_for_platform()    # juejin / zhihu / devto 格式适配
  │
  └── PublisherAgent.execute() — 内容验证 → 各平台适配器 → 记录结果
```

### RAG 模块

```
rag/embedder.py     — DeepSeek Embedding API（Week 1）/ BGE 本地（Week 2 预留）
rag/knowledge_base.py — ChromaDB 封装（add_documents/search/get_stats）
rag/retriever.py    — 检索管道（retrieve_for_writing/format_context）
```

### 关键目录

```
agents/       Agent 实现 + Tool/Skill 系统
orchestrator/ 任务编排引擎 + 调度器（带随机抖动反检测）
platforms/    各平台适配器（可插拔）
rag/          RAG 知识库
llm/          LLM Client（OpenAI 兼容，对接 DeepSeek）
cli/          Click CLI 命令
dashboard/    Streamlit Web 面板（4 页面：总览/发布分析/AI 分析/系统状态）
data/         运行时数据（chroma 向量库 / 日志）
```

## Key Decisions

- **语言**: Python（AI 生态最佳）
- **LLM**: DeepSeek API（OpenAI 兼容格式）
- **向量库**: ChromaDB（本地轻量）
- **CLI**: Click + Rich
- **配置**: YAML with `${ENV_VAR}` 变量替换
- **Python 版本**: 3.10+（代码使用 `X | None` 联合类型语法；Python 3.9 需 `from __future__ import annotations`）
- **MCP**: 架构预留，v2 升级
- **开发顺序**: CLI 优先，Dashboard 最后

## Platform Delays

- **掘金**: Cookie 认证（`authenticate()` 时验证）。API 发文章需 title，沸点无需
- **知乎**: Playwright 浏览器自动化，Cookie 持久化，随机延迟反检测（需要在有 GUI 的环境首次配置 Cookie）
- **Dev.to**: Forem API，API key 认证

## Testing

- 单元测试用 `unittest.mock` 完全隔离 LLM 和网络调用
- `conftest.py` 提供 `mock_llm_client` 和 `mock_web_search`（autouse）fixtures
- 集成测试在 `tests/test_integration/`，测试 Orchestrator 编排完整 pipeline
- 平台适配器测试需 mock 外部 API

## 当前进度 / Current Progress

> **每次完成阶段性工作后更新此段。** 新 session 从这里开始，无需重新调查。

### 已完成

| 模块 | 状态 | 说明 |
|------|------|------|
| Writer Agent | ✅ v0.1 | 内容生成（LLM + RAG + Skills），7 个测试通过 |
| Publisher Agent | ✅ v0.1 | 跨平台发布（掘金 API + 知乎 Playwright），适配器模式可插拔 |
| Analyst Agent | ✅ v0.2 | 效果分析（读取 post_history.json，report/recommend/rank），21 个测试通过 |
| 掘金适配器 | ✅ | Cookie 认证，API 发文章/沸点 |
| 知乎适配器 | ✅ | Playwright 浏览器自动化，Cookie 持久化 |
| RAG 模块 | ✅ | DeepSeek Embedding + ChromaDB，6 个测试通过 |
| CLI 命令 | ✅ | write / publish / schedule / rag 四组命令 |
| 测试套件 | ✅ | 88 passed, 0 failed |
| Dashboard | ✅ v0.2 | Streamlit Web 面板：总览/发布分析/AI 分析/系统状态 4 页面 |

### 待开发

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 🌐 Dev.to 适配器 | ✅ 已完成 | Forem API，发文章，集成到 Publisher |
| 🔮 MCP 协议 | 🔮 v2 | 架构已预留 |

### 下一步行动计划（2026-07-16 制定）

> **三步走，按顺序执行：**

**Step 1: 🍽️ Dogfooding — 跑通真实全流程**
- 用 AgentCrew MCN 写一篇推广自己的技术文章
- `python3 -m cli.main write generate --topic "AI 自动内容营销工具 AgentCrew 实战" --platform juejin --rag`
- 先在掘金 dry-run，确认无误后正式发布
- 目的：验证 mock 测试覆盖不到的真实环境问题

**Step 2: 🌐 Dev.to 适配器** (已完成)
- Forem API 认证
- 实现 `DevToAdapter(BasePlatformAdapter)`
- 发文章 / Markdown 支持
- 集成到 Publisher Agent + CLI

**Step 3: 🔮 MCP 协议**
- 为 Agent 提供 MCP 工具接入能力
- 架构已预留，按 v2 计划升级
