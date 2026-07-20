# Contributing to AgentCrew MCN

Thanks for contributing! AgentCrew is an open-source multi-agent content marketing automation tool.

## Development Setup

```bash
git clone https://github.com/super-rick/agentcrew-mcn.git
cd agentcrew-mcn
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m cli.main init
pytest tests/ -v
```

## Architecture

- **Agent** — AI employee with Tool + Skill registries
- **Tool** — Atomic operation (web_search, get_current_time, etc.)
- **Skill** — Tool pipeline (trending_writing, technical_article, etc.)
- **Platform Adapter** — `authenticate()` + `post()` per platform
- **Orchestrator** — Task dispatch + scheduler

## What to Contribute

### Platform Adapters

```python
from platforms.base import BasePlatformAdapter, ContentPost, PostResult

class MyAdapter(BasePlatformAdapter):
    platform_name = "myplatform"
    def authenticate(self) -> bool: ...
    def post(self, content: ContentPost) -> PostResult: ...
```

See `platforms/devto.py` (API) or `platforms/csdn.py` (Cookie) for examples.

### Skills

```python
class MySkill(Skill):
    name = "my_skill"
    description = "What this skill does"
    def execute(self, registry, params) -> SkillResult: ...
```

### Bug Fixes

Check [Issues](https://github.com/super-rick/agentcrew-mcn/issues).

## PR Workflow

1. Fork → create branch: `git checkout -b feat/my-feature`
2. Write code + tests: `pytest tests/ -q`
3. Format: `make lint`
4. Commit: `git commit -m "feat: short description"`
5. Push → create PR

## Code Style

- Python 3.10+, type annotations (`from __future__ import annotations`)
- Format: black, Lint: ruff (line width: 100)
- Tests use `unittest.mock`, no real API keys needed

## Questions?

- Bugs → [Issues](https://github.com/super-rick/agentcrew-mcn/issues)
- Ideas → [Discussions](https://github.com/super-rick/agentcrew-mcn/discussions)
- Docs → [super-rick.github.io/agentcrew-mcn](https://super-rick.github.io/agentcrew-mcn/)
