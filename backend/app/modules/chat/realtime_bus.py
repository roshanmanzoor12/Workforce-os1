from __future__ import annotations

from typing import (
    Any,
    Protocol,
)

from .realtime_events import (
    ChatRealtimeEvent,
    deserialize_event,
    serialize_event,
)


CHAT_REALTIME_CHANNEL = (
    "workforceos:chat:events:v1"
)


class RedisPublisherProtocol(
    Protocol
):
    async def publish(
        self,
        channel: str,
        message: str,
    ) -> Any:
        ...


class ChatRealtimeBus:
    def __init__(
        self,
        redis_client: RedisPublisherProtocol,
        *,
        channel: str = CHAT_REALTIME_CHANNEL,
    ) -> None:
        self.redis_client = redis_client
        self.channel = channel

    async def publish(
        self,
        event: ChatRealtimeEvent,
    ) -> int:
        payload = serialize_event(
            event
        )

        result = await self.redis_client.publish(
            self.channel,
            payload,
        )

        return int(
            result
        )

    @staticmethod
    def decode(
        payload: str | bytes,
    ) -> ChatRealtimeEvent:
        return deserialize_event(
            payload
        )


__all__ = [
    "CHAT_REALTIME_CHANNEL",
    "ChatRealtimeBus",
    "RedisPublisherProtocol",
]