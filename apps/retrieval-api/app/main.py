import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import REPO_ROOT, get_settings

load_dotenv(REPO_ROOT / ".env")
load_dotenv()

# Ensure Cognee runs in local single-user mode unless explicitly overridden.
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

from app.routes import documents, health, query  # noqa: E402

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    if not settings.llm_api_key:
        logger.warning(
            "LLM_API_KEY is not set; Cognee ingest/query will fail until it is configured"
        )
    yield


app = FastAPI(
    title="Flowy Retrieval API",
    description="PDF information retrieval powered by Cognee",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)
