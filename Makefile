.PHONY: install test lint fmt clean run-write run-publish run-schedule

install:
	pip install -r requirements.txt

test:
	pytest -v

lint:
	ruff check agents/ platforms/ orchestrator/ rag/ llm/ cli/
	black --check agents/ platforms/ orchestrator/ rag/ llm/ cli/

fmt:
	ruff check --fix agents/ platforms/ orchestrator/ rag/ llm/ cli/
	black agents/ platforms/ orchestrator/ rag/ llm/ cli/

run-write:
	python -m cli.main write generate --topic "AI Agent 架构设计" --style technical

run-publish:
	python -m cli.main publish post --content "测试" --platform juejin --dry-run

run-schedule:
	python -m cli.main schedule start --topic-file topics.txt --platform juejin --interval 6

clean:
	rm -rf data/chroma/*
	rm -rf data/logs/*.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
