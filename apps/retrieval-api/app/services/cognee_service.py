from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

# Local single-user mode for in-process Cognee usage.
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

import cognee
from cognee import SearchType

from app.schemas import SearchTypeOption

logger = logging.getLogger(__name__)

_SEARCH_TYPE_MAP = {
    SearchTypeOption.RAG_COMPLETION: SearchType.RAG_COMPLETION,
    SearchTypeOption.GRAPH_COMPLETION: SearchType.GRAPH_COMPLETION,
    SearchTypeOption.CHUNKS: SearchType.CHUNKS,
    SearchTypeOption.SUMMARIES: SearchType.SUMMARIES,
    SearchTypeOption.FEELING_LUCKY: SearchType.FEELING_LUCKY,
}


def _normalize_result(item: Any) -> Any:
    if item is None:
        return None
    if isinstance(item, (str, int, float, bool)):
        return item
    if isinstance(item, dict):
        return {key: _normalize_result(value) for key, value in item.items()}
    if isinstance(item, (list, tuple)):
        return [_normalize_result(value) for value in item]
    text = getattr(item, "text", None)
    if isinstance(text, str):
        payload: dict[str, Any] = {"text": text}
        for attr in ("dataset_id", "dataset_name", "search_result"):
            value = getattr(item, attr, None)
            if value is not None:
                payload[attr] = _normalize_result(value)
        return payload
    if hasattr(item, "model_dump"):
        try:
            return item.model_dump()
        except Exception:  # noqa: BLE001
            pass
    return str(item)


class CogneeService:
    """Thin wrapper around Cognee remember / recall / forget."""

    async def ingest_pdf(self, file_path: Path, dataset_name: str) -> Any:
        absolute = str(file_path.resolve())
        logger.info("ingesting PDF into Cognee", extra={"path": absolute, "dataset": dataset_name})
        result = await cognee.remember(absolute, dataset_name=dataset_name)
        return _normalize_result(result)

    async def query(
        self,
        query_text: str,
        *,
        dataset_name: str,
        search_type: SearchTypeOption = SearchTypeOption.RAG_COMPLETION,
    ) -> list[Any]:
        cognee_type = _SEARCH_TYPE_MAP[search_type]
        logger.info(
            "querying Cognee",
            extra={"dataset": dataset_name, "search_type": search_type.value},
        )
        try:
            results = await cognee.recall(
                query_text=query_text,
                query_type=cognee_type,
                datasets=[dataset_name],
            )
        except TypeError:
            # Older Cognee signatures may not accept datasets on recall.
            results = await cognee.search(
                query_text,
                query_type=cognee_type,
                datasets=[dataset_name],
            )

        if results is None:
            return []
        if not isinstance(results, list):
            return [_normalize_result(results)]
        return [_normalize_result(item) for item in results]

    async def forget_all(self) -> Any:
        logger.warning("clearing all Cognee memory")
        result = await cognee.forget(everything=True)
        return _normalize_result(result)
