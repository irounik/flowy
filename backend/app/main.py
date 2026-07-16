import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.database.session import async_session_factory
from app.adk.runtime import WORKFLOW_REGISTRY
from app.services import WorkflowService

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


async def seed_workflows() -> None:
    """Register built-in workflows on startup."""
    try:
        async with async_session_factory() as session:
            service = WorkflowService(session)
            descriptions = {
                "invoice-approval": "Extract, summarize, approve, and email invoice processing workflow",
                "research": "Webhook-triggered research with search, LLM summary, and Slack notification",
            }
            for name in WORKFLOW_REGISTRY:
                existing = await service.get_by_name(name)
                if not existing:
                    await service.register(name, descriptions.get(name), "0.1.0")
                    logger.info("registered workflow", extra={"workflow": name})
    except Exception as exc:
        logger.warning("workflow seed skipped: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_workflows()
    yield


app = FastAPI(
    title="Flowy",
    description="Async agentic workflow platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}
