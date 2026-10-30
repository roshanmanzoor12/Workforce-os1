from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, status

from app.config import settings
from app.modules.health.schemas import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.modules.health.service import (
    get_health,
    get_readiness,
)


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


# =========================================================
# LIVENESS
# =========================================================

@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Application liveness",
)
async def liveness() -> LivenessResponse:
    """
    Lightweight liveness endpoint.

    This endpoint only proves that the FastAPI process is running.

    It does NOT check:
    - PostgreSQL
    - Redis
    - MinIO / S3
    - tenant databases
    - external integrations

    Intended for:
    - Docker liveness checks
    - Kubernetes liveness probes
    - reverse proxy checks
    """

    return LivenessResponse(
        status="alive",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
    )


# =========================================================
# READINESS
# =========================================================

@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Application readiness",
)
async def readiness(
    request: Request,
    response: Response,
) -> ReadinessResponse:
    """
    Check whether WorkforceOS is ready to serve requests.

    Required infrastructure:
    - control PostgreSQL database
    - Redis
    - MinIO / S3

    HTTP status:
        200 -> ready
        503 -> not ready
    """

    result = await get_readiness()

    if not result.ready:
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    request.app.state.ready = result.ready

    return result


# =========================================================
# FULL HEALTH
# =========================================================

@router.get(
    "",
    response_model=HealthResponse,
    summary="Detailed application health",
)
async def health(
    response: Response,
) -> HealthResponse:
    """
    Return detailed WorkforceOS infrastructure health.

    Includes:
    - overall status
    - environment
    - application version
    - process uptime
    - database health
    - Redis health
    - object-storage health
    - latency for each dependency

    HTTP behavior:
        healthy  -> 200
        degraded -> 200
        unhealthy -> 503

    A degraded system may still be partially operational,
    therefore degraded does not automatically return 503.
    """

    result = await get_health()

    if result.status == "unhealthy":
        response.status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return result