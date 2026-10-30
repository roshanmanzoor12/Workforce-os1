from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.memberships.enums import (
    WorkspaceMembershipRole,
)

from app.modules.memberships.models import (
    WorkspaceMembership,
)
from app.modules.memberships.repository import (
    WorkspaceMembershipRepository,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_REMOVED,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_MEMBER,
    WORKSPACE_ROLE_OWNER,
    Workspace,
)

MANAGER_ROLES = frozenset(
    {
        WorkspaceMembershipRole.OWNER,
        WorkspaceMembershipRole.ADMIN,
    }
)

WORKSPACE_ADMIN_ROLES = frozenset(
    {
        WorkspaceMembershipRole.OWNER,
    }
)

def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


class WorkspaceMembershipService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            WorkspaceMembershipRepository(
                session
            )
        )

    async def _get_workspace(
        self,
        workspace_id: uuid.UUID,
    ) -> Workspace:
        result = await self.session.execute(
            select(
                Workspace
            ).where(
                Workspace.id
                == workspace_id
            )
        )

        workspace = (
            result.scalar_one_or_none()
        )

        if workspace is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Workspace not found.",
            )

        return workspace

    @staticmethod
    def _workspace_creator_id(
        workspace: Workspace,
    ) -> uuid.UUID:
        value = getattr(
            workspace,
            "created_by_user_id",
            None,
        )

        if value is None:
            raise RuntimeError(
                "Workspace does not expose "
                "created_by_user_id."
            )

        if isinstance(
            value,
            uuid.UUID,
        ):
            return value

        return uuid.UUID(
            str(value)
        )

    async def bootstrap_owner(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership:
        workspace = (
            await self._get_workspace(
                workspace_id
            )
        )

        creator_user_id = (
            self._workspace_creator_id(
                workspace
            )
        )

        if creator_user_id != user_id:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only the workspace creator "
                    "can bootstrap ownership."
                ),
            )

        existing = (
            await self.repository
            .get_for_user(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if existing is not None:
            existing.role_key = (
                WORKSPACE_ROLE_OWNER
            )

            existing.status = (
                MEMBERSHIP_STATUS_ACTIVE
            )

            existing.joined_at = (
                existing.joined_at
                or utcnow()
            )

            existing.suspended_at = None
            existing.removed_at = None

            await self.session.commit()
            await self.session.refresh(
                existing
            )

            return existing

        membership = WorkspaceMembership(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            role_key=WORKSPACE_ROLE_OWNER,
            status=MEMBERSHIP_STATUS_ACTIVE,
            invited_by_user_id=None,
            invited_at=None,
            joined_at=utcnow(),
            suspended_at=None,
            removed_at=None,
        )

        await self.repository.add(
            membership
        )

        await self.session.commit()
        await self.session.refresh(
            membership
        )

        return membership

    async def require_active_member(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership:
        membership = (
            await self.repository
            .get_active_for_user(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if membership is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Active workspace membership "
                    "required."
                ),
            )

        return membership

    async def require_manager(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership:
        membership = (
            await self.require_active_member(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if membership.role_key not in {
            WORKSPACE_ROLE_OWNER,
            WORKSPACE_ROLE_ADMIN,
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Workspace OWNER or ADMIN "
                    "role required."
                ),
            )

        return membership

    async def get_my_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership:
        return await self.require_active_member(
            workspace_id=workspace_id,
            user_id=user_id,
        )

    async def list_members(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[
        WorkspaceMembership
    ]:
        await self.require_active_member(
            workspace_id=workspace_id,
            user_id=user_id,
        )

        return (
            await self.repository
            .list_for_workspace(
                workspace_id=workspace_id
            )
        )

    @staticmethod
    def role_value(
        role: WorkspaceMembershipRole,
    ) -> str:
        return role.value

    async def add_member(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role: WorkspaceMembershipRole,
    ) -> WorkspaceMembership:
        actor = (
            await self.require_manager(
                workspace_id=workspace_id,
                user_id=actor_user_id,
            )
        )

        role_value = self.role_value(
            role
        )

        if (
            role_value
            == WORKSPACE_ROLE_OWNER
            and actor.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only an OWNER can assign "
                    "the OWNER role."
                ),
            )

        existing = (
            await self.repository
            .get_for_user(
                workspace_id=workspace_id,
                user_id=target_user_id,
            )
        )

        if existing is not None:
            if (
                existing.status
                != MEMBERSHIP_STATUS_REMOVED
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "User already has a "
                        "workspace membership."
                    ),
                )

            existing.status = (
                MEMBERSHIP_STATUS_ACTIVE
            )

            existing.role_key = (
                role_value
            )

            existing.invited_by_user_id = (
                actor_user_id
            )

            existing.invited_at = utcnow()
            existing.joined_at = utcnow()

            existing.suspended_at = None
            existing.removed_at = None

            await self.session.commit()
            await self.session.refresh(
                existing
            )

            return existing

        membership = WorkspaceMembership(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=target_user_id,
            role_key=role_value,
            status=MEMBERSHIP_STATUS_ACTIVE,
            invited_by_user_id=(
                actor_user_id
            ),
            invited_at=utcnow(),
            joined_at=utcnow(),
            suspended_at=None,
            removed_at=None,
        )

        await self.repository.add(
            membership
        )

        await self.session.commit()
        await self.session.refresh(
            membership
        )

        return membership

    async def update_role(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role: WorkspaceMembershipRole,
    ) -> WorkspaceMembership:
        actor = (
            await self.require_manager(
                workspace_id=workspace_id,
                user_id=actor_user_id,
            )
        )

        target = (
            await self.repository
            .get_for_user(
                workspace_id=workspace_id,
                user_id=target_user_id,
            )
        )

        if (
            target is None
            or target.status
            == MEMBERSHIP_STATUS_REMOVED
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Workspace membership "
                    "not found."
                ),
            )

        role_value = self.role_value(
            role
        )

        if (
            target.role_key
            == WORKSPACE_ROLE_OWNER
            and actor.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "ADMIN cannot modify "
                    "an OWNER."
                ),
            )

        if (
            role_value
            == WORKSPACE_ROLE_OWNER
            and actor.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only OWNER can assign "
                    "OWNER role."
                ),
            )

        if (
            target.user_id
            == actor_user_id
            and target.role_key
            == WORKSPACE_ROLE_OWNER
            and role_value
            != WORKSPACE_ROLE_OWNER
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "OWNER cannot demote "
                    "their own membership."
                ),
            )

        target.role_key = role_value

        await self.session.commit()
        await self.session.refresh(
            target
        )

        return target

    async def remove_member(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> WorkspaceMembership:
        actor = (
            await self.require_manager(
                workspace_id=workspace_id,
                user_id=actor_user_id,
            )
        )

        target = (
            await self.repository
            .get_for_user(
                workspace_id=workspace_id,
                user_id=target_user_id,
            )
        )

        if (
            target is None
            or target.status
            == MEMBERSHIP_STATUS_REMOVED
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Workspace membership "
                    "not found."
                ),
            )

        if (
            target.role_key
            == WORKSPACE_ROLE_OWNER
            and actor.role_key
            != WORKSPACE_ROLE_OWNER
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "ADMIN cannot remove "
                    "an OWNER."
                ),
            )

        if (
            target.user_id
            == actor_user_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "You cannot remove your own "
                    "workspace membership."
                ),
            )

        target.status = (
            MEMBERSHIP_STATUS_REMOVED
        )

        target.removed_at = utcnow()

        await self.session.commit()
        await self.session.refresh(
            target
        )

        return target

__all__ = [
    "MANAGER_ROLES",
    "WORKSPACE_ADMIN_ROLES",
    "WorkspaceMembershipService",
]