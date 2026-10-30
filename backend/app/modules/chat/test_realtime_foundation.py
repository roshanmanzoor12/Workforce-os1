from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

import pytest

from app.modules.chat.pagination import (
    decode_message_cursor,
    encode_message_cursor,
)
from app.modules.chat.realtime_bus import (
    CHAT_REALTIME_CHANNEL,
    ChatRealtimeBus,
)
from app.modules.chat.realtime_enums import (
    ChatRealtimeEventType,
)
from app.modules.chat.realtime_events import (
    ChatRealtimeEvent,
)
from app.modules.chat.typing_service import (
    TypingService,
)


def test_message_cursor_round_trip():
    created_at = datetime.now(
        timezone.utc
    )

    message_id = uuid.uuid4()

    encoded = encode_message_cursor(
        created_at=created_at,
        message_id=message_id,
    )

    decoded = decode_message_cursor(
        encoded
    )

    assert (
        decoded.message_id
        == message_id
    )

    assert (
        decoded.created_at
        == created_at
    )


def test_invalid_cursor_rejected():
    with pytest.raises(
        ValueError,
        match="Invalid message cursor",
    ):
        decode_message_cursor(
            "not-a-valid-cursor"
        )


def test_realtime_event_round_trip():
    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = ChatRealtimeEvent(
        event_type=(
            ChatRealtimeEventType
            .MESSAGE_CREATED
        ),
        conversation_id=conversation_id,
        actor_user_id=user_id,
        data={
            "message_id": str(
                uuid.uuid4()
            ),
        },
    )

    restored = (
        ChatRealtimeEvent.from_json(
            event.to_json()
        )
    )

    assert (
        restored.event_id
        == event.event_id
    )

    assert (
        restored.event_type
        == event.event_type
    )

    assert (
        restored.conversation_id
        == conversation_id
    )


class FakePublisher:
    def __init__(
        self,
    ):
        self.channel = None
        self.message = None

    async def publish(
        self,
        channel,
        message,
    ):
        self.channel = channel
        self.message = message

        return 3


@pytest.mark.asyncio
async def test_realtime_bus_publishes_event():
    redis_client = FakePublisher()

    bus = ChatRealtimeBus(
        redis_client
    )

    event = ChatRealtimeEvent(
        event_type=(
            ChatRealtimeEventType
            .PRESENCE_UPDATED
        ),
        actor_user_id=uuid.uuid4(),
    )

    subscribers = await bus.publish(
        event
    )

    assert subscribers == 3

    assert (
        redis_client.channel
        == CHAT_REALTIME_CHANNEL
    )

    decoded = bus.decode(
        redis_client.message
    )

    assert (
        decoded.event_id
        == event.event_id
    )


class FakeTypingRedis:
    def __init__(
        self,
    ):
        self.values = {}

    async def zadd(
        self,
        name,
        mapping,
    ):
        bucket = self.values.setdefault(
            name,
            {}
        )

        bucket.update(
            mapping
        )

        return len(
            mapping
        )

    async def zrem(
        self,
        name,
        *values,
    ):
        bucket = self.values.setdefault(
            name,
            {}
        )

        removed = 0

        for value in values:
            if value in bucket:
                del bucket[
                    value
                ]

                removed += 1

        return removed

    async def zremrangebyscore(
        self,
        name,
        min,
        max,
    ):
        bucket = self.values.setdefault(
            name,
            {}
        )

        maximum = float(
            max
        )

        expired = [
            key
            for key, score
            in bucket.items()
            if score <= maximum
        ]

        for key in expired:
            del bucket[
                key
            ]

        return len(
            expired
        )

    async def zrangebyscore(
        self,
        name,
        min,
        max,
    ):
        bucket = self.values.setdefault(
            name,
            {}
        )

        minimum = float(
            min
        )

        return [
            key
            for key, score
            in bucket.items()
            if score >= minimum
        ]

    async def expire(
        self,
        name,
        seconds,
    ):
        return True


@pytest.mark.asyncio
async def test_typing_start_and_stop():
    redis_client = (
        FakeTypingRedis()
    )

    service = TypingService(
        redis_client
    )

    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await service.start_typing(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    typing_users = (
        await service.list_typing_users(
            conversation_id=(
                conversation_id
            )
        )
    )

    assert user_id in typing_users

    await service.stop_typing(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    typing_users = (
        await service.list_typing_users(
            conversation_id=(
                conversation_id
            )
        )
    )

    assert user_id not in typing_users