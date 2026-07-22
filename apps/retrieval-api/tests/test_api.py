from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.deps import get_cognee_service
from app.main import app
from app.schemas import SearchTypeOption


class FakeCogneeService:
    def __init__(self) -> None:
        self.ingest_pdf = AsyncMock(return_value={"ok": True})
        self.query = AsyncMock(return_value=[{"text": "sample answer"}])
        self.forget_all = AsyncMock(return_value={"cleared": True})


@pytest.fixture
def fake_cognee() -> FakeCogneeService:
    return FakeCogneeService()


@pytest.fixture
def client(fake_cognee: FakeCogneeService):
    app.dependency_overrides[get_cognee_service] = lambda: fake_cognee
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "flowy-retrieval-api"


def test_upload_pdf_success(client: TestClient, fake_cognee: FakeCogneeService) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("report.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        data={"dataset_name": "docs"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "report.pdf"
    assert body["dataset_name"] == "docs"
    assert body["status"] == "ingested"
    fake_cognee.ingest_pdf.assert_awaited_once()
    args, kwargs = fake_cognee.ingest_pdf.await_args
    assert args[1] == "docs"
    assert Path(args[0]).name.endswith("_report.pdf")


def test_upload_rejects_non_pdf(client: TestClient, fake_cognee: FakeCogneeService) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    fake_cognee.ingest_pdf.assert_not_awaited()


def test_query_success(client: TestClient, fake_cognee: FakeCogneeService) -> None:
    response = client.post(
        "/api/v1/query",
        json={
            "query": "What is in the document?",
            "dataset_name": "docs",
            "search_type": "RAG_COMPLETION",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "What is in the document?"
    assert body["dataset_name"] == "docs"
    assert body["search_type"] == SearchTypeOption.RAG_COMPLETION.value
    assert body["results"] == [{"text": "sample answer"}]
    fake_cognee.query.assert_awaited_once()


def test_query_requires_text(client: TestClient) -> None:
    response = client.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 422


def test_reset_memory(client: TestClient, fake_cognee: FakeCogneeService) -> None:
    response = client.delete("/api/v1/memory")
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"
    fake_cognee.forget_all.assert_awaited_once()


def test_query_cognee_error(client: TestClient, fake_cognee: FakeCogneeService) -> None:
    fake_cognee.query = AsyncMock(side_effect=RuntimeError("boom"))
    response = client.post("/api/v1/query", json={"query": "hello"})
    assert response.status_code == 500
    assert "Cognee query failed" in response.json()["detail"]
