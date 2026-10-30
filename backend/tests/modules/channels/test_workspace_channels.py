from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

import pytest

from app.modules.channels.enums import (
    WorkspaceChannelRole,
    WorkspaceChannelType,
)
from app.modules.channels.schemas import (
    make_channel_slug,
)
from app.modules.channels.service import (
    WorkspaceChannelPermissionError,
    WorkspaceChannelService,
)


def test_channel_slug_normalization():
    assert (
        make_channel_slug(
            "Engineering Team"
        )
        == "engineering-team"
    )

    assert (
        make_channel_slug(
            "  Product & Design! "
        )
        == "product-design"
    )


class FakeSession:
    async def flush(
        self,
    ):
        return None


class FakeChannel:
    def __init__(
        self,
        *,
        workspace_id,
        user_id,
        name,
        slug,
        channel_type,
    ):
        self.id = uuid.uuid4()

        self.workspace_id = workspace_id

        self.created_by_user_id = user_id

        self.name = name
        self.slug = slug

        self.channel_type = channel_type

        self.is_active = True

        self.created_at = datetime.now(
            timezone.utc
        )

        self.updated_at = datetime.now(
            timezone.utc
        )


class FakeMember:
    def __init__(
        self,
        *,
        role=WorkspaceChannelRole.OWNER,
    ):
        self.role = role
        self.left_at = None


class FakeRepository:
    def __init__(
        self,
        *,
        owned=True,
    ):
        self.owned = owned

        self.channel = None
        self.member = None

        self.messages = []

    async def workspace_owned_by_user(
        self,
        session,
        *,
        workspace_id,
        user_id,
    ):
        return self.owned

    async def get_by_slug(
        self,
        session,
        *,
        workspace_id,
        slug,
    ):
        if (
            self.channel is not None
            and self.channel.slug == slug
        ):
            return self.channel

        return None

    async def create_channel(
        self,
        session,
        *,
        workspace_id,
        user_id,
        name,
        slug,
        channel_type,
    ):
        self.channel = FakeChannel(
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            slug=slug,
            channel_type=channel_type,
        )

        return self.channel

    async def add_owner(
        self,
        session,
        *,
        channel_id,
        user_id,
    ):
        self.member = FakeMember()

        return self.member

    async def get_channel(
        self,
        session,
        *,
        channel_id,
    ):
        return self.channel

    async def get_member(
        self,
        session,
        *,
        channel_id,
        user_id,
    ):
        return self.member

    async def list_for_user(
        self,
        session,
        *,
        workspace_id,
        user_id,
    ):
        if self.channel is None:
            return []

        return [
            self.channel
        ]

    async def create_message(
        self,
        session,
        *,
        channel_id,
        sender_user_id,
        content,
    ):
        message = type(
            "FakeMessage",
            (),
            {},
        )()

        message.id = uuid.uuid4()
        message.channel_id = channel_id
        message.sender_user_id = (
            sender_user_id
        )
        message.content = content

        self.messages.append(
            message
        )

        return message

    async def list_messages(
        self,
        session,
        *,
        channel_id,
        limit,
    ):
        return self.messages[
            -limit:
        ]


@pytest.mark.asyncio
async def test_workspace_owner_creates_channel():
    repository = FakeRepository(
        owned=True
    )

    service = WorkspaceChannelService(
        FakeSession(),
        repository=repository,
    )

    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    channel = await service.create_channel(
        workspace_id=workspace_id,
        user_id=user_id,
        name="Engineering",
        channel_type=(
            WorkspaceChannelType.TEXT
        ),
    )

    assert channel.workspace_id == workspace_id

    assert (
        channel.slug
        == "engineering"
    )

    assert repository.member is not None

    assert (
        repository.member.role
        == WorkspaceChannelRole.OWNER
    )


@pytest.mark.asyncio
async def test_non_owner_cannot_create_channel():
    service = WorkspaceChannelService(
        FakeSession(),
        repository=FakeRepository(
            owned=False
        ),
    )

    with pytest.raises(
        WorkspaceChannelPermissionError
    ):
        await service.create_channel(
            workspace_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Private",
            channel_type=(
                WorkspaceChannelType.TEXT
            ),
        )


@pytest.mark.asyncio
async def test_channel_message_requires_member():
    repository = FakeRepository(
        owned=True
    )

    service = WorkspaceChannelService(
        FakeSession(),
        repository=repository,
    )

    user_id = uuid.uuid4()

    channel = await service.create_channel(
        workspace_id=uuid.uuid4(),
        user_id=user_id,
        name="General",
        channel_type=(
            WorkspaceChannelType.TEXT
        ),
    )

    repository.member = None

    with pytest.raises(
        WorkspaceChannelPermissionError
    ):
        await service.send_message(
            channel_id=channel.id,
            user_id=user_id,
            content="hello",
        )


@pytest.mark.asyncio
async def test_owner_can_send_channel_message():
    repository = FakeRepository(
        owned=True
    )

    service = WorkspaceChannelService(
        FakeSession(),
        repository=repository,
    )

    user_id = uuid.uuid4()

    channel = await service.create_channel(
        workspace_id=uuid.uuid4(),
        user_id=user_id,
        name="General",
        channel_type=(
            WorkspaceChannelType.TEXT
        ),
    )

    message = await service.send_message(
        channel_id=channel.id,
        user_id=user_id,
        content="hello",
    )

    assert message.content == "hello"