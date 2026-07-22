import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.deps import get_cognee_service
from app.schemas import MemoryResetResponse, QueryRequest, QueryResponse
from app.services.cognee_service import CogneeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_memory(
    body: QueryRequest,
    settings: Settings = Depends(get_settings),
    cognee_service: CogneeService = Depends(get_cognee_service),
) -> QueryResponse:
    dataset = (body.dataset_name or settings.default_dataset).strip() or settings.default_dataset
    try:
        results = await cognee_service.query(
            body.query,
            dataset_name=dataset,
            search_type=body.search_type,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Cognee query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cognee query failed: {exc}",
        ) from exc

    return QueryResponse(
        query=body.query,
        dataset_name=dataset,
        search_type=body.search_type,
        results=results,
    )


@router.delete("/memory", response_model=MemoryResetResponse)
async def reset_memory(
    cognee_service: CogneeService = Depends(get_cognee_service),
) -> MemoryResetResponse:
    try:
        detail = await cognee_service.forget_all()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Cognee forget failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cognee forget failed: {exc}",
        ) from exc

    return MemoryResetResponse(status="cleared", detail=detail)
