from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


HealthStatus = Literal[
    "healthy",
    "degraded",
    "unhealthy",
]


class ServiceHealth(BaseModel):
    """
    Health status for one infrastructure dependency.
    """

    name: str

    status: HealthStatus

    message: str | None = None

    latency_ms: float | None = Field(
        default=None,
        ge=0,
    )


class LivenessResponse(BaseModel):
    """
    Simple process liveness response.

    This endpoint should NOT depend on PostgreSQL,
    Redis, MinIO, or other external services.
    """

    status: Literal["alive"]

    app: str

    version: str

    environment: str

    timestamp: datetime


class ReadinessResponse(BaseModel):
    """
    Application readiness response.

    Ready only when required infrastructure is available.
    """

    status: HealthStatus

    ready: bool

    app: str

    version: str

    environment: str

    timestamp: datetime

    services: list[ServiceHealth]


class HealthResponse(BaseModel):
    """
    Detailed platform health response.

    Intended for:
    - platform admin
    - diagnostics
    - container health
    - infrastructure monitoring
    """

    status: HealthStatus

    app: str

    version: str

    environment: str

    timestamp: datetime

    uptime_seconds: float = Field(
        ge=0,
    )

    services: list[ServiceHealth]