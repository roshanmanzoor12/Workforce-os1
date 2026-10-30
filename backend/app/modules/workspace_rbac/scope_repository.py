from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound, ValidationError
from app.modules.workspace_rbac.scope_models import (
    SAVED_RESOURCE_SCOPE_TYPES,
    WorkspaceMembershipScopeGrant,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    WORKSPACE_STATUS_READY,
    Workspace,
    WorkspaceMembership,
)


class MembershipScopeGrantRepository:
    """
    Internal control-plane persistence.

    Callers authorize the actor and validate tenant resources.
    Mutations lock the target membership and never commit.

    The application service must lock the workspace before mutations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def validate_uuid(value: object, *, name: str) -> uuid.UUID:
        if not isinstance(value, uuid.UUID):
            raise ValidationError(f"Invalid {name}.")

        return value

    @staticmethod
    def validate_scope_type(value: object) -> str:
        if (
            not isinstance(value, str)
            or value not in SAVED_RESOURCE_SCOPE_TYPES
        ):
            raise ValidationError(
                "Saved scope type must be department or team."
            )

        return value

    async def require_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        lock: bool = False,
    ) -> Workspace:
        self.validate_uuid(workspace_id, name="workspace ID")

        statement = select(Workspace).where(
            Workspace.id == workspace_id,
        )

        if lock:
            statement = statement.with_for_update()

        workspace = await self.session.scalar(
            statement.execution_options(populate_existing=True),
        )

        if (
            workspace is None
            or workspace.id != workspace_id
            or not workspace.is_active
            or workspace.status != WORKSPACE_STATUS_READY
        ):
            raise ResourceNotFound("Workspace was not found.")

        return workspace

    async def require_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        active_only: bool = True,
        lock: bool = False,
    ) -> WorkspaceMembership:
        self.validate_uuid(workspace_id, name="workspace ID")
        self.validate_uuid(membership_id, name="membership ID")

        statement = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.id == membership_id,
        )

        if active_only:
            statement = statement.where(
                WorkspaceMembership.status == MEMBERSHIP_STATUS_ACTIVE,
            )

        if lock:
            statement = statement.with_for_update()

        membership = await self.session.scalar(
            statement.execution_options(populate_existing=True),
        )

        if (
            membership is None
            or membership.id != membership_id
            or membership.workspace_id != workspace_id
            or (
                active_only
                and membership.status != MEMBERSHIP_STATUS_ACTIVE
            )
        ):
            raise ResourceNotFound(
                "Workspace membership was not found."
            )

        return membership

    async def list_for(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
    ) -> tuple[WorkspaceMembershipScopeGrant, ...]:
        self.validate_uuid(workspace_id, name="workspace ID")
        self.validate_uuid(membership_id, name="membership ID")

        grant = WorkspaceMembershipScopeGrant

        statement = (
            select(grant)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.id == grant.membership_id,
            )
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.status == MEMBERSHIP_STATUS_ACTIVE,
                grant.membership_id == membership_id,
            )
            .order_by(grant.scope_type, grant.resource_id)
            .execution_options(populate_existing=True)
        )

        result = await self.session.execute(statement)
        return tuple(result.scalars().all())

    async def add(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        scope_type: str,
        resource_id: uuid.UUID,
        granted_by_user_id: uuid.UUID,
    ) -> WorkspaceMembershipScopeGrant:
        scope_type = self.validate_scope_type(scope_type)
        self.validate_uuid(resource_id, name="resource ID")
        self.validate_uuid(granted_by_user_id, name="grantor user ID")

        await self.require_membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
            active_only=True,
            lock=True,
        )

        grant = WorkspaceMembershipScopeGrant

        statement = (
            insert(grant)
            .values(
                membership_id=membership_id,
                scope_type=scope_type,
                resource_id=resource_id,
                granted_by_user_id=granted_by_user_id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    grant.membership_id,
                    grant.scope_type,
                    grant.resource_id,
                ],
            )
            .returning(grant)
        )

        created = await self.session.scalar(statement)

        if created is not None:
            return created

        # An existing grant retains its original grantor and timestamp.
        existing = await self.session.scalar(
            select(grant)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.id == grant.membership_id,
            )
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.status == MEMBERSHIP_STATUS_ACTIVE,
                grant.membership_id == membership_id,
                grant.scope_type == scope_type,
                grant.resource_id == resource_id,
            )
            .execution_options(populate_existing=True),
        )

        if existing is None:
            raise ResourceNotFound("Scope grant was not found.")

        return existing

    async def remove(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        scope_type: str,
        resource_id: uuid.UUID,
    ) -> bool:
        scope_type = self.validate_scope_type(scope_type)
        self.validate_uuid(resource_id, name="resource ID")

        # Permit cleanup after suspension/removal.
        await self.require_membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
            active_only=False,
            lock=True,
        )

        grant = WorkspaceMembershipScopeGrant

        membership_in_workspace = (
            select(WorkspaceMembership.id)
            .where(
                WorkspaceMembership.id == grant.membership_id,
                WorkspaceMembership.workspace_id == workspace_id,
            )
            .exists()
        )

        deleted_id = await self.session.scalar(
            delete(grant)
            .where(
                grant.membership_id == membership_id,
                grant.scope_type == scope_type,
                grant.resource_id == resource_id,
                membership_in_workspace,
            )
            .returning(grant.resource_id),
        )

        return deleted_id is not None


__all__ = ["MembershipScopeGrantRepository"]