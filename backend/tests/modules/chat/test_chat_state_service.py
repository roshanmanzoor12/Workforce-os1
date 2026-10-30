from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from app.modules.chat.enums import (
    PresenceStatus,
)
from app.modules.chat.service import (
    ChatPermissionError,
)
from app.modules.chat.state_service import (
    ChatStateService,
)


class FakeMessage:
    def __init__(
        self,
        *,
        sender_user_id,
        conversation_id,
    ):
        self.id = uuid.uuid4()
        self.sender_user_id = sender_user_id
        self.conversation_id = conversation_id
        self.content = "hello"
        self.edited_at = None
        self.deleted_at = None


class FakeMember:
    def __init__(
        self,
    ):
        self.left_at = None


class FakeConversation:
    def __init__(
        self,
    ):
        self.is_active = True


class FakePresence:
    def __init__(
        self,
        user_id,
    ):
        self.user_id = user_id
        self.status = PresenceStatus.OFFLINE
        self.last_seen_at = datetime.now()
        self.updated_at = datetime.now()


class FakeSession:
    async def flush(
        self,
    ):
        return None


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


class FakeStateRepository:
    def __init__(
        self,
        message,
    ):
        self.message = message
        self.presence = {}

    async def get_message(
        self,
        session,
        *,
        message_id,
    ):
        return self.message

    async def ensure_presence(
        self,
        session,
        *,
        user_id,
    ):
        if user_id not in self.presence:
            self.presence[user_id] = (
                FakePresence(
                    user_id
                )
            )

        return self.presence[
            user_id
        ]


class FakeFriendshipService:
    def __init__(
        self,
        allowed=True,
    ):
        self.allowed = allowed

    async def are_friends(
        self,
        *,
        first_user_id,
        second_user_id,
    ):
        return self.allowed


@pytest.mark.asyncio
async def test_sender_can_edit_message():
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    message = FakeMessage(
        sender_user_id=user_id,
        conversation_id=conversation_id,
    )

    service = ChatStateService(
        FakeSession(),
        repository=FakeStateRepository(
            message
        ),
        chat_repository=FakeChatRepository(),
        friendship_service=(
            FakeFriendshipService()
        ),
    )

    result = await service.edit_message(
        conversation_id=conversation_id,
        message_id=message.id,
        user_id=user_id,
        content="updated",
    )

    assert result.content == "updated"
    assert result.edited_at is not None


@pytest.mark.asyncio
async def test_other_user_cannot_edit_message():
    sender_id = uuid.uuid4()
    other_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    message = FakeMessage(
        sender_user_id=sender_id,
        conversation_id=conversation_id,
    )

    service = ChatStateService(
        FakeSession(),
        repository=FakeStateRepository(
            message
        ),
        chat_repository=FakeChatRepository(),
        friendship_service=(
            FakeFriendshipService()
        ),
    )

    with pytest.raises(
        ChatPermissionError,
    ):
        await service.edit_message(
            conversation_id=conversation_id,
            message_id=message.id,
            user_id=other_id,
            content="hack",
        )


@pytest.mark.asyncio
async def test_delete_is_soft_delete():
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    message = FakeMessage(
        sender_user_id=user_id,
        conversation_id=conversation_id,
    )

    service = ChatStateService(
        FakeSession(),
        repository=FakeStateRepository(
            message
        ),
        chat_repository=FakeChatRepository(),
        friendship_service=(
            FakeFriendshipService()
        ),
    )

    result = await service.delete_message(
        conversation_id=conversation_id,
        message_id=message.id,
        user_id=user_id,
    )

    assert result.deleted_at is not None
    assert result.content == ""


@pytest.mark.asyncio
async def test_presence_can_be_updated():
    user_id = uuid.uuid4()

    message = FakeMessage(
        sender_user_id=user_id,
        conversation_id=uuid.uuid4(),
    )

    repository = FakeStateRepository(
        message
    )

    service = ChatStateService(
        FakeSession(),
        repository=repository,
        chat_repository=FakeChatRepository(),
        friendship_service=(
            FakeFriendshipService()
        ),
    )

    result = await service.set_presence(
        user_id=user_id,
        status=PresenceStatus.ONLINE,
    )

    assert (
        result.status
        == PresenceStatus.ONLINE
    )


@pytest.mark.asyncio
async def test_presence_hidden_from_non_friend():
    current_user_id = uuid.uuid4()
    target_user_id = uuid.uuid4()

    message = FakeMessage(
        sender_user_id=current_user_id,
        conversation_id=uuid.uuid4(),
    )

    service = ChatStateService(
        FakeSession(),
        repository=FakeStateRepository(
            message
        ),
        chat_repository=FakeChatRepository(),
        friendship_service=(
            FakeFriendshipService(
                allowed=False
            )
        ),
    )

    with pytest.raises(
        ChatPermissionError,
    ):
        await service.get_presence(
            current_user_id=current_user_id,
            target_user_id=target_user_id,
        )