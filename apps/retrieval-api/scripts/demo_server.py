#!/usr/bin/env python3
"""Run the retrieval API with a demo Cognee backend for reliable video recording."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
os.environ.setdefault("LLM_API_KEY", "demo-key")

import uvicorn
from fastapi import FastAPI

# Ensure app package is importable when launched from repo root.
APP_DIR = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(APP_DIR))

from app.deps import get_cognee_service
from app.main import app
from app.schemas import SearchTypeOption


class DemoCogneeService:
    """Deterministic Cognee stand-in so the demo works without a live LLM key."""

    async def ingest_pdf(self, file_path: Path, dataset_name: str) -> dict[str, Any]:
        return {
            "status": "ok",
            "path": str(file_path),
            "dataset_name": dataset_name,
            "message": "Indexed sample-report.pdf into Cognee memory",
        }

    async def query(
        self,
        query_text: str,
        *,
        dataset_name: str,
        search_type: SearchTypeOption = SearchTypeOption.RAG_COMPLETION,
    ) -> list[dict[str, Any]]:
        return [
            {
                "text": (
                    "According to the uploaded report, revenue grew 42% year over year. "
                    "The main risk is supply-chain delays in Q3, with a recommended action "
                    "to diversify suppliers by September."
                ),
                "dataset_name": dataset_name,
                "search_type": search_type.value,
                "query": query_text,
            }
        ]

    async def forget_all(self) -> dict[str, Any]:
        return {"cleared": True}


app.dependency_overrides[get_cognee_service] = lambda: DemoCogneeService()


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
