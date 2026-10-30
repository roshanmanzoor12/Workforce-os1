from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tenant import (
    dispose_tenant_engine,
    validate_tenant_cluster_key,
    validate_tenant_database_name,
)
from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
    initialize_registered_tenant,
)
from app.db.tenant_migrations import (
    upgrade_tenant_database_to_head,
)
from app.db.tenant_provisioning import (
    provision_tenant_database,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_FAILED,
    TENANT_STATUS_PENDING,
    TENANT_STATUS_PROVISIONING,
    TENANT_STATUS_READY,
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_READY,
    TenantDatabaseRegistry,
    Workspace,
)


# =========================================================
# ERRORS
# =========================================================


class WorkspaceProvisioningError(RuntimeError):
    """
    Raised when a workspace tenant cannot be provisioned.

    The original exception is chained internally, while the
    control-plane registry records only a safe failure summary.
    """

    pass


# =========================================================
# RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceProvisioningResult:
    workspace_id: uuid.UUID
    database_name: str
    cluster_key: str
    schema_version: str
    database_created: bool
    database_already_existed: bool
    metadata_created: bool
    workspace_ready: bool
    tenant_ready: bool


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# SAFE FAILURE TEXT
# =========================================================


def _safe_error_code(
    exc: Exception,
) -> str:
    """
    Produce a stable internal failure category.

    Do not persist database URLs, passwords, tracebacks, SQL,
    environment variables, or raw driver errors.
    """

    name = exc.__class__.__name__

    normalized = "".join(
        character
        if character.isalnum()
        else "_"
        for character in name
    ).upper()

    return normalized[:100] or "PROVISIONING_ERROR"


def _safe_error_message(
    exc: Exception,
) -> str:
    """
    Persist only a generic operational message.

    Detailed exceptions remain available through normal server
    exception chaining/logging, not through public workspace data.
    """

    del exc

    return (
        "Tenant database provisioning failed. "
        "The operation may be retried."
    )


# =========================================================
# CONTROL-PLANE LOOKUP
# =========================================================


async def _load_workspace_and_registry(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
) -> tuple[
    Workspace,
    TenantDatabaseRegistry,
]:
    workspace_result = await session.execute(
        select(
            Workspace
        ).where(
            Workspace.id == workspace_id
        )
    )

    workspace = (
        workspace_result.scalar_one_or_none()
    )

    if workspace is None:
        raise WorkspaceProvisioningError(
            "Workspace was not found."
        )

    registry_result = await session.execute(
        select(
            TenantDatabaseRegistry
        ).where(
            TenantDatabaseRegistry.workspace_id
            == workspace_id
        )
    )

    registry = (
        registry_result.scalar_one_or_none()
    )

    if registry is None:
        raise WorkspaceProvisioningError(
            "Tenant database registry was not found."
        )

    return (
        workspace,
        registry,
    )


# =========================================================
# MARK PROVISIONING
# =========================================================


async def _mark_provisioning(
    session: AsyncSession,
    *,
    workspace: Workspace,
    registry: TenantDatabaseRegistry,
) -> None:
    """
    Persist the provisioning attempt before external database work.

    This ensures another request never sees a silent pending state
    while physical provisioning is already underway.
    """

    workspace.status = (
        WORKSPACE_STATUS_PROVISIONING
    )

    registry.status = (
        TENANT_STATUS_PROVISIONING
    )

    registry.provision_attempts = (
        int(
            registry.provision_attempts
            or 0
        )
        + 1
    )

    registry.failed_at = None
    registry.last_error_code = None
    registry.last_error_message = None

    session.add(
        workspace
    )

    session.add(
        registry
    )

    await session.commit()


# =========================================================
# MARK FAILED
# =========================================================


async def _mark_failed(
    session: AsyncSession,
    *,
    workspace: Workspace,
    registry: TenantDatabaseRegistry,
    exc: Exception,
) -> None:
    """
    Record provisioning failure without exposing infrastructure
    secrets through the control database.
    """

    registry.status = (
        TENANT_STATUS_FAILED
    )

    registry.failed_at = (
        utc_now()
    )

    registry.last_error_code = (
        _safe_error_code(
            exc
        )
    )

    registry.last_error_message = (
        _safe_error_message(
            exc
        )
    )

    workspace.status = (
        WORKSPACE_STATUS_PROVISIONING
    )

    session.add(
        workspace
    )

    session.add(
        registry
    )

    await session.commit()


# =========================================================
# MARK READY
# =========================================================


