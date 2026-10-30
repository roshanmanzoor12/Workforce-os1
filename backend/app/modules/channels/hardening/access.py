from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
)


class ChannelAccessDenied(
    PermissionError
):
    """
    Raised when a realtime connection no longer has valid channel access.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class ChannelAccessContext:
    workspace_id: uuid.UUID
    channel_id: uuid.UUID
    user_id: uuid.UUID

    channel_is_active: bool
    member_role: str | None


class ChannelAccessGuard:
    """
    Server-side realtime authorization guard.

    Websocket tickets are short-lived credentials, but channel access can
    change after ticket issuance.  Production websocket entry therefore
    needs a fresh database check before a connection is accepted.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_context(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChannelAccessContext:
        result = await self.session.execute(
            select(
                WorkspaceChannel,
                WorkspaceChannelMember,
            )
            .join(
                WorkspaceChannelMember,
                (
                    WorkspaceChannelMember.channel_id
                    == WorkspaceChannel.id
                ),
            )
            .where(
                WorkspaceChannel.id
                == channel_id,

                WorkspaceChannel.workspace_id
                == workspace_id,

                WorkspaceChannel.is_active
                .is_(
                    True
                ),

                WorkspaceChannelMember.user_id
                == user_id,

                WorkspaceChannelMember.left_at
                .is_(
                    None
                ),
            )
            .limit(
                1
            )
        )

        row = result.first()

        if row is None:
            raise ChannelAccessDenied(
                "Active channel membership is required."
            )

        channel = row[0]
        member = row[1]

        raw_role = getattr(
            member,
            "role",
            None,
        )

        if raw_role is None:
            member_role = None
        else:
            member_role = getattr(
                raw_role,
                "value",
                None,
            )

            if member_role is None:
                member_role = str(
                    raw_role
                )

        return ChannelAccessContext(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
            channel_is_active=bool(
                channel.is_active
            ),
            member_role=member_role,
        )

    async def assert_access(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ChannelAccessContext:
        return await self.get_context(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )

    async def has_access(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        try:
            await self.assert_access(
                workspace_id=workspace_id,
                channel_id=channel_id,
                user_id=user_id,
            )

        except ChannelAccessDenied:
            return False

        return True