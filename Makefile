.PHONY: dev dev-frontend db-up db-down migrate install install-frontend build-frontend test lint

install:
	cd backend && pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

build-frontend:
	cd frontend && npm run build

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check app tests
