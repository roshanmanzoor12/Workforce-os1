from __future__ import annotations

import re
from contextlib import asynccontextmanager
from threading import RLock
from typing import AsyncIterator

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings


# =========================================================
# TENANT DATABASE SECURITY
# =========================================================

TENANT_DATABASE_NAME_PATTERN = re.compile(
    r"^tenant_[0-9a-f]{32}$"
)

SUPPORTED_TENANT_CLUSTER_KEY = "primary"


class TenantDatabaseConfigurationError(RuntimeError):
    """
    Raised when trusted tenant database configuration is invalid.

    This represents a server-side configuration or routing failure.
    Arbitrary client database connection information must never be
    accepted here.
    """

    pass


# =========================================================
# DATABASE NAME VALIDATION
# =========================================================


def validate_tenant_database_name(
    database_name: str,
) -> str:
    """
    Validate a server-generated WorkforceOS tenant database name.

    Valid form:

        tenant_<32 lowercase hexadecimal characters>

    Example:

        tenant_123e4567e89b12d3a456426614174000

    Invalid values are rejected rather than sanitized.
    """

    if not isinstance(
        database_name,
        str,
    ):
        raise TenantDatabaseConfigurationError(
            "Tenant database name must be a string."
        )

    normalized = database_name.strip()

    if not TENANT_DATABASE_NAME_PATTERN.fullmatch(
        normalized
    ):
        raise TenantDatabaseConfigurationError(
            "Invalid tenant database identity."
        )

    return normalized


# =========================================================
# CLUSTER VALIDATION
# =========================================================


def validate_tenant_cluster_key(
    cluster_key: str,
) -> str:
    """
    Validate the trusted tenant database cluster key.

    Phase 03 currently supports one PostgreSQL cluster:

        primary
    """

    if cluster_key != SUPPORTED_TENANT_CLUSTER_KEY:
        raise TenantDatabaseConfigurationError(
            "Unsupported tenant database cluster."
        )

    return cluster_key


# =========================================================
# TRUSTED BASE DATABASE URL
# =========================================================


def get_primary_database_url() -> URL:
    """
    Resolve the trusted PostgreSQL connection URL used as the basis
    for tenant database connections.

    Only the database component is changed during tenant routing.

    Driver, host, port, username, password and query parameters
    remain controlled by server configuration.
    """

    try:
        url = make_url(
            settings.control_database_url
        )

    except Exception as exc:
        raise TenantDatabaseConfigurationError(
            "Control database URL is invalid."
        ) from exc

    if not url.drivername.startswith(
        "postgresql"
    ):
        raise TenantDatabaseConfigurationError(
            "Tenant databases require PostgreSQL."
        )

    if url.host is None:
        raise TenantDatabaseConfigurationError(
            "PostgreSQL host is not configured."
        )

    return url


# =========================================================
# TENANT DATABASE URL
# =========================================================


