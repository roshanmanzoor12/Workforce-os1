from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from app.config import settings
from app.core.database import check_control_database
from app.core.logging import get_logger
from app.core.redis import check_redis
from app.core.storage import check_storage
from app.modules.health.schemas import (
    HealthResponse,
    ReadinessResponse,
    ServiceHealth,
)


logger = get_logger(__name__)


# =========================================================
# PROCESS START TIME
# =========================================================

PROCESS_STARTED_AT = time.monotonic()


# =========================================================
# TIME HELPERS
# =========================================================

def utc_now() -> datetime:
    """
    Return current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


def get_uptime_seconds() -> float:
    """
    Return application process uptime in seconds.
    """

    return max(
        0.0,
        time.monotonic() - PROCESS_STARTED_AT,
    )


# =========================================================
# INDIVIDUAL SERVICE CHECKS
# =========================================================

async def check_database_health() -> ServiceHealth:
    """
    Check PostgreSQL control database health and measure latency.
    """

    started = time.perf_counter()

    try:
        healthy = await check_control_database()

        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        if healthy:
            return ServiceHealth(
                name="database",
                status="healthy",
                message="Control database is reachable.",
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

        return ServiceHealth(
            name="database",
            status="unhealthy",
            message="Control database is unavailable.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )

    except Exception as exc:
        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        logger.error(
            "health_database_check_failed",
            error=str(exc),
        )

        return ServiceHealth(
            name="database",
            status="unhealthy",
            message="Control database health check failed.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )


async def check_redis_health() -> ServiceHealth:
    """
    Check Redis health and measure latency.
    """

    started = time.perf_counter()

    try:
        healthy = await check_redis()

        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        if healthy:
            return ServiceHealth(
                name="redis",
                status="healthy",
                message="Redis is reachable.",
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

        return ServiceHealth(
            name="redis",
            status="unhealthy",
            message="Redis is unavailable.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )

    except Exception as exc:
        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        logger.error(
            "health_redis_check_failed",
            error=str(exc),
        )

        return ServiceHealth(
            name="redis",
            status="unhealthy",
            message="Redis health check failed.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )


async def check_storage_health() -> ServiceHealth:
    """
    Check S3/MinIO health.

    boto3 is synchronous, so run it in a worker thread so it
    does not block the FastAPI event loop.
    """

    started = time.perf_counter()

    try:
        healthy = await asyncio.to_thread(
            check_storage
        )

        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        if healthy:
            return ServiceHealth(
                name="storage",
                status="healthy",
                message="Object storage is reachable.",
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

        return ServiceHealth(
            name="storage",
            status="unhealthy",
            message="Object storage is unavailable.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )

    except Exception as exc:
        latency_ms = (
            time.perf_counter() - started
        ) * 1000

        logger.error(
            "health_storage_check_failed",
            error=str(exc),
        )

        return ServiceHealth(
            name="storage",
            status="unhealthy",
            message="Object storage health check failed.",
            latency_ms=round(
                latency_ms,
                2,
            ),
        )


# =========================================================
# CORE SERVICE HEALTH COLLECTION
# =========================================================

async def collect_service_health() -> list[ServiceHealth]:
    """
    Run all required infrastructure health checks concurrently.

    PostgreSQL
    Redis
    MinIO/S3
    """

    database_health, redis_health, storage_health = (
        await asyncio.gather(
            check_database_health(),
            check_redis_health(),
            check_storage_health(),
        )
    )

    return [
        database_health,
        redis_health,
        storage_health,
    ]


# =========================================================
# OVERALL STATUS
# =========================================================

def calculate_overall_status(
    services: list[ServiceHealth],
) -> str:
    """
    Determine application health from service results.

    Rules:

        all healthy
            -> healthy

        some healthy, some unhealthy
            -> degraded

        all unhealthy
            -> unhealthy
    """

    if not services:
        return "unhealthy"

    healthy_count = sum(
        service.status == "healthy"
        for service in services
    )

    if healthy_count == len(services):
        return "healthy"

    if healthy_count == 0:
        return "unhealthy"

    return "degraded"


# =========================================================
# READINESS
# =========================================================

async def get_readiness() -> ReadinessResponse:
    """
    Return application readiness.

    WorkforceOS is ready only when every required core service
    is healthy.
    """

    services = await collect_service_health()

    status = calculate_overall_status(
        services
    )

    ready = all(
        service.status == "healthy"
        for service in services
    )

    return ReadinessResponse(
        status=status,
        ready=ready,
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=utc_now(),
        services=services,
    )


# =========================================================
# FULL HEALTH
# =========================================================

async def get_health() -> HealthResponse:
    """
    Return detailed WorkforceOS health information.

    Includes:
    - overall health
    - environment
    - version
    - process uptime
    - PostgreSQL latency
    - Redis latency
    - object storage latency
    """

    services = await collect_service_health()

    status = calculate_overall_status(
        services
    )

    return HealthResponse(
        status=status,
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=utc_now(),
        uptime_seconds=round(
            get_uptime_seconds(),
            2,
        ),
        services=services,
    )