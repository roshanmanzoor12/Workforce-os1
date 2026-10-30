from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    select,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from .enums import (
    WorkspaceChannelMessageType,
    WorkspaceChannelRole,
    WorkspaceChannelType,
)
from .models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
    WorkspaceChannelMessage,
)


class WorkspaceChannelRepository:
    async def workspace_owned_by_user(
        self,
        session: AsyncSession,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        result = await session.execute(
            text(
                """
                SELECT 1
                FROM workspaces
                WHERE id = :workspace_id
                  AND created_by_user_id = :user_id
                LIMIT 1
                """
            ),
            {
                "workspace_id": workspace_id,
                "user_id": user_id,
            },
        )

        return (
            result.first()
            is not None
        )

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

        return result.scalar_one_or_none()

    async def get_by_slug(
        self,
        session: AsyncSession,
        *,
        workspace_id: uuid.UUID,
        slug: str,
    ) -> WorkspaceChannel | None:
        result = await session.execute(
            select(
                WorkspaceChannel
            ).where(
                WorkspaceChannel.workspace_id
                == workspace_id,
                WorkspaceChannel.slug
                == slug,
            )
        )

        return result.scalar_one_or_none()

    async def create_channel(
        self,
        session: AsyncSession,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        slug: str,
        channel_type: WorkspaceChannelType,
    ) -> WorkspaceChannel:
        channel = WorkspaceChannel(
            workspace_id=workspace_id,
            name=name,
            slug=slug,
            channel_type=channel_type,
            created_by_user_id=user_id,
        )

        session.add(
            channel
        )

        await session.flush()

        return channel

    async def add_owner(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelMember:
        member = WorkspaceChannelMember(
            channel_id=channel_id,
            user_id=user_id,
            role=WorkspaceChannelRole.OWNER,
        )

        session.add(
            member
        )

        await session.flush()

        return member

    async def get_member(
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
                WorkspaceChannelMember.channel_id
                == channel_id,
                WorkspaceChannelMember.user_id
                == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_user(
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
                WorkspaceChannelMember.channel_id
                == WorkspaceChannel.id,
            )
            .where(
                WorkspaceChannel.workspace_id
                == workspace_id,
                WorkspaceChannel.is_active.is_(
                    True
                ),
                WorkspaceChannelMember.user_id
                == user_id,
                WorkspaceChannelMember.left_at.is_(
                    None
                ),
            )
            .order_by(
                WorkspaceChannel.created_at.asc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def create_message(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        content: str,
    ) -> WorkspaceChannelMessage:
        message = WorkspaceChannelMessage(
            channel_id=channel_id,
            sender_user_id=sender_user_id,
            message_type=(
                WorkspaceChannelMessageType.TEXT
            ),
            content=content,
        )

        session.add(
            message
        )

        await session.flush()

        return message

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
                WorkspaceChannelMessage.channel_id
                == channel_id,
            )
        )

        return result.scalar_one_or_none()

    async def update_message(
        self,
        session: AsyncSession,
        *,
        message: WorkspaceChannelMessage,
        content: str,
        edited_at: datetime,
    ) -> WorkspaceChannelMessage:
        message.content = content
        message.edited_at = edited_at

        await session.flush()

        return message

    async def delete_message(
        self,
        session: AsyncSession,
        *,
        message: WorkspaceChannelMessage,
        deleted_at: datetime,
    ) -> WorkspaceChannelMessage:
        message.deleted_at = deleted_at

        await session.flush()

        return message

    async def list_messages(
        self,
        session: AsyncSession,
        *,
        channel_id: uuid.UUID,
        limit: int,
    ) -> list[
        WorkspaceChannelMessage
    ]:
        safe_limit = max(
            1,
            min(
                int(
                    limit
                ),
                100,
            ),
        )

        result = await session.execute(
            select(
                WorkspaceChannelMessage
            )
            .where(
                WorkspaceChannelMessage.channel_id
                == channel_id,
                WorkspaceChannelMessage.deleted_at.is_(
                    None
                ),
            )
            .order_by(
                WorkspaceChannelMessage.created_at.desc(),
                WorkspaceChannelMessage.id.desc(),
            )
            .limit(
                safe_limit
            )
        )

        rows = list(
            result.scalars().all()
        )

        rows.reverse()

        return rows

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
                WorkspaceChannelMessage.channel_id
                == channel_id,
            )
        )

        return result.scalar_one_or_none()

    async def update_message(
        self,
        session: AsyncSession,
        *,
        message: WorkspaceChannelMessage,
        content: str,
        edited_at: datetime,
    ) -> WorkspaceChannelMessage:
        message.content = content
        message.edited_at = edited_at

        await session.flush()

        return message

    async def delete_message(
        self,
        session: AsyncSession,
        *,
        message: WorkspaceChannelMessage,
        deleted_at: datetime,
    ) -> WorkspaceChannelMessage:
        message.deleted_at = deleted_at

        await session.flush()

        return message
    
__all__ = [
    "WorkspaceChannelRepository",
]