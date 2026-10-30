from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.database import (
    ControlSessionLocal,
    dispose_control_database,
    test_control_database_connection,
)
from app.core.exceptions import (
    DatabaseError,
    RedisError,
    StorageError,
)
from app.core.logging import (
    configure_logging,
    get_logger,
)
from app.core.redis import (
    close_redis,
    test_redis_connection,
)
from app.core.storage import (
    ensure_bucket,
    test_storage_connection,
)
from app.db.tenant import dispose_all_tenant_engines
from app.modules.chat.chat_redis import close_chat_redis
from app.modules.chat.realtime_runtime import (
    start_chat_realtime_runtime,
    stop_chat_realtime_runtime,
)
from app.modules.realtime_bridge.runtime import (
    runtime as realtime_bridge_runtime,
)
from app.modules.tenant_api.provider import (
    register_tenant_session_resolver,
    tenant_session_resolver_registered,
)
from app.modules.tenant_api.resolver import resolve_tenant_session


logger = get_logger(__name__)


# =========================================================
# STARTUP HELPERS
# =========================================================


async def startup_database() -> None:
    """Verify the control PostgreSQL database is reachable."""
    logger.info(
        "startup_database_check_started"
    )

    try:
        await test_control_database_connection()

        logger.info(
            "startup_database_check_passed"
        )

    except DatabaseError:
        logger.exception(
            "startup_database_check_failed"
        )
        raise


async def startup_redis() -> None:
    """Verify the core Redis connection."""
    logger.info(
        "startup_redis_check_started"
    )

    try:
        await test_redis_connection()

        logger.info(
            "startup_redis_check_passed"
        )

    except RedisError:
        logger.exception(
            "startup_redis_check_failed"
        )
        raise


async def startup_storage() -> None:
    """Verify object storage and ensure the application bucket exists."""
    logger.info(
        "startup_storage_check_started"
    )

    try:
        test_storage_connection()

        bucket = ensure_bucket()

        logger.info(
            "startup_storage_check_passed",
            bucket=bucket,
        )

    except StorageError:
        logger.exception(
            "startup_storage_check_failed"
        )
        raise


def startup_tenant_routing() -> None:
    """Register the authorized tenant-session resolver."""
    logger.info(
        "startup_tenant_routing_started"
    )

    register_tenant_session_resolver(
        resolve_tenant_session
    )

    if not tenant_session_resolver_registered():
        raise RuntimeError(
            "Tenant session resolver registration failed."
        )

    logger.info(
        "startup_tenant_routing_passed"
    )


async def startup_realtime() -> None:
    """Start the call publisher transport and personal chat subscriber."""
    logger.info(
        "startup_realtime_started"
    )

    try:
        await realtime_bridge_runtime.start()

        await start_chat_realtime_runtime(
            session_factory=ControlSessionLocal,
        )

    except Exception:
        logger.exception(
            "startup_realtime_failed"
        )
        raise

    logger.info(
        "startup_realtime_worker_started"
    )


# =========================================================
# APPLICATION STARTUP
# =========================================================


async def startup_services() -> None:
    """Start infrastructure and the personal realtime worker."""
    logger.info(
        "workforceos_startup_started",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )

    await startup_database()
    await startup_redis()
    await startup_storage()

    startup_tenant_routing()

    await startup_realtime()

    logger.info(
        "workforceos_startup_complete",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


# =========================================================
# APPLICATION SHUTDOWN
# =========================================================


async def shutdown_services() -> None:
    """Stop workers before releasing Redis and database resources."""
    logger.info(
        "workforceos_shutdown_started"
    )

    try:
        await stop_chat_realtime_runtime()

    except Exception as exc:
        logger.warning(
            "chat_realtime_shutdown_error",
            error=str(exc),
        )

    try:
        await realtime_bridge_runtime.stop()

    except Exception as exc:
        logger.warning(
            "realtime_bridge_shutdown_error",
            error=str(exc),
        )

    try:
        await close_chat_redis()

    except Exception as exc:
        logger.warning(
            "chat_redis_shutdown_error",
            error=str(exc),
        )

    try:
        await dispose_all_tenant_engines()

    except Exception as exc:
        logger.warning(
            "tenant_database_shutdown_error",
            error=str(exc),
        )

    try:
        await close_redis()

    except Exception as exc:
        logger.warning(
            "redis_shutdown_error",
            error=str(exc),
        )

    try:
        await dispose_control_database()

    except Exception as exc:
        logger.warning(
            "database_shutdown_error",
            error=str(exc),
        )

    logger.info(
        "workforceos_shutdown_complete"
    )


# =========================================================
# FASTAPI LIFESPAN
# =========================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start services and clean up even when startup fails."""
    configure_logging()

    app.state.ready = False

    logger.info(
        "application_lifespan_starting"
    )

    try:
        try:
            await startup_services()

        except Exception:
            logger.exception(
                "application_startup_failed"
            )
            raise

        app.state.ready = True

        yield

    finally:
        app.state.ready = False

        await shutdown_services()

        logger.info(
            "application_lifespan_stopped"
        )