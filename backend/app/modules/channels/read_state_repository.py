from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from .hardening.read_state_upsert import (
    ChannelReadStateUpserter,
)
from .models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
    WorkspaceChannelMessage,
)
from .read_state_models import (
    WorkspaceChannelReadState,
)


class WorkspaceChannelReadStateRepository:
    async def get_channel(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
    ) -> WorkspaceChannel | None:
        result = await session.execute(
            select(
                WorkspaceChannel
            ).where(
                WorkspaceChannel.id
                == channel_id
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def get_active_member(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelMember | None:
        result = await session.execute(
            select(
                WorkspaceChannelMember
            ).where(
                WorkspaceChannelMember
                .channel_id
                == channel_id,
                WorkspaceChannelMember
                .user_id
                == user_id,
                WorkspaceChannelMember
                .left_at
                .is_(
                    None
                ),
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def get_message(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> WorkspaceChannelMessage | None:
        result = await session.execute(
            select(
                WorkspaceChannelMessage
            ).where(
                WorkspaceChannelMessage.id
                == message_id,
                WorkspaceChannelMessage
                .channel_id
                == channel_id,
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def get_state(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelReadState | None:
        result = await session.execute(
            select(
                WorkspaceChannelReadState
            ).where(
                WorkspaceChannelReadState
                .channel_id
                == channel_id,
                WorkspaceChannelReadState
                .user_id
                == user_id,
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def save_state(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        last_read_message_id:
            uuid.UUID | None,
        last_read_at: datetime,
    ) -> WorkspaceChannelReadState:
        """
        Atomic PostgreSQL UPSERT.

        Public signature remains compatible with Phase 16C.
        Workspace identity is resolved from the channel row instead of
        trusting caller-supplied workspace data.
        """

        channel = await self.get_channel(
            session,
            channel_id=channel_id,
        )

        if channel is None:
            raise LookupError(
                "Workspace channel not found."
            )

        upserter = (
            ChannelReadStateUpserter(
                session
            )
        )

        return await (
            upserter.upsert_and_flush(
                workspace_id=(
                    channel.workspace_id
                ),
                channel_id=channel_id,
                user_id=user_id,
                last_read_message_id=(
                    last_read_message_id
                ),
                read_at=last_read_at,
            )
        )

    async def latest_message(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
    ) -> WorkspaceChannelMessage | None:
        result = await session.execute(
            select(
                WorkspaceChannelMessage
            )
            .where(
                WorkspaceChannelMessage
                .channel_id
                == channel_id,
                WorkspaceChannelMessage
                .deleted_at
                .is_(
                    None
                ),
            )
            .order_by(
                WorkspaceChannelMessage
                .created_at
                .desc(),
            )
            .limit(
                1
            )
        )

        return (
            result.scalar_one_or_none()
        )

    async def unread_count(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        last_read_at:
            datetime | None,
    ) -> int:
        conditions = [
            (
                WorkspaceChannelMessage
                .channel_id
                == channel_id
            ),
            (
                WorkspaceChannelMessage
                .deleted_at
                .is_(
                    None
                )
            ),
            or_(
                WorkspaceChannelMessage
                .sender_user_id
                .is_(
                    None
                ),
                WorkspaceChannelMessage
                .sender_user_id
                != user_id,
            ),
        ]

        if last_read_at is not None:
            conditions.append(
                WorkspaceChannelMessage
                .created_at
                > last_read_at
            )

        result = await session.execute(
            select(
                func.count(
                    WorkspaceChannelMessage.id
                )
            ).where(
                *conditions
            )
        )

        return int(
            result.scalar_one()
        )

    async def list_active_channels(
        self,
        session: AsyncSession,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[
        WorkspaceChannel
    ]:
        result = await session.execute(
            select(
                WorkspaceChannel
            )
            .join(
                WorkspaceChannelMember,
                WorkspaceChannelMember
                .channel_id
                == WorkspaceChannel.id,
            )
            .where(
                WorkspaceChannel
                .workspace_id
                == workspace_id,
                WorkspaceChannel
                .is_active
                .is_(
                    True
                ),
                WorkspaceChannelMember
                .user_id
                == user_id,
                WorkspaceChannelMember
                .left_at
                .is_(
                    None
                ),
            )
            .order_by(
                WorkspaceChannel
                .created_at
                .asc()
            )
        )

        return list(
            result.scalars().all()
        )


__all__ = [
    "WorkspaceChannelReadStateRepository",
]