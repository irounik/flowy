# Flowy Backend

FastAPI backend for the async agentic workflow platform.

## Project Structure

```
app/
├── api/              # REST API route handlers
├── services/         # Business logic (workflow, execution, approval, events)
├── repositories/     # Data access layer
├── models/           # ORM model exports
├── schemas/          # Pydantic request/response models
├── database/         # SQLAlchemy engine, session, models
├── adk/
│   ├── workflows/    # ADK workflow definitions
│   ├── tools/        # Python and MCP tools
│   ├── prompts/      # System prompts
│   ├── agents/       # Agent definitions (future)
│   └── runtime.py    # ADK execution orchestrator
├── events/           # SSE event streaming
├── chat/             # Execution-aware chat
├── approvals/        # Approval helpers
└── main.py           # FastAPI application entry point
```

## Running Locally

See the root [README](../README.md) for setup instructions.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Environment Variables

See `.env.example` for all configuration options.