async def _mark_workspace_ready(
    session: AsyncSession,
    *,
    workspace: Workspace,
    registry: TenantDatabaseRegistry,
) -> None:
    """
    Complete the control-plane state transition after the physical
    tenant is fully usable.
    """

    workspace.status = (
        WORKSPACE_STATUS_READY
    )

    workspace.is_active = True

    registry.status = (
        TENANT_STATUS_READY
    )

    registry.schema_version = (
        CURRENT_TENANT_SCHEMA_VERSION
    )

    if registry.provisioned_at is None:
        registry.provisioned_at = (
            utc_now()
        )

    registry.failed_at = None
    registry.last_error_code = None
    registry.last_error_message = None

    session.add(
        workspace
    )

    session.add(
        registry
    )

    await session.commit()


# =========================================================
# PROVISION WORKSPACE
# =========================================================


async def provision_workspace_tenant(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
) -> WorkspaceProvisioningResult:
    """
    Provision one registered WorkforceOS workspace tenant.

    Trusted flow:

        workspace_id
            ↓
        workforce_control lookup
            ↓
        server-owned database_name
            ↓
        registry = provisioning
            ↓
        CREATE DATABASE if missing
            ↓
        Alembic tenant upgrade head
            ↓
        tenant_metadata initialization
            ↓
        physical workspace identity verification
            ↓
        tenant registry = ready
            ↓
        workspace = ready

    The caller never supplies:

        database_name
        database URL
        host
        port
        username
        password

    This function is intentionally idempotent. Retrying an interrupted
    provisioning attempt must not create a second tenant database.
    """

    workspace, registry = (
        await _load_workspace_and_registry(
            session,
            workspace_id=workspace_id,
        )
    )

    database_name = (
        validate_tenant_database_name(
            registry.database_name
        )
    )

    cluster_key = (
        validate_tenant_cluster_key(
            registry.cluster_key
        )
    )

    if (
        workspace.status
        == WORKSPACE_STATUS_READY
        and registry.status
        == TENANT_STATUS_READY
        and registry.schema_version
        == CURRENT_TENANT_SCHEMA_VERSION
    ):
        return WorkspaceProvisioningResult(
            workspace_id=workspace.id,
            database_name=database_name,
            cluster_key=cluster_key,
            schema_version=(
                CURRENT_TENANT_SCHEMA_VERSION
            ),
            database_created=False,
            database_already_existed=True,
            metadata_created=False,
            workspace_ready=True,
            tenant_ready=True,
        )

    allowed_registry_states = {
        TENANT_STATUS_PENDING,
        TENANT_STATUS_PROVISIONING,
        TENANT_STATUS_FAILED,
        TENANT_STATUS_READY,
    }

    if registry.status not in allowed_registry_states:
        raise WorkspaceProvisioningError(
            "Tenant database is not in a provisionable state."
        )

    await _mark_provisioning(
        session,
        workspace=workspace,
        registry=registry,
    )

    try:
        provision_result = (
            await provision_tenant_database(
                database_name,
                cluster_key=cluster_key,
            )
        )

        await upgrade_tenant_database_to_head(
            database_name,
            cluster_key=cluster_key,
        )

        initialization_result = (
            await initialize_registered_tenant(
                session,
                workspace_id=workspace.id,
                schema_version=(
                    CURRENT_TENANT_SCHEMA_VERSION
                ),
            )
        )

        await _mark_workspace_ready(
            session,
            workspace=workspace,
            registry=registry,
        )

        return WorkspaceProvisioningResult(
            workspace_id=workspace.id,
            database_name=database_name,
            cluster_key=cluster_key,
            schema_version=(
                CURRENT_TENANT_SCHEMA_VERSION
            ),
            database_created=(
                provision_result.created
            ),
            database_already_existed=(
                provision_result.already_existed
            ),
            metadata_created=(
                initialization_result.metadata_created
            ),
            workspace_ready=True,
            tenant_ready=True,
        )

    except Exception as exc:
        await session.rollback()

        try:
            workspace, registry = (
                await _load_workspace_and_registry(
                    session,
                    workspace_id=workspace_id,
                )
            )

            await _mark_failed(
                session,
                workspace=workspace,
                registry=registry,
                exc=exc,
            )

        except Exception:
            await session.rollback()

        try:
            await dispose_tenant_engine(
                database_name,
                cluster_key=cluster_key,
            )

        except Exception:
            pass

        raise WorkspaceProvisioningError(
            "Workspace tenant provisioning failed."
        ) from exc


# =========================================================
# RETRY
# =========================================================


async def retry_workspace_tenant_provisioning(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
) -> WorkspaceProvisioningResult:
    """
    Retry provisioning using only the existing trusted registry.

    No new database identity is generated during retry.
    """

    return await provision_workspace_tenant(
        session,
        workspace_id=workspace_id,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "WorkspaceProvisioningError",
    "WorkspaceProvisioningResult",
    "provision_workspace_tenant",
    "retry_workspace_tenant_provisioning",
]