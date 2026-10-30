from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.orm import (
    selectinload,
)

from app.modules.workspace_rbac.models import (
    WorkspaceCustomRole,
    WorkspaceCustomRolePermission,
    WorkspaceMembershipModeration,
)
from app.modules.workspaces.models import (
    WorkspaceMembership,
)


class WorkspaceRBACRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CUSTOM ROLES
    # =====================================================

    async def list_custom_roles(
        self,
        workspace_id: uuid.UUID,
    ) -> Sequence[
        WorkspaceCustomRole
    ]:
        result = await self.session.execute(
            select(
                WorkspaceCustomRole
            )
            .where(
                WorkspaceCustomRole.workspace_id
                == workspace_id
            )
            .order_by(
                WorkspaceCustomRole
                .display_name
                .asc()
            )
        )

        return result.scalars().all()

    async def get_custom_role(
        self,
        *,
        workspace_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> WorkspaceCustomRole | None:
        result = await self.session.execute(
            select(
                WorkspaceCustomRole
            ).where(
                WorkspaceCustomRole.workspace_id
                == workspace_id,
                WorkspaceCustomRole.id
                == role_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_custom_role_by_key(
        self,
        *,
        workspace_id: uuid.UUID,
        role_key: str,
    ) -> WorkspaceCustomRole | None:
        result = await self.session.execute(
            select(
                WorkspaceCustomRole
            ).where(
                WorkspaceCustomRole.workspace_id
                == workspace_id,
                WorkspaceCustomRole.role_key
                == role_key,
            )
        )

        return result.scalar_one_or_none()

    async def create_custom_role(
        self,
        *,
        workspace_id: uuid.UUID,
        role_key: str,
        display_name: str,
        description: str | None,
        created_by_user_id: uuid.UUID,
    ) -> WorkspaceCustomRole:
        role = WorkspaceCustomRole(
            workspace_id=workspace_id,
            role_key=role_key,
            display_name=display_name,
            description=description,
            is_active=True,
            created_by_user_id=(
                created_by_user_id
            ),
        )

        self.session.add(role)

        await self.session.flush()

        return role

    async def set_role_permissions(
        self,
        *,
        role_id: uuid.UUID,
        permissions: set[str],
    ) -> None:
        await self.session.execute(
            delete(
                WorkspaceCustomRolePermission
            ).where(
                WorkspaceCustomRolePermission
                .role_id
                == role_id
            )
        )

        for permission in sorted(
            permissions
        ):
            self.session.add(
                WorkspaceCustomRolePermission(
                    role_id=role_id,
                    permission_key=permission,
                )
            )

        await self.session.flush()

    async def get_role_permissions(
        self,
        role_id: uuid.UUID,
    ) -> frozenset[str]:
        result = await self.session.execute(
            select(
                WorkspaceCustomRolePermission
                .permission_key
            ).where(
                WorkspaceCustomRolePermission
                .role_id
                == role_id
            )
        )

        return frozenset(
            result.scalars().all()
        )

    async def delete_custom_role(
        self,
        role: WorkspaceCustomRole,
    ) -> None:
        await self.session.delete(role)

        await self.session.flush()

    # =====================================================
    # MEMBERS
    # =====================================================

    async def list_members(
        self,
        workspace_id: uuid.UUID,
    ) -> Sequence[
        WorkspaceMembership
    ]:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            )
            .options(
                selectinload(
                    WorkspaceMembership.user
                )
            )
            .where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.status
                != "removed",
            )
            .order_by(
                WorkspaceMembership
                .created_at
                .asc()
            )
        )

        return result.scalars().all()

    async def get_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        membership_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            )
            .options(
                selectinload(
                    WorkspaceMembership.user
                )
            )
            .where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.id
                == membership_id,
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # MODERATION
    # =====================================================

    async def get_moderation(
        self,
        membership_id: uuid.UUID,
    ) -> WorkspaceMembershipModeration | None:
        result = await self.session.execute(
            select(
                WorkspaceMembershipModeration
            ).where(
                WorkspaceMembershipModeration
                .membership_id
                == membership_id
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_moderation(
        self,
        membership_id: uuid.UUID,
    ) -> WorkspaceMembershipModeration:
        moderation = await self.get_moderation(
            membership_id
        )

        if moderation is not None:
            return moderation

        moderation = (
            WorkspaceMembershipModeration(
                membership_id=membership_id,
            )
        )

        self.session.add(moderation)

        await self.session.flush()

        return moderation


__all__ = [
    "WorkspaceRBACRepository",
]