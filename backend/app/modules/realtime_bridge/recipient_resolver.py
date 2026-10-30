from __future__ import annotations

import uuid

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.channels.models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
)
from app.modules.chat.models import (
    ConversationMember,
)


# =========================================================
# REALTIME RECIPIENT RESOLVER
# =========================================================


class RealtimeRecipientResolver:
    """
    Resolve authorized user IDs for realtime fanout.

    Important membership semantics:

    Workspace channel membership is active when:

        WorkspaceChannelMember.left_at IS NULL

    WorkspaceChannelMember does not expose an is_active
    boolean column.

    Conversation membership continues to use the native
    ConversationMember.is_active field.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CHANNEL USERS
    # =====================================================

    async def channel_users(
        self,
        *,
        channel_id: uuid.UUID,
    ) -> list[
        uuid.UUID
    ]:
        """
        Return active users for an active workspace channel.

        A channel user is eligible when:

            membership.channel_id == channel_id
            membership.left_at IS NULL
            workspace channel is_active == True
        """

        result = await self.session.execute(
            select(
                WorkspaceChannelMember.user_id
            )
            .join(
                WorkspaceChannel,
                WorkspaceChannel.id
                == WorkspaceChannelMember.channel_id,
            )
            .where(
                WorkspaceChannelMember.channel_id
                == channel_id,
                WorkspaceChannelMember.left_at.is_(
                    None
                ),
                WorkspaceChannel.is_active.is_(
                    True
                ),
            )
            .distinct()
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # CONVERSATION USERS
    # =====================================================

    async def conversation_users(
        self,
        *,
        conversation_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """
        Return users whose conversation membership is active.

        A membership is active when left_at is None.
        """

        result = await self.session.execute(
            select(
                ConversationMember.user_id
            ).where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.left_at.is_(
                    None
                ),
            ).distinct()
        )

        return list(
            result.scalars().all()
        )

# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "RealtimeRecipientResolver",
]