from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config

from app.db.tenant import (
    SUPPORTED_TENANT_CLUSTER_KEY,
    validate_tenant_cluster_key,
    validate_tenant_database_name,
)


# =========================================================
# PATHS
# =========================================================

BACKEND_ROOT = Path(
    __file__
).resolve().parents[2]

TENANT_ALEMBIC_CONFIG_PATH = (
    BACKEND_ROOT
    / "alembic.tenant.ini"
)


# =========================================================
# ERRORS
# =========================================================


class TenantMigrationError(RuntimeError):
    """
    Raised when tenant schema migrations cannot be completed.
    """

    pass


# =========================================================
# RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class TenantMigrationResult:
    database_name: str
    cluster_key: str
    target_revision: str


# =========================================================
# ALEMBIC CONFIGURATION
# =========================================================


def build_tenant_alembic_config(
    *,
    database_name: str,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> Config:
    """
    Build an Alembic configuration for exactly one trusted
    tenant database.

    No database URL is accepted from the caller.

    The database name is passed through Alembic's -x mechanism
    and migrations/tenant/env.py builds the connection URL from
    trusted server configuration.
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

    if not TENANT_ALEMBIC_CONFIG_PATH.is_file():
        raise TenantMigrationError(
            "Tenant Alembic configuration file was not found."
        )

    config = Config(
        str(
            TENANT_ALEMBIC_CONFIG_PATH
        )
    )

    config.cmd_opts = SimpleNamespace(
        x=[
            (
                "database_name="
                f"{trusted_database_name}"
            ),
            (
                "cluster_key="
                f"{trusted_cluster_key}"
            ),
        ]
    )

    return config


# =========================================================
# SYNCHRONOUS MIGRATION WORKER
# =========================================================


def _upgrade_tenant_database_sync(
    *,
    database_name: str,
    cluster_key: str,
    revision: str,
) -> TenantMigrationResult:
    """
    Run Alembic synchronously.

    This function is executed in a worker thread because the tenant
    Alembic environment manages its own asyncio event loop.
    """

    config = build_tenant_alembic_config(
        database_name=database_name,
        cluster_key=cluster_key,
    )

    try:
        command.upgrade(
            config,
            revision,
        )

    except Exception as exc:
        raise TenantMigrationError(
            "Tenant database migration failed."
        ) from exc

    return TenantMigrationResult(
        database_name=database_name,
        cluster_key=cluster_key,
        target_revision=revision,
    )


# =========================================================
# ASYNC PUBLIC MIGRATION API
# =========================================================


async def upgrade_tenant_database(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
    revision: str = "head",
) -> TenantMigrationResult:
    """
    Upgrade one trusted tenant database.

    Safe request:

        database_name
            ↓
        strict tenant-name validation
            ↓
        trusted Alembic tenant environment
            ↓
        trusted server database credentials
            ↓
        requested migration revision

    This function intentionally runs Alembic inside a worker
    thread because migrations/tenant/env.py uses asyncio.run().
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

    if not isinstance(
        revision,
        str,
    ):
        raise TenantMigrationError(
            "Tenant migration revision must be a string."
        )

    trusted_revision = (
        revision.strip()
    )

    if not trusted_revision:
        raise TenantMigrationError(
            "Tenant migration revision cannot be empty."
        )

    return await asyncio.to_thread(
        _upgrade_tenant_database_sync,
        database_name=trusted_database_name,
        cluster_key=trusted_cluster_key,
        revision=trusted_revision,
    )


# =========================================================
# HEAD MIGRATION
# =========================================================


async def upgrade_tenant_database_to_head(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> TenantMigrationResult:
    """
    Upgrade one trusted tenant database to the latest tenant
    migration head.
    """

    return await upgrade_tenant_database(
        database_name,
        cluster_key=cluster_key,
        revision="head",
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "TENANT_ALEMBIC_CONFIG_PATH",
    "TenantMigrationError",
    "TenantMigrationResult",
    "build_tenant_alembic_config",
    "upgrade_tenant_database",
    "upgrade_tenant_database_to_head",
]