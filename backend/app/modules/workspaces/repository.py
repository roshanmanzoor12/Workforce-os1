from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    TenantDatabaseRegistry,
    Workspace,
    WorkspaceMembership,
)


# =========================================================
# WORKSPACE REPOSITORY
# =========================================================


class WorkspaceRepository:
    """
    Control-database repository for WorkspaceOS workspaces.

    Responsibilities:
    - workspace records
    - workspace memberships
    - tenant database registry records

    This repository never:
    - creates PostgreSQL databases
    - builds tenant connection URLs
    - accepts arbitrary client database names
    - performs tenant business-data queries
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # WORKSPACES
    # =====================================================

    async def get_workspace_by_id(
        self,
        workspace_id: uuid.UUID,
        *,
        include_relationships: bool = False,
    ) -> Workspace | None:
        statement = select(
            Workspace
        ).where(
            Workspace.id == workspace_id
        )

        if include_relationships:
            statement = statement.options(
                selectinload(
                    Workspace.memberships
                ),
                selectinload(
                    Workspace.tenant_database
                ),
            )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_workspace_by_slug(
        self,
        slug: str,
        *,
        include_relationships: bool = False,
    ) -> Workspace | None:
        statement = select(
            Workspace
        ).where(
            Workspace.slug == slug
        )

        if include_relationships:
            statement = statement.options(
                selectinload(
                    Workspace.memberships
                ),
                selectinload(
                    Workspace.tenant_database
                ),
            )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def workspace_slug_exists(
        self,
        slug: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(
                    Workspace.id
                )
            ).where(
                Workspace.slug == slug
            )
        )

        return bool(
            result.scalar_one()
        )

    async def create_workspace(
        self,
        *,
        name: str,
        slug: str,
        created_by_user_id: uuid.UUID,
        timezone: str = "UTC",
        workspace_type: str = "company",
        logo_url: str | None = None,
        status: str,
        is_active: bool = True,
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            slug=slug,
            created_by_user_id=created_by_user_id,
            timezone=timezone,
            workspace_type=workspace_type,
            logo_url=logo_url,
            status=status,
            is_active=is_active,
        )

        self.session.add(
            workspace
        )

        await self.session.flush()

        await self.session.refresh(
            workspace
        )

        return workspace

    async def update_workspace(
        self,
        workspace: Workspace,
        *,
        name: str | None = None,
        timezone: str | None = None,
        workspace_type: str | None = None,
        logo_url: str | None = None,
    ) -> Workspace:
        if name is not None:
            workspace.name = name

        if workspace_type is not None:
            workspace.workspace_type = workspace_type

        if timezone is not None:
            workspace.timezone = timezone

        if logo_url is not None:
            workspace.logo_url = logo_url

        await self.session.flush()

        return workspace

    async def set_workspace_status(
        self,
        workspace: Workspace,
        *,
        status: str,
    ) -> Workspace:
        workspace.status = status

        await self.session.flush()

        return workspace

    async def set_workspace_active(
        self,
        workspace: Workspace,
        *,
        active: bool,
    ) -> Workspace:
        workspace.is_active = active

        await self.session.flush()

        return workspace

    # =====================================================
    # WORKSPACE MEMBERSHIPS
    # =====================================================

    async def get_membership_by_id(
        self,
        membership_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.id
                == membership_id
            )
        )

        return result.scalar_one_or_none()

    async def get_workspace_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                and_(
                    WorkspaceMembership.workspace_id
                    == workspace_id,
                    WorkspaceMembership.user_id
                    == user_id,
                )
            )
        )

        return result.scalar_one_or_none()

    async def get_active_workspace_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                and_(
                    WorkspaceMembership.workspace_id
                    == workspace_id,
                    WorkspaceMembership.user_id
                    == user_id,
                    WorkspaceMembership.status
                    == MEMBERSHIP_STATUS_ACTIVE,
                )
            )
        )

        return result.scalar_one_or_none()

    async def create_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        role_key: str,
        status: str,
        invited_by_user_id: uuid.UUID | None = None,
        invited_at=None,
        joined_at=None,
    ) -> WorkspaceMembership:
        membership = WorkspaceMembership(
            workspace_id=workspace_id,
            user_id=user_id,
            role_key=role_key,
            status=status,
            invited_by_user_id=invited_by_user_id,
            invited_at=invited_at,
            joined_at=joined_at,
        )

        self.session.add(
            membership
        )

        await self.session.flush()

        await self.session.refresh(
            membership
        )

        return membership

    async def update_membership_role(
        self,
        membership: WorkspaceMembership,
        *,
        role_key: str,
    ) -> WorkspaceMembership:
        membership.role_key = role_key

        await self.session.flush()

        return membership

    async def update_membership_status(
        self,
        membership: WorkspaceMembership,
        *,
        status: str,
        invited_at=None,
        joined_at=None,
        suspended_at=None,
        removed_at=None,
    ) -> WorkspaceMembership:
        membership.status = status

        if invited_at is not None:
            membership.invited_at = invited_at

        if joined_at is not None:
            membership.joined_at = joined_at

        if suspended_at is not None:
            membership.suspended_at = suspended_at

        if removed_at is not None:
            membership.removed_at = removed_at

        await self.session.flush()

        return membership

    async def list_workspace_memberships(
        self,
        workspace_id: uuid.UUID,
        *,
        include_removed: bool = False,
    ) -> Sequence[WorkspaceMembership]:
        statement = select(
            WorkspaceMembership
        ).where(
            WorkspaceMembership.workspace_id
            == workspace_id
        )

        if not include_removed:
            statement = statement.where(
                WorkspaceMembership.status
                != "removed"
            )

        statement = statement.order_by(
            WorkspaceMembership.created_at.asc()
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def list_user_memberships(
        self,
        user_id: uuid.UUID,
        *,
        include_inactive: bool = False,
    ) -> Sequence[WorkspaceMembership]:
        statement = (
            select(
                WorkspaceMembership
            )
            .where(
                WorkspaceMembership.user_id
                == user_id
            )
            .options(
                selectinload(
                    WorkspaceMembership.workspace
                ).selectinload(
                    Workspace.tenant_database
                )
            )
        )

        if not include_inactive:
            statement = statement.where(
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE
            )

        statement = statement.order_by(
            WorkspaceMembership.created_at.asc()
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def count_workspace_memberships(
        self,
        workspace_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> int:
        statement = select(
            func.count(
                WorkspaceMembership.id
            )
        ).where(
            WorkspaceMembership.workspace_id
            == workspace_id
        )

        if status is not None:
            statement = statement.where(
                WorkspaceMembership.status
                == status
            )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    async def count_workspace_owners(
        self,
        workspace_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> int:
        statement = select(
            func.count(
                WorkspaceMembership.id
            )
        ).where(
            WorkspaceMembership.workspace_id
            == workspace_id,
            WorkspaceMembership.role_key
            == "owner",
        )

        if active_only:
            statement = statement.where(
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE
            )

        result = await self.session.execute(
            statement
        )

        return int(
            result.scalar_one()
        )

    # =====================================================
    # TENANT DATABASE REGISTRY
    # =====================================================

    async def get_tenant_database_by_id(
        self,
        registry_id: uuid.UUID,
    ) -> TenantDatabaseRegistry | None:
        result = await self.session.execute(
            select(
                TenantDatabaseRegistry
            ).where(
                TenantDatabaseRegistry.id
                == registry_id
            )
        )

        return result.scalar_one_or_none()

    async def get_tenant_database_for_workspace(
        self,
        workspace_id: uuid.UUID,
    ) -> TenantDatabaseRegistry | None:
        result = await self.session.execute(
            select(
                TenantDatabaseRegistry
            ).where(
                TenantDatabaseRegistry.workspace_id
                == workspace_id
            )
        )

        return result.scalar_one_or_none()

    async def get_tenant_database_by_name(
        self,
        database_name: str,
    ) -> TenantDatabaseRegistry | None:
        result = await self.session.execute(
            select(
                TenantDatabaseRegistry
            ).where(
                TenantDatabaseRegistry.database_name
                == database_name
            )
        )

        return result.scalar_one_or_none()

    async def tenant_database_name_exists(
        self,
        database_name: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(
                    TenantDatabaseRegistry.id
                )
            ).where(
                TenantDatabaseRegistry.database_name
                == database_name
            )
        )

        return bool(
            result.scalar_one()
        )

    async def create_tenant_database_registry(
        self,
        *,
        workspace_id: uuid.UUID,
        database_name: str,
        cluster_key: str = "primary",
        status: str,
        schema_version: str | None = None,
    ) -> TenantDatabaseRegistry:
        registry = TenantDatabaseRegistry(
            workspace_id=workspace_id,
            database_name=database_name,
            cluster_key=cluster_key,
            status=status,
            schema_version=schema_version,
        )

        self.session.add(
            registry
        )

        await self.session.flush()

        await self.session.refresh(
            registry
        )

        return registry

    async def set_tenant_database_status(
        self,
        registry: TenantDatabaseRegistry,
        *,
        status: str,
    ) -> TenantDatabaseRegistry:
        registry.status = status

        await self.session.flush()

        return registry

    async def mark_tenant_database_provisioning(
        self,
        registry: TenantDatabaseRegistry,
    ) -> TenantDatabaseRegistry:
        registry.status = "provisioning"
        registry.provision_attempts += 1

        registry.failed_at = None
        registry.last_error_code = None
        registry.last_error_message = None

        await self.session.flush()

        return registry

    async def mark_tenant_database_ready(
        self,
        registry: TenantDatabaseRegistry,
        *,
        provisioned_at,
        schema_version: str | None = None,
    ) -> TenantDatabaseRegistry:
        registry.status = "ready"
        registry.provisioned_at = provisioned_at
        registry.failed_at = None
        registry.last_error_code = None
        registry.last_error_message = None

        if schema_version is not None:
            registry.schema_version = schema_version

        await self.session.flush()

        return registry

    async def mark_tenant_database_failed(
        self,
        registry: TenantDatabaseRegistry,
        *,
        failed_at,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> TenantDatabaseRegistry:
        registry.status = "failed"
        registry.failed_at = failed_at
        registry.last_error_code = error_code
        registry.last_error_message = error_message

        await self.session.flush()

        return registry

    async def update_tenant_schema_version(
        self,
        registry: TenantDatabaseRegistry,
        *,
        schema_version: str,
    ) -> TenantDatabaseRegistry:
        registry.schema_version = schema_version

        await self.session.flush()

        return registry

    # =====================================================
    # AUTHORIZED WORKSPACE LOOKUP
    # =====================================================

    async def get_authorized_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[
        Workspace,
        WorkspaceMembership,
        TenantDatabaseRegistry | None,
    ] | None:
        """
        Resolve workspace context using server-owned control data.

        This is the repository foundation for safe tenant routing.

        The caller provides workspace UUID only.

        The database name is never accepted from client input.
        """

        result = await self.session.execute(
            select(
                Workspace,
                WorkspaceMembership,
            )
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id
                == Workspace.id,
            )
            .where(
                Workspace.id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE,
                Workspace.is_active.is_(
                    True
                ),
            )
        )

        row = result.first()

        if row is None:
            return None

        workspace = row[0]
        membership = row[1]

        tenant = await self.get_tenant_database_for_workspace(
            workspace.id
        )

        return (
            workspace,
            membership,
            tenant,
        )


# =========================================================
# REPOSITORY FACTORY
# =========================================================


def get_workspace_repository(
    session: AsyncSession,
) -> WorkspaceRepository:
    return WorkspaceRepository(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "WorkspaceRepository",
    "get_workspace_repository",
]