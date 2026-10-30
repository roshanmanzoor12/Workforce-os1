from __future__ import annotations

import uuid

from .chat_redis import (
    get_chat_redis,
)
from .models import (
    ChatMessage,
    ChatMessageReceipt,
)
from .realtime_bus import (
    ChatRealtimeBus,
)
from .realtime_enums import (
    ChatRealtimeEventType,
)
from .realtime_events import (
    ChatRealtimeEvent,
)


class ChatRealtimePublishService:
    def __init__(
        self,
        *,
        bus: ChatRealtimeBus | None = None,
    ) -> None:
        self.bus = (
            bus
            or ChatRealtimeBus(
                get_chat_redis()
            )
        )

    async def publish_best_effort(
        self,
        event: ChatRealtimeEvent,
    ) -> bool:
        try:
            await self.bus.publish(
                event
            )

            return True

        except Exception:
            return False

    async def message_created(
        self,
        *,
        message: ChatMessage,
        actor_user_id: uuid.UUID,
    ) -> bool:
        event = ChatRealtimeEvent(
            event_type=(
                ChatRealtimeEventType
                .MESSAGE_CREATED
            ),
            conversation_id=(
                message.conversation_id
            ),
            actor_user_id=actor_user_id,
            data={
                "message_id": str(
                    message.id
                ),
                "sender_user_id": str(
                    actor_user_id
                ),
                "message_type": (
                    message.message_type.value
                ),
                "content": message.content,
                "created_at": (
                    message.created_at.isoformat()
                ),
            },
        )

        return await self.publish_best_effort(
            event
        )

    async def message_updated(
        self,
        *,
        message: ChatMessage,
        actor_user_id: uuid.UUID,
    ) -> bool:
        event = ChatRealtimeEvent(
            event_type=(
                ChatRealtimeEventType
                .MESSAGE_UPDATED
            ),
            conversation_id=(
                message.conversation_id
            ),
            actor_user_id=actor_user_id,
            data={
                "message_id": str(
                    message.id
                ),
                "content": message.content,
                "edited_at": (
                    message.edited_at.isoformat()
                    if message.edited_at
                    else None
                ),
            },
        )

        return await self.publish_best_effort(
            event
        )

    async def message_deleted(
        self,
        *,
        message: ChatMessage,
        actor_user_id: uuid.UUID,
    ) -> bool:
        event = ChatRealtimeEvent(
            event_type=(
                ChatRealtimeEventType
                .MESSAGE_DELETED
            ),
            conversation_id=(
                message.conversation_id
            ),
            actor_user_id=actor_user_id,
            data={
                "message_id": str(
                    message.id
                ),
                "deleted_at": (
                    message.deleted_at.isoformat()
                    if message.deleted_at
                    else None
                ),
            },
        )

        return await self.publish_best_effort(
            event
        )

    async def message_read(
        self,
        *,
        conversation_id: uuid.UUID,
        receipt: ChatMessageReceipt,
        actor_user_id: uuid.UUID,
    ) -> bool:
        event = ChatRealtimeEvent(
            event_type=(
                ChatRealtimeEventType
                .MESSAGE_READ
            ),
            conversation_id=(
                conversation_id
            ),
            actor_user_id=actor_user_id,
            data={
                "message_id": str(
                    receipt.message_id
                ),
                "user_id": str(
                    receipt.user_id
                ),
                "read_at": (
                    receipt.read_at.isoformat()
                ),
            },
        )

        return await self.publish_best_effort(
            event
        )

    async def typing_started(
        self,
        *,
        conversation_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> bool:
        return await self.publish_best_effort(
            ChatRealtimeEvent(
                event_type=(
                    ChatRealtimeEventType
                    .TYPING_STARTED
                ),
                conversation_id=(
                    conversation_id
                ),
                actor_user_id=actor_user_id,
            )
        )

    async def typing_stopped(
        self,
        *,
        conversation_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> bool:
        return await self.publish_best_effort(
            ChatRealtimeEvent(
                event_type=(
                    ChatRealtimeEventType
                    .TYPING_STOPPED
                ),
                conversation_id=(
                    conversation_id
                ),
                actor_user_id=actor_user_id,
            )
        )

    async def presence_updated(
        self,
        *,
        actor_user_id: uuid.UUID,
        online: bool,
    ) -> bool:
        return await self.publish_best_effort(
            ChatRealtimeEvent(
                event_type=(
                    ChatRealtimeEventType
                    .PRESENCE_UPDATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                data={
                    "online": online,
                },
            )
        )


__all__ = [
    "ChatRealtimePublishService",
]