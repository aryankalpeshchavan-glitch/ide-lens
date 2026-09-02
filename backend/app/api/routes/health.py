"""System endpoints: process health and best-effort dependency probes."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.db.checks import check_database_connection
from app.infrastructure.redis import check_redis_connection
from app.schemas.health import DependencyHealth, HealthResponse

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Process and dependency health",
)
def health() -> HealthResponse:
    """Return process health plus real dependency probes.

    ``status`` reflects process health only: the API process is alive and
    serving requests. Dependency statuses come from actual probes; a
    dependency that cannot be reached is reported as ``unavailable`` rather
    than pretending to be healthy.
    """
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        version=__version__,
        dependencies={
            "postgres": DependencyHealth(status=check_database_connection()),
            "redis": DependencyHealth(status=check_redis_connection()),
        },
    )