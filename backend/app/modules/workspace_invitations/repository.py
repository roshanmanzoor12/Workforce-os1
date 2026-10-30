from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import (
    Column,
    MetaData,
    String,
    Table,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.auth.models import User
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)


# Match the existing personal Calling Number table; do not allocate numbers
# or require the user to share their email with the inviter.
_calling_numbers = Table(
    "personal_call_numbers_v1",
    MetaData(),
    Column("user_id", PG_UUID(as_uuid=True), primary_key=True),
    Column("calling_number", String(10), nullable=False),
)


class WorkspaceInvitationRepository:
    """
    Control-plane persistence for workspace invitations.

    This repository intentionally operates only against
    workforce_control.

    Tenant-local employee / department / team UUIDs are stored
    as logical references on WorkspaceInvitation and are never
    joined from this repository.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # WORKSPACE
    # =====================================================

    async def get_workspace(
        self,
        workspace_id: uuid.UUID,
    ) -> Workspace | None:
        result = await self.session.execute(
            select(
                Workspace
            ).where(
                Workspace.id
                == workspace_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # USERS
    # =====================================================

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(
                User
            ).where(
                func.lower(
                    User.email
                )
                == email.lower()
            )
        )

        return result.scalar_one_or_none()

    async def resolve_invitee(self, identifier: str) -> User | None:
        value = identifier.strip().removeprefix("@").lower()
        try:
            target_id = uuid.UUID(value)
        except ValueError:
            target_id = None
        if target_id is None and len(value) == 10 and value.isascii() and value.isdecimal():
            statement = (
                select(User)
                .join(_calling_numbers, _calling_numbers.c.user_id == User.id)
                .where(_calling_numbers.c.calling_number == value)
            )
        else:
            condition = (User.id == target_id) if target_id else (func.lower(User.username) == value)
            statement = select(User).where(condition)

        result = await self.session.execute(
            statement.where(
                User.is_active.is_(True),
                User.is_locked.is_(False),
                User.is_email_verified.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_incoming(self, user: User) -> list[WorkspaceInvitation]:
        result = await self.session.execute(
            select(WorkspaceInvitation).where(
                WorkspaceInvitation.status == "pending",
                WorkspaceInvitation.expires_at > datetime.now().astimezone(),
                func.lower(WorkspaceInvitation.email) == user.email.lower(),
            ).order_by(WorkspaceInvitation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_incoming_by_id(self, invitation_id: uuid.UUID, user: User) -> WorkspaceInvitation | None:
        result = await self.session.execute(
            select(WorkspaceInvitation).where(
                WorkspaceInvitation.id == invitation_id,
                func.lower(WorkspaceInvitation.email) == user.email.lower(),
            )
        )
        return result.scalar_one_or_none()

    # =====================================================
    # MEMBERSHIPS
    # =====================================================

    async def get_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_membership(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        result = await self.session.execute(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE,
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
        invited_by_user_id: (
            uuid.UUID | None
        ),
        invited_at: datetime | None,
        joined_at: datetime | None,
    ) -> WorkspaceMembership:
        membership = WorkspaceMembership(
            workspace_id=workspace_id,
            user_id=user_id,
            role_key=role_key,
            status=status,
            invited_by_user_id=(
                invited_by_user_id
            ),
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

    # =====================================================
    # INVITATIONS
    # =====================================================

    async def get_by_id(
        self,
        *,
        workspace_id: uuid.UUID,
        invitation_id: uuid.UUID,
    ) -> WorkspaceInvitation | None:
        result = await self.session.execute(
            select(
                WorkspaceInvitation
            ).where(
                WorkspaceInvitation.workspace_id
                == workspace_id,
                WorkspaceInvitation.id
                == invitation_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> WorkspaceInvitation | None:
        result = await self.session.execute(
            select(
                WorkspaceInvitation
            ).where(
                WorkspaceInvitation.token_hash
                == token_hash
            )
        )

        return result.scalar_one_or_none()

    async def get_pending_for_email(
        self,
        *,
        workspace_id: uuid.UUID,
        email: str,
    ) -> WorkspaceInvitation | None:
        result = await self.session.execute(
            select(
                WorkspaceInvitation
            )
            .where(
                WorkspaceInvitation.workspace_id
                == workspace_id,
                func.lower(
                    WorkspaceInvitation.email
                )
                == email.lower(),
                WorkspaceInvitation.status
                == "pending",
            )
            .order_by(
                WorkspaceInvitation
                .created_at
                .desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def list_for_workspace(
        self,
        workspace_id: uuid.UUID,
    ) -> Sequence[
        WorkspaceInvitation
    ]:
        result = await self.session.execute(
            select(
                WorkspaceInvitation
            )
            .where(
                WorkspaceInvitation.workspace_id
                == workspace_id
            )
            .order_by(
                WorkspaceInvitation
                .created_at
                .desc()
            )
        )

        return result.scalars().all()

    async def create(
        self,
        *,
        workspace_id: uuid.UUID,
        employee_id: uuid.UUID | None,
        email: str,
        invited_user_id: uuid.UUID | None,
        role_key: str,
        department_id: uuid.UUID | None,
        team_id: uuid.UUID | None,
        manager_membership_id: (
            uuid.UUID | None
        ),
        invited_by_user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> WorkspaceInvitation:
        invitation = WorkspaceInvitation(
            workspace_id=workspace_id,
            employee_id=employee_id,
            email=email,
            invited_user_id=(
                invited_user_id
            ),
            role_key=role_key,
            department_id=department_id,
            team_id=team_id,
            manager_membership_id=(
                manager_membership_id
            ),
            invited_by_user_id=(
                invited_by_user_id
            ),
            token_hash=token_hash,
            status="pending",
            expires_at=expires_at,
        )

        self.session.add(
            invitation
        )

        await self.session.flush()

        await self.session.refresh(
            invitation
        )

        return invitation

    async def mark_accepted(
        self,
        invitation: WorkspaceInvitation,
        *,
        user_id: uuid.UUID,
        accepted_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.status = "accepted"

        invitation.invited_user_id = (
            user_id
        )

        invitation.accepted_at = (
            accepted_at
        )

        await self.session.flush()

        return invitation

    async def mark_declined(
        self,
        invitation: WorkspaceInvitation,
        *,
        declined_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.status = "declined"

        invitation.declined_at = (
            declined_at
        )

        await self.session.flush()

        return invitation

    async def mark_expired(
        self,
        invitation: WorkspaceInvitation,
    ) -> WorkspaceInvitation:
        invitation.status = "expired"

        await self.session.flush()

        return invitation

    async def mark_revoked(
        self,
        invitation: WorkspaceInvitation,
        *,
        revoked_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.status = "revoked"

        invitation.revoked_at = (
            revoked_at
        )

        await self.session.flush()

        return invitation

    async def rotate_token(
        self,
        invitation: WorkspaceInvitation,
        *,
        token_hash: str,
        expires_at: datetime,
    ) -> WorkspaceInvitation:
        invitation.token_hash = (
            token_hash
        )

        invitation.expires_at = (
            expires_at
        )

        invitation.status = "pending"

        invitation.accepted_at = None
        invitation.declined_at = None
        invitation.revoked_at = None

        await self.session.flush()

        return invitation


__all__ = [
    "WorkspaceInvitationRepository",
]
