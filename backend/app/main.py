"""FastAPI application entry point for the IdeaLens backend.

Run locally from the ``backend`` directory:

    .venv\\Scripts\\python -m uvicorn app.main:app --reload

The application boots without PostgreSQL or Redis running; both are reported
honestly as ``unavailable`` by /health until they are reachable. Research runs
are queued (Redis) or executed in-process when Redis is unavailable.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.research_runs import router as research_router
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)




def create_app() -> FastAPI:
    """Application factory; kept separate so tests can build isolated instances."""
    configure_logging()
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "IdeaLens backend — evidence-driven technical intelligence API. "
            "Asynchronous research runs with per-stage checkpointing, source "
            "adapters (Semantic Scholar, Crossref, arXiv, GitHub), and guardrailed "
            "reports. Scope-aware signals only — no novelty guarantees."
        ),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):  # pragma: no cover
        """Attach a request id for traceability across logs/responses."""
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    application.include_router(health_router)
    application.include_router(research_router)
    application.include_router(documents_router)
    return application


app = create_app()