def build_tenant_database_url(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> URL:
    """
    Build a trusted tenant database URL.

    The caller may supply only a database identity previously
    resolved from workforce_control.

    Arbitrary database URLs are never accepted.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    validate_tenant_cluster_key(
        cluster_key
    )

    base_url = get_primary_database_url()

    return base_url.set(
        database=trusted_database_name
    )


# =========================================================
# ENGINE / SESSIONMAKER CACHE
# =========================================================

_tenant_engines: dict[
    tuple[str, str],
    AsyncEngine,
] = {}

_tenant_sessionmakers: dict[
    tuple[str, str],
    async_sessionmaker[AsyncSession],
] = {}

# RLock is intentional.
#
# get_tenant_sessionmaker() may need to call get_tenant_engine()
# while cache creation is protected. Both helpers use this same
# lock, so a reentrant lock prevents self-deadlock.
_cache_lock = RLock()


def _cache_key(
    database_name: str,
    cluster_key: str,
) -> tuple[str, str]:
    return (
        cluster_key,
        database_name,
    )


# =========================================================
# ENGINE CREATION
# =========================================================


def get_tenant_engine(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> AsyncEngine:
    """
    Resolve or create the async SQLAlchemy engine for a trusted tenant.

    Engines are cached per:

        (cluster_key, database_name)

    database_name must originate from TenantDatabaseRegistry after
    workspace authorization.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    key = _cache_key(
        trusted_database_name,
        trusted_cluster_key,
    )

    existing = _tenant_engines.get(
        key
    )

    if existing is not None:
        return existing

    with _cache_lock:
        existing = _tenant_engines.get(
            key
        )

        if existing is not None:
            return existing

        tenant_url = build_tenant_database_url(
            trusted_database_name,
            cluster_key=trusted_cluster_key,
        )

        engine = create_async_engine(
            tenant_url,
            pool_pre_ping=True,
            future=True,
        )

        _tenant_engines[
            key
        ] = engine

        return engine


# =========================================================
# SESSIONMAKER CREATION
# =========================================================


def get_tenant_sessionmaker(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> async_sessionmaker[AsyncSession]:
    """
    Resolve or create the AsyncSession factory for one tenant DB.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    key = _cache_key(
        trusted_database_name,
        trusted_cluster_key,
    )

    existing = _tenant_sessionmakers.get(
        key
    )

    if existing is not None:
        return existing

    with _cache_lock:
        existing = _tenant_sessionmakers.get(
            key
        )

        if existing is not None:
            return existing

        engine = get_tenant_engine(
            trusted_database_name,
            cluster_key=trusted_cluster_key,
        )

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        _tenant_sessionmakers[
            key
        ] = session_factory

        return session_factory


# =========================================================
# TENANT SESSION
# =========================================================


@asynccontextmanager
async def tenant_session(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> AsyncIterator[AsyncSession]:
    """
    Open a tenant-scoped SQLAlchemy session.

    Authorization is intentionally outside this low-level helper.

    Correct request flow:

        authenticate user
            ↓
        validate active workspace membership
            ↓
        resolve TenantDatabaseRegistry
            ↓
        ensure registry is routable
            ↓
        open tenant_session()
    """

    session_factory = (
        get_tenant_sessionmaker(
            database_name,
            cluster_key=cluster_key,
        )
    )

    async with session_factory() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise


# =========================================================
# CACHE INSPECTION
# =========================================================


def has_cached_tenant_engine(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> bool:
    """
    Return whether an engine exists in the local process cache.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    key = _cache_key(
        trusted_database_name,
        trusted_cluster_key,
    )

    with _cache_lock:
        return key in _tenant_engines


# =========================================================
# SINGLE TENANT DISPOSAL
# =========================================================


async def dispose_tenant_engine(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> None:
    """
    Remove and dispose one tenant's cached engine/session factory.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    key = _cache_key(
        trusted_database_name,
        trusted_cluster_key,
    )

    with _cache_lock:
        engine = _tenant_engines.pop(
            key,
            None,
        )

        _tenant_sessionmakers.pop(
            key,
            None,
        )

    if engine is not None:
        await engine.dispose()


# =========================================================
# ALL TENANT DISPOSAL
# =========================================================


async def dispose_all_tenant_engines() -> None:
    """
    Dispose every cached tenant engine in this process.

    Intended for application shutdown and tests.
    """

    with _cache_lock:
        engines = list(
            _tenant_engines.values()
        )

        _tenant_engines.clear()
        _tenant_sessionmakers.clear()

    for engine in engines:
        await engine.dispose()


# =========================================================
# CACHE SIZE
# =========================================================


def tenant_engine_cache_size() -> int:
    """
    Return the number of cached tenant engines.
    """

    with _cache_lock:
        return len(
            _tenant_engines
        )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "SUPPORTED_TENANT_CLUSTER_KEY",
    "TENANT_DATABASE_NAME_PATTERN",
    "TenantDatabaseConfigurationError",
    "validate_tenant_database_name",
    "validate_tenant_cluster_key",
    "get_primary_database_url",
    "build_tenant_database_url",
    "get_tenant_engine",
    "get_tenant_sessionmaker",
    "tenant_session",
    "has_cached_tenant_engine",
    "dispose_tenant_engine",
    "dispose_all_tenant_engines",
    "tenant_engine_cache_size",
]