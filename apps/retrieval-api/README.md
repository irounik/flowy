# Retrieval API

FastAPI service that ingests PDFs into [Cognee](https://www.cognee.ai/) and answers questions with RAG completion.

## Setup

From the monorepo root:

```bash
cp .env.example .env
# set LLM_API_KEY=sk-...

make install
make dev
```

OpenAPI UI: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness |
| `POST` | `/api/v1/documents` | Upload a PDF into Cognee memory |
| `POST` | `/api/v1/query` | Ask a question (default `RAG_COMPLETION`) |
| `DELETE` | `/api/v1/memory` | Clear Cognee memory (local/dev) |

## Examples

### Upload a PDF

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -F "file=@./sample.pdf" \
  -F "dataset_name=main_dataset"
```

### Query with RAG

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key findings?",
    "dataset_name": "main_dataset",
    "search_type": "RAG_COMPLETION"
  }'
```

### Reset memory

```bash
curl -X DELETE "http://localhost:8000/api/v1/memory"
```

## Manual smoke test

1. Set `LLM_API_KEY` in `.env`.
2. Start the server with `make dev`.
3. Upload a text-based PDF via `/api/v1/documents`.
4. Query with `/api/v1/query` and confirm an answer is returned.

Scanned/image-only PDFs need OCR beyond the built-in PyPDF loader and are out of scope for this MVP.

## Demo recording

To record a local Swagger UI walkthrough without a live LLM key:

```bash
# terminal 1
uv run python apps/retrieval-api/scripts/demo_server.py

# terminal 2
uv run python apps/retrieval-api/scripts/record_demo.py
```

This writes `/opt/cursor/artifacts/flowy-retrieval-demo.mp4` (and screenshots).

## License

MIT. Cognee is Apache-2.0.
