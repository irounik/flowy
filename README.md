# Flowy

Async agentic workflow platform — monorepo for AI-powered workflows that run over minutes, hours, or days.

## Vision

Flowy is an async workflow execution platform for AI agents. Workflows can be triggered manually or by external events and support LLM reasoning, tool calls, MCP servers, human approvals, notifications, and conversational interaction.

**MVP scope:** Backend only. A dynamic workflow creator UI will be added in a future iteration.

## Monorepo Structure

```
flowy/
├── backend/          # FastAPI + Google ADK 2.0 workflow runtime
├── frontend/         # Placeholder for future workflow designer UI
├── docker-compose.yml
└── Makefile
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for PostgreSQL)
- Google API key (optional, for Gemini LLM nodes)

### 1. Start PostgreSQL

```bash
make db-up
```

### 2. Install backend dependencies

```bash
make install
```

### 3. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set GOOGLE_API_KEY if using LLM nodes
```

### 4. Run migrations

```bash
make migrate
```

### 5. Start the API server

```bash
make dev
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Built-in Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `invoice-approval` | Manual | Extract → Summarize → Human Approval → Email |
| `research` | Webhook | Search → LLM Summary → Slack Notification |

## API Overview

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows/{workflow}/run` | Start a workflow execution |
| POST | `/triggers/manual` | Manual trigger with input payload |
| POST | `/webhooks/{workflow}` | Webhook trigger |
| GET | `/executions` | List executions (filter by status, workflow) |
| GET | `/executions/{id}` | Get execution details with history |
| POST | `/approvals/{id}` | Approve a pending request |
| POST | `/approvals/{id}/reject` | Reject a pending request |
| POST | `/chat/{executionId}` | Chat about a running execution |
| GET | `/executions/{id}/events` | SSE event stream |

## Example: Invoice Approval

```bash
# Start workflow
curl -X POST http://localhost:8000/api/v1/workflows/invoice-approval/run \
  -H "Content-Type: application/json" \
  -d '{"invoice_text": "Invoice from Acme Corp for $1250 due Aug 1"}'

# Check execution status
curl http://localhost:8000/api/v1/executions/{executionId}

# Approve when waiting
curl -X POST http://localhost:8000/api/v1/approvals/{approvalId} \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve"}'

# Chat about progress
curl -X POST http://localhost:8000/api/v1/chat/{executionId} \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current status?"}'
```

## Architecture

```
FastAPI APIs
    ↓
Workflow / Execution / Approval / Chat / Event Services
    ↓
Google ADK 2.0 Runtime
    ↓
Gemini · Python Tools · MCP Tools
    ↓
PostgreSQL
```

Workflow execution runs asynchronously via FastAPI background tasks. This can be swapped for Celery, Pub/Sub, or Cloud Run Jobs without changing the public API.

## Development

```bash
make test    # Run tests
make lint    # Run ruff linter
```

## License

Apache 2.0
