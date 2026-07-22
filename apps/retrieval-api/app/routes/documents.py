import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import Settings, get_settings
from app.deps import get_cognee_service
from app.schemas import DocumentIngestResponse
from app.services.cognee_service import CogneeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["documents"])

_PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _validate_pdf(file: UploadFile) -> None:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported (.pdf extension required).",
        )
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in _PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {content_type}. Expected application/pdf.",
        )


def _safe_filename(filename: str) -> str:
    base = Path(filename).name
    cleaned = _SAFE_NAME.sub("_", base).strip("._")
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned or 'document'}.pdf"
    return cleaned


@router.post(
    "/documents",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to ingest"),
    dataset_name: str | None = Form(default=None),
    settings: Settings = Depends(get_settings),
    cognee_service: CogneeService = Depends(get_cognee_service),
) -> DocumentIngestResponse:
    _validate_pdf(file)
    dataset = (dataset_name or settings.default_dataset).strip() or settings.default_dataset

    upload_dir = settings.upload_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "document.pdf"
    stored_name = f"{uuid.uuid4().hex}_{_safe_filename(original_name)}"
    destination = upload_dir / stored_name

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        destination.write_bytes(content)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to save upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save upload: {exc}",
        ) from exc
    finally:
        await file.close()

    try:
        detail = await cognee_service.ingest_pdf(destination, dataset)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Cognee ingest failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cognee ingest failed: {exc}",
        ) from exc

    return DocumentIngestResponse(
        filename=original_name,
        dataset_name=dataset,
        status="ingested",
        detail=detail,
    )
