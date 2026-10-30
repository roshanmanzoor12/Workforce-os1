from __future__ import annotations

import uuid

import pytest

from app.modules.chat.realtime_presence import (
    RealtimePresenceTracker,
)
from app.modules.chat.realtime_publish_service import (
    ChatRealtimePublishService,
)
from app.modules.chat.realtime_enums import (
    ChatRealtimeEventType,
)
from app.modules.chat.typing_command_service import (
    TypingCommandService,
)


class FakePresenceRedis:
    def __init__(
        self,
    ):
        self.values = {}

    async def set(
        self,
        name,
        value,
        *,
        ex,
    ):
        self.values[
            name
        ] = value

        return True

    async def get(
        self,
        name,
    ):
        return self.values.get(
            name
        )

    async def delete(
        self,
        *names,
    ):
        removed = 0

        for name in names:
            if name in self.values:
                del self.values[
                    name
                ]

                removed += 1

        return removed


@pytest.mark.asyncio
async def test_presence_heartbeat_online_offline():
    redis_client = FakePresenceRedis()

    tracker = RealtimePresenceTracker(
        redis_client
    )

    user_id = uuid.uuid4()

    await tracker.heartbeat(
        user_id=user_id
    )

    assert await tracker.is_online(
        user_id=user_id
    )

    await tracker.mark_offline(
        user_id=user_id
    )

    assert not await tracker.is_online(
        user_id=user_id
    )


class FakeBus:
    def __init__(
        self,
    ):
        self.events = []

    async def publish(
        self,
        event,
    ):
        self.events.append(
            event
        )

        return 1


@pytest.mark.asyncio
async def test_publish_service_message_event():
    bus = FakeBus()

    publisher = (
        ChatRealtimePublishService(
            bus=bus
        )
    )

    conversation_id = uuid.uuid4()
    actor_user_id = uuid.uuid4()

    result = await publisher.typing_started(
        conversation_id=(
            conversation_id
        ),
        actor_user_id=actor_user_id,
    )

    assert result is True

    assert len(
        bus.events
    ) == 1

    assert (
        bus.events[0].event_type
        == ChatRealtimeEventType.TYPING_STARTED
    )

    assert (
        bus.events[0].conversation_id
        == conversation_id
    )


class FailingBus:
    async def publish(
        self,
        event,
    ):
        raise RuntimeError(
            "Redis unavailable"
        )


@pytest.mark.asyncio
async def test_publish_is_best_effort():
    publisher = (
        ChatRealtimePublishService(
            bus=FailingBus()
        )
    )

    result = await publisher.presence_updated(
        actor_user_id=uuid.uuid4(),
        online=True,
    )

    assert result is False


class FakeConversation:
    is_active = True


class FakeMember:
    left_at = None


class FakeChatRepository:
    async def get_conversation(
        self,
        session,
        *,
        conversation_id,
    ):
        return FakeConversation()

    async def get_member(
        self,
        session,
        *,
        conversation_id,
        user_id,
    ):
        return FakeMember()


class FakeTypingService:
    def __init__(
        self,
    ):
        self.users = set()

    async def start_typing(
        self,
        *,
        conversation_id,
        user_id,
    ):
        self.users.add(
            user_id
        )

    async def stop_typing(
        self,
        *,
        conversation_id,
        user_id,
    ):
        self.users.discard(
            user_id
        )

    async def list_typing_users(
        self,
        *,
        conversation_id,
    ):
        return list(
            self.users
        )


class FakePublisher:
    async def typing_started(
        self,
        *,
        conversation_id,
        actor_user_id,
    ):
        return True

    async def typing_stopped(
        self,
        *,
        conversation_id,
        actor_user_id,
    ):
        return True


class FakeSession:
    pass


@pytest.mark.asyncio
async def test_typing_command_membership_flow():
    typing_service = (
        FakeTypingService()
    )

    service = TypingCommandService(
        FakeSession(),
        typing_service=typing_service,
        chat_repository=(
            FakeChatRepository()
        ),
        publisher=FakePublisher(),
    )

    conversation_id = uuid.uuid4()
    user_id = uuid.uuid4()

    await service.start(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    users = await service.list_users(
        conversation_id=conversation_id,
        user_id=uuid.uuid4(),
    )

    assert user_id in users

    await service.stop(
        conversation_id=conversation_id,
        user_id=user_id,
    )

    users = await service.list_users(
        conversation_id=conversation_id,
        user_id=uuid.uuid4(),
    )

    assert user_id not in users