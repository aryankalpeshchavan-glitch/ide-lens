"""Response schemas for system endpoints."""

from typing import Literal

from pydantic import BaseModel


class DependencyHealth(BaseModel):
    """Health state of a single dependency as probed at request time.

    ``ok``: dependency reachable. ``unavailable``: dependency could not be
    reached. ``not_checked``: dependency intentionally not probed (reserved;
    unused by the M1 probes).
    """

    status: Literal["ok", "unavailable", "not_checked"]


class HealthResponse(BaseModel):
    """GET /health response.

    ``status`` is process health only; it indicates the API process is alive.
    Dependency health is reported separately and is never inferred from the
    process state.
    """

    status: Literal["ok"]
    service: str
    environment: str
    version: str
    dependencies: dict[str, DependencyHealth]