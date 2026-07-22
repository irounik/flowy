from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SearchTypeOption(str, Enum):
    RAG_COMPLETION = "RAG_COMPLETION"
    GRAPH_COMPLETION = "GRAPH_COMPLETION"
    CHUNKS = "CHUNKS"
    SUMMARIES = "SUMMARIES"
    FEELING_LUCKY = "FEELING_LUCKY"


class DocumentIngestResponse(BaseModel):
    filename: str
    dataset_name: str
    status: str = "ingested"
    detail: Any | None = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language question")
    dataset_name: str | None = Field(
        default=None,
        description="Dataset to search; defaults to DEFAULT_DATASET",
    )
    search_type: SearchTypeOption = SearchTypeOption.RAG_COMPLETION


class QueryResponse(BaseModel):
    query: str
    dataset_name: str
    search_type: SearchTypeOption
    results: list[Any]


class MemoryResetResponse(BaseModel):
    status: str = "cleared"
    detail: Any | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
