from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
)


class ChannelAttachmentAccessGuard:
    """
    Correct channel membership check for the attachment module.

    WorkspaceChannelMember has a `left_at` lifecycle field rather than
    an `is_active` column.  The old attachment implementation referenced
    WorkspaceChannelMember.is_active, which can fail at runtime.

    This helper provides one canonical query for attachment access.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def is_allowed(
        self,
        *,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                WorkspaceChannelMember.id
            )
            .join(
                WorkspaceChannel,
                (
                    WorkspaceChannel.id
                    ==
                    WorkspaceChannelMember.channel_id
                ),
            )
            .where(
                WorkspaceChannelMember.channel_id
                == channel_id,

                WorkspaceChannelMember.user_id
                == user_id,

                WorkspaceChannelMember.left_at
                .is_(
                    None
                ),

                WorkspaceChannel.is_active
                .is_(
                    True
                ),
            )
            .limit(
                1
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    async def assert_allowed(
        self,
        *,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> None:
        allowed = await self.is_allowed(
            user_id=user_id,
            channel_id=channel_id,
        )

        if not allowed:
            raise PermissionError(
                "Active channel membership is required "
                "for attachment access."
            )