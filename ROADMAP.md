# AgentCrew MCN 未来路线图 (Roadmap)

> 当前版本: **v0.2.1 (Beta)** | 最后更新: 2026-07-19

AgentCrew MCN 是一个多 Agent 架构的开源内容营销自动化工具。已完成核心闭环：Writer → Publisher → Analyst，支持掘金/知乎/Dev.to 三个平台，具备 RAG、MCP 协议、Streamlit Dashboard、定时调度等能力。203 个测试全部通过。

---

## 总览

```
v0.2.1 (当前)     v0.3 (可靠性)      v0.4 (智能)       v1.0 (平台化)     v2.0 (商业)
    │                  │                  │                  │                  │
    ├─ 3 Agents        ├─ 错误重试       ├─ 动态Skill编排  ├─ Web API        ├─ SaaS
    ├─ 3 Platforms     ├─ 持久化调度     ├─ 多模型Provider ├─ 用户系统       ├─ 付费计划
    ├─ RAG + MCP       ├─ 内容审核       ├─ 图片生成       ├─ 协作功能       ├─ 企业版
    └─ CLI+Dashboard   └─ CI/CD完善      └─ 智能排期       └─ 插件市场       └─ 白标
```

---

## Phase 1: v0.3 — Reliability & Hardening（可靠性加固）

> **目标**: 让现有功能稳定可靠，生产可用。优先级最高。

### 1.1 错误处理与重试机制
- 在 `BaseAgent` 和平台 `adapter.post()` 层加入指数退避重试（3 次）
- `TaskResult` 增加 `retry_count` 字段
- CLI 输出区分"重试中"和"最终失败"

### 1.2 持久化调度器
- 将调度任务持久化到 SQLite（`data/scheduler.db`）
- 新增 `schedule resume` 命令：重启后恢复未完成任务
- 支持 cron 表达式

### 1.3 内容安全审核 — Reviewer Agent
- 新增第 4 个 Agent：发布前自动审核内容
- 审核维度：敏感词、平台规范、内容质量评分
- Pipeline: Writer → Reviewer → Publisher

### 1.4 CI/CD 与工程完善
- `Dockerfile` + `docker-compose.yml`
- `.pre-commit-config.yaml`（ruff + black + mypy）
- GitHub Actions: Docker build + 集成测试

### 1.5 已知问题修复
- RAG 批量嵌入 OOM → 自动分批
- Dev.to API key 诊断增强
- CLI spinner + ChromaDB 超时兼容

---

## Phase 2: v0.4 — Intelligence Upgrade（智能升级）

> **目标**: 让 AI 员工更聪明，内容质量更高。

### 2.1 动态 Skill 编排（LLM-driven）
- Skill 增加 LLM 自主编排模式：根据描述选择 Tool 调用顺序
- 保持向后兼容：`workflow_type: "deterministic" | "llm_driven"`

### 2.2 多模型 Provider 支持
- 重构 `llm/` → 支持 DeepSeek / OpenAI / Anthropic / Ollama
- 为不同 Agent 指定不同模型

### 2.3 图片/多媒体生成
- `ImageGenerationTool` — DALL-E / Stability AI
- Writer Agent 生成封面图

### 2.4 智能排期
- Analyst Agent 分析最佳发布时间
- Scheduler 支持 `smart_schedule` 模式

### 2.5 跨平台内容改编
- 掘金：技术深度 + 代码示例
- 知乎：观点鲜明 + 故事化
- Dev.to：英文版生成

---

## Phase 3: v0.5 — Platform Expansion（平台扩展）

> **目标**: 覆盖更多平台，进入国际化。

### 新平台适配器

| 平台 | 优先级 | 认证方式 | 特点 |
|------|--------|----------|------|
| **CSDN** | 🔴 高 | Cookie / API | 国内最大开发者社区 |
| **微信公众平台** | 🔴 高 | API + AppID/Secret | 最大中文内容生态 |
| **SegmentFault (思否)** | 🟡 中 | Cookie | 技术问答+专栏 |
| **X (Twitter)** | 🟡 中 | OAuth 1.0a | 国际化必备 |
| **小红书** | 🟢 低 | App 模拟 | 高价值但难度大 |
| **Medium** | 🟢 低 | API key | 国际化博客 |

- 平台适配器插件化（`importlib.metadata` entry points）
- 社区贡献的第三方适配器 pip installable
- Dashboard 实时平台健康检查

---

## Phase 4: v1.0 — Platformization（平台化）

> **目标**: 从 CLI 工具升级为 Web 平台。

- **Web API** — FastAPI + WebSocket + JWT 认证
- **Dashboard 升级** — 内容日历、AI 对话页面、移动端适配
- **用户系统** — PostgreSQL + 多用户隔离 + RBAC
- **插件市场** — PyPI 标签 `agentcrew-skill` / `agentcrew-platform`
- **内容策略** — 日历视图、系列管理、话题库 UI

---

## Phase 5: v2.0 — Commercialization（商业化）

> **目标**: 可运营的 SaaS 产品。

- **SaaS 部署** — Kubernetes Helm Chart、多租户
- **付费计划** — Free / Pro (¥99/月) / Team (¥499/月) / Enterprise
- **高级分析** — ROI 分析、竞品监控、趋势预测、A/B 测试
- **Agent 协作** — Agent 间消息传递、每日站报推送到飞书/钉钉
- **企业特性** — SSO、审计日志、私有部署、白标

---

## 技术债务清理（贯穿所有阶段）

| 项目 | 阶段 | 说明 |
|------|------|------|
| 类型标注完善 | v0.3 | mypy strict mode |
| 测试覆盖率 > 80% | v0.3-v0.4 | 补齐边界用例 |
| 异步改造 | v0.4 | asyncio 全面替代同步 |
| 结构化日志 | v0.3 | structlog / JSON |
| 性能优化 | v1.0 | LLM 缓存、RAG 加速 |
| 安全审计 | v1.0 | Cookie 加密、Key 轮换 |

---

## 优先级矩阵

```
                    影响力
              低        中        高
          ┌─────────┬─────────┬─────────┐
    高    │         │ 新平台   │ 错误重试 │
实         │         │ 图片生成 │ 持久调度 │
施   ├─────────┼─────────┼─────────┤
难   中    │ CI/CD   │ 多模型   │ 内容审核 │
度         │ 已知Bug │ 智能排期 │ Web API  │
     ├─────────┼─────────┼─────────┤
    低    │ 代码清理 │ 跨平台适配│ 动态Skill│
          │         │         │          │
          └─────────┴─────────┴─────────┘
```

执行顺序: 左上 → 右上 → 中中 → 右下

---

## 下一个迭代：v0.3 任务清单

1. **Reviewer Agent** — 发布前内容审核（新 Agent）
2. **重试机制** — BaseAgent + PlatformAdapter 层指数退避
3. **持久化调度** — SQLite 存储 + `schedule resume` 命令
4. **Docker 部署** — Dockerfile + docker-compose.yml
5. **Pre-commit hooks** — ruff + black + mypy
6. **修复 test_base.py 警告** — TestAgent 去掉 `__init__`
7. **RAG 批量嵌入分批** — 自动 3-5 chunks/次
