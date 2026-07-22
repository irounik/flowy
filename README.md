# Flowy

Python monorepo for AI-powered workflows and information retrieval.

## Structure

```text
flowy/
├── apps/
│   └── retrieval-api/   # FastAPI + Cognee RAG (PDF ingest & query)
├── packages/            # Shared libraries (reserved)
├── data/uploads/        # Local PDF uploads (gitignored)
├── Makefile
└── pyproject.toml       # uv workspace root
```

## Prerequisites

- Python 3.11–3.13
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key (default Cognee LLM/embeddings provider)

## Quick start (retrieval API)

```bash
cp .env.example .env
# set LLM_API_KEY in .env

make install
make dev
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

See [apps/retrieval-api/README.md](apps/retrieval-api/README.md) for PDF upload and query examples.

## License

MIT. Direct dependencies are MIT or Apache-2.0 (Cognee is Apache-2.0).
