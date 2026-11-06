from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# CONTROL DATABASE ENGINE
# =========================================================

control_engine: AsyncEngine = create_async_engine(
    settings.control_database_url,
    echo=settings.debug,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
    },
)


# =========================================================
# SESSION FACTORY
# =========================================================

ControlSessionLocal = async_sessionmaker(
    bind=control_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# =========================================================
# FASTAPI DATABASE DEPENDENCY
# =========================================================

async def get_control_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for control-plane database access.

    Example:

        async def route(
            db: AsyncSession = Depends(get_control_db),
        ):
            ...
    """

    async with ControlSessionLocal() as session:
        try:
            yield session

        except SQLAlchemyError as exc:
            await session.rollback()

            logger.exception(
                "control_database_session_error",
                error=str(exc),
            )

            raise DatabaseError(
                "A control database operation failed."
            ) from exc

        finally:
            await session.close()


# =========================================================
# TRANSACTION CONTEXT MANAGER
# =========================================================

@asynccontextmanager
async def control_transaction() -> AsyncIterator[AsyncSession]:
    """
    Creates an explicit transaction.

    Automatically:
    - commits on success
    - rolls back on error
    - closes session

    Example:

        async with control_transaction() as db:
            db.add(user)
    """

    async with ControlSessionLocal() as session:
        try:
            async with session.begin():
                yield session

        except SQLAlchemyError as exc:
            await session.rollback()

            logger.exception(
                "control_database_transaction_error",
                error=str(exc),
            )

            raise DatabaseError(
                "Control database transaction failed."
            ) from exc

        finally:
            await session.close()


# =========================================================
# HEALTH CHECK
# =========================================================

async def check_control_database() -> bool:
    """
    Tests the control database connection using SELECT 1.

    Returns:
        True  -> healthy
        False -> unavailable
    """

    try:
        async with ControlSessionLocal() as session:
            result = await session.execute(
                text("SELECT 1")
            )

            return result.scalar_one() == 1

    except Exception as exc:
        logger.error(
            "control_database_health_check_failed",
            error=str(exc),
        )

        return False


# =========================================================
# DATABASE VERSION
# =========================================================

async def get_database_version() -> str | None:
    """
    Returns PostgreSQL server version.
    Useful for system-health/admin screens.
    """

    try:
        async with ControlSessionLocal() as session:
            result = await session.execute(
                text("SELECT version()")
            )

            return result.scalar_one()

    except Exception as exc:
        logger.warning(
            "database_version_check_failed",
            error=str(exc),
        )

        return None


# =========================================================
# CONNECTION TEST
# =========================================================

async def test_control_database_connection() -> None:
    """
    Raises DatabaseError if PostgreSQL is unavailable.

    Intended for application startup/readiness checks.
    """

    healthy = await check_control_database()

    if not healthy:
        raise DatabaseError(
            "Unable to connect to the WorkforceOS control database."
        )


# =========================================================
# ENGINE SHUTDOWN
# =========================================================

async def dispose_control_database() -> None:
    """
    Cleanly disposes all control DB connection pools.
    Call during FastAPI shutdown.
    """

    await control_engine.dispose()

    logger.info(
        "control_database_engine_disposed"
    )
