from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound, ValidationError
from app.modules.workspace_permissions.roles import (
    BUILT_IN_ROLE_KEYS,
    OWNER_ROLE,
)
from app.modules.workspace_rbac.assignment_models import (
    WorkspaceMembershipRoleAssignment,
)
from app.modules.workspace_rbac.models import WorkspaceCustomRole
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    WorkspaceMembership,
)


class MembershipRoleAssignmentRepository:
    """
    Internal persistence operations.

    The calling service must authorize the actor and validate
    grantable permissions. This repository validates workspace
    ownership of memberships and custom roles.

    These methods do not commit transactions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def normalize_role_key(role_key: str) -> str:
        if not isinstance(role_key, str):
            raise ValidationError("Workspace role is invalid.")

        normalized = role_key.strip().lower()

        if not normalized or len(normalized) > 64:
            raise ValidationError("Workspace role is invalid.")

        if normalized == OWNER_ROLE:
            raise ValidationError(
                "Owner cannot be assigned as an additional role."
            )

        return normalized

    async def _membership(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        active_only: bool,
    ) -> WorkspaceMembership:
        statement = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.id == membership_id,
        )

        if active_only:
            statement = statement.where(
                WorkspaceMembership.status == MEMBERSHIP_STATUS_ACTIVE
            )

        statement = statement.with_for_update()

        membership = await self.session.scalar(statement)

        if (
            membership is None
            or membership.workspace_id != workspace_id
            or membership.id != membership_id
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
    ) -> Sequence[WorkspaceMembershipRoleAssignment]:
        assignment = WorkspaceMembershipRoleAssignment

        statement = (
            select(assignment)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.id == assignment.membership_id,
            )
            .outerjoin(
                WorkspaceCustomRole,
                WorkspaceCustomRole.id == assignment.custom_role_id,
            )
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.id == membership_id,
                or_(
                    assignment.custom_role_id.is_(None),
                    and_(
                        WorkspaceCustomRole.workspace_id == workspace_id,
                        WorkspaceCustomRole.role_key == assignment.role_key,
                    ),
                ),
            )
            .order_by(assignment.role_key)
        )

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        role_key: str,
        granted_by_user_id: uuid.UUID,
    ) -> WorkspaceMembershipRoleAssignment:
        normalized = self.normalize_role_key(role_key)

        membership = await self._membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
            active_only=True,
        )

        if membership.role_key.strip().lower() == normalized:
            raise ValidationError(
                "This role is already the member's primary role."
            )

        custom_role_id = None

        if normalized not in BUILT_IN_ROLE_KEYS:
            custom_role = await self.session.scalar(
                select(WorkspaceCustomRole)
                .where(
                    WorkspaceCustomRole.workspace_id == workspace_id,
                    WorkspaceCustomRole.role_key == normalized,
                    WorkspaceCustomRole.is_active.is_(True),
                )
                .with_for_update()
            )

            if (
                custom_role is None
                or not custom_role.is_active
                or custom_role.workspace_id != workspace_id
                or custom_role.role_key != normalized
            ):
                raise ResourceNotFound(
                    "Active workspace role was not found."
                )

            custom_role_id = custom_role.id

        existing = await self.session.scalar(
            select(WorkspaceMembershipRoleAssignment)
            .where(
                WorkspaceMembershipRoleAssignment.membership_id
                == membership_id,
                WorkspaceMembershipRoleAssignment.role_key == normalized,
            )
            .with_for_update()
        )

        if existing is not None:
            if existing.custom_role_id != custom_role_id:
                raise ValidationError(
                    "Workspace role assignment is inconsistent."
                )
            return existing

        assignment = WorkspaceMembershipRoleAssignment(
            membership_id=membership_id,
            role_key=normalized,
            custom_role_id=custom_role_id,
            granted_by_user_id=granted_by_user_id,
        )

        self.session.add(assignment)
        await self.session.flush()

        return assignment

    async def remove(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
        role_key: str,
    ) -> bool:
        normalized = self.normalize_role_key(role_key)

        await self._membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
            active_only=False,
        )

        assignment = await self.session.scalar(
            select(WorkspaceMembershipRoleAssignment)
            .where(
                WorkspaceMembershipRoleAssignment.membership_id
                == membership_id,
                WorkspaceMembershipRoleAssignment.role_key == normalized,
            )
            .with_for_update()
        )

        if assignment is None:
            return False

        await self.session.delete(assignment)
        await self.session.flush()

        return True


__all__ = ["MembershipRoleAssignmentRepository"]