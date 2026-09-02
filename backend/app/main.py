"""FastAPI application entry point for the IdeaLens backend.

Run locally from the ``backend`` directory:

    .venv\\Scripts\\python -m uvicorn app.main:app --reload

The application boots without PostgreSQL or Redis running; both are reported
honestly as ``unavailable`` by /health until they are reachable.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Application factory; kept separate so tests can build isolated instances."""
    configure_logging()
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "IdeaLens backend — M1 engineering foundation. "
            "Research analysis functionality is not implemented yet."
        ),
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    return application


app = create_app()