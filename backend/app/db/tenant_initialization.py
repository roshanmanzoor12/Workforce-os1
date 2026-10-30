from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.db.tenant import (
    tenant_session,
    validate_tenant_cluster_key,
    validate_tenant_database_name,
)
from app.db.tenant_models import (
    TenantMetadata,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
)


# =========================================================
# CONSTANTS
# =========================================================


CURRENT_TENANT_SCHEMA_VERSION = "p6k7l8m9n0o1"

# =========================================================
# ERRORS
# =========================================================


class TenantInitializationError(
    RuntimeError
):
    """
    Raised when a physical tenant database cannot be safely
    initialized or does not match its control-plane registry.
    """

    pass


# =========================================================
# RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class TenantInitializationResult:
    workspace_id: uuid.UUID
    database_name: str
    schema_version: str

    metadata_created: bool
    registry_marked_ready: bool


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# TENANT METADATA INITIALIZATION
# =========================================================


async def initialize_tenant_metadata(
    *,
    workspace_id: uuid.UUID,
    database_name: str,
    cluster_key: str,
    schema_version: str = (
        CURRENT_TENANT_SCHEMA_VERSION
    ),
) -> bool:
    """
    Ensure the physical tenant database contains exactly one
    tenant_metadata identity row for the expected workspace.

    Returns:

        True
            metadata row was created

        False
            matching metadata already existed

    If metadata exists for another workspace, initialization
    fails instead of silently reassigning the database.

    schema_version represents the tenant Alembic revision that
    WorkforceOS expects the physical database to be running.
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

    async with tenant_session(
        trusted_database_name,
        cluster_key=(
            trusted_cluster_key
        ),
    ) as session:
        result = await session.execute(
            select(
                TenantMetadata
            )
        )

        metadata_rows = list(
            result.scalars().all()
        )

        if len(metadata_rows) > 1:
            raise TenantInitializationError(
                "Tenant database contains "
                "multiple metadata identity rows."
            )

        if metadata_rows:
            metadata = metadata_rows[0]

            if (
                metadata.workspace_id
                != workspace_id
            ):
                raise TenantInitializationError(
                    "Tenant database workspace "
                    "identity does not match "
                    "the control-plane registry."
                )

            if (
                metadata.schema_version
                != schema_version
            ):
                metadata.schema_version = (
                    schema_version
                )

            if not metadata.is_active:
                metadata.is_active = True

            await session.commit()

            return False

        metadata = TenantMetadata(
            workspace_id=workspace_id,
            schema_version=(
                schema_version
            ),
            initialized_at=utc_now(),
            is_active=True,
        )

        session.add(
            metadata
        )

        await session.commit()

        return True


# =========================================================
# CONTROL REGISTRY FINALIZATION
# =========================================================


async def mark_tenant_registry_ready(
    control_session: AsyncSession,
    *,
    registry: TenantDatabaseRegistry,
    schema_version: str = (
        CURRENT_TENANT_SCHEMA_VERSION
    ),
) -> None:
    """
    Mark the trusted control-plane tenant registry as ready.

    This occurs only after:

        physical database exists
        ->
        Alembic upgrade succeeds
        ->
        tenant metadata is initialized
    """

    registry.status = (
        TENANT_STATUS_READY
    )

    registry.schema_version = (
        schema_version
    )

    registry.provisioned_at = (
        utc_now()
    )

    registry.failed_at = None
    registry.last_error_code = None
    registry.last_error_message = None

    control_session.add(
        registry
    )

    await control_session.commit()


# =========================================================
# COMPLETE INITIALIZATION
# =========================================================


async def initialize_registered_tenant(
    control_session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    schema_version: str = (
        CURRENT_TENANT_SCHEMA_VERSION
    ),
) -> TenantInitializationResult:
    """
    Complete tenant initialization for one trusted workspace.

    Security boundary:

        caller supplies workspace_id only

        database_name + cluster_key
        are resolved only from workforce_control

    A caller cannot select an arbitrary physical tenant database.
    """

    result = await (
        control_session.execute(
            select(
                TenantDatabaseRegistry
            ).where(
                TenantDatabaseRegistry
                .workspace_id
                == workspace_id
            )
        )
    )

    registry = (
        result.scalar_one_or_none()
    )

    if registry is None:
        raise TenantInitializationError(
            "Tenant database registry "
            "was not found for workspace."
        )

    trusted_database_name = (
        validate_tenant_database_name(
            registry.database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            registry.cluster_key
        )
    )

    metadata_created = (
        await initialize_tenant_metadata(
            workspace_id=workspace_id,
            database_name=(
                trusted_database_name
            ),
            cluster_key=(
                trusted_cluster_key
            ),
            schema_version=(
                schema_version
            ),
        )
    )

    await mark_tenant_registry_ready(
        control_session,
        registry=registry,
        schema_version=schema_version,
    )

    return TenantInitializationResult(
        workspace_id=workspace_id,
        database_name=(
            trusted_database_name
        ),
        schema_version=(
            schema_version
        ),
        metadata_created=(
            metadata_created
        ),
        registry_marked_ready=True,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "CURRENT_TENANT_SCHEMA_VERSION",
    "TenantInitializationError",
    "TenantInitializationResult",
    "initialize_tenant_metadata",
    "mark_tenant_registry_ready",
    "initialize_registered_tenant",
]
