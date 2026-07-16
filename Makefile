.PHONY: dev db-up db-down migrate install test lint

install:
	cd backend && pip install -e ".[dev]"

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check app tests
