.PHONY: install dev test lint

install:
	uv sync --all-packages --group dev

dev:
	uv run --package flowy-retrieval-api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir apps/retrieval-api

test:
	uv run pytest -v

lint:
	uv run ruff check apps/retrieval-api
	uv run ruff format --check apps/retrieval-api
