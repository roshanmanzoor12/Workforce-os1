from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.voice_channels.access import VoiceChannelAccess
from app.modules.voice_channels.models import (
    VOICE_PARTICIPANT_JOINED,
    VOICE_PARTICIPANT_LEFT,
)
from app.modules.voice_channels.service import (
    VoiceChannelPermissionError,
    VoiceChannelService,
)


def make_access(
    *,
    can_moderate: bool = False,
) -> VoiceChannelAccess:
    return VoiceChannelAccess(
        workspace_id=uuid.uuid4(),
        actor_user_id=uuid.uuid4(),
        permissions=frozenset(),
        can_read=True,
        can_moderate=can_moderate,
    )


def make_service() -> VoiceChannelService:
    # Execute the real service methods while replacing external I/O.
    service = object.__new__(VoiceChannelService)

    service.repository = SimpleNamespace(
        active_ban=AsyncMock(return_value=None),
        participant=AsyncMock(return_value=None),
    )

    service.require_voice_channel = AsyncMock()
    service._require_active_call = AsyncMock()
    service.publish = AsyncMock()

    return service


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        "moderator_state",
        "kick",
        "ban",
        "unban",
    ],
)
async def test_regular_member_cannot_moderate(
    operation: str,
) -> None:
    service = make_service()
    access = make_access()
    channel_id = uuid.uuid4()
    target_user_id = uuid.uuid4()

    arguments = {
        "access": access,
        "channel_id": channel_id,
        "user_id": target_user_id,
    }

    if operation == "moderator_state":
        arguments["payload"] = SimpleNamespace(
            server_muted=True,
            server_deafened=None,
        )

    if operation == "ban":
        arguments["reason"] = "Test moderation"

    with pytest.raises(VoiceChannelPermissionError):
        await getattr(service, operation)(**arguments)

    # Permission rejection must occur before accessing or changing a call.
    service._require_active_call.assert_not_awaited()
    service.require_voice_channel.assert_not_awaited()
    service.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_banned_user_cannot_join() -> None:
    service = make_service()
    access = make_access()
    channel_id = uuid.uuid4()

    service.repository.active_ban.return_value = SimpleNamespace(
        is_active=True,
        user_id=access.actor_user_id,
    )

    with pytest.raises(VoiceChannelPermissionError):
        await service.join(
            access=access,
            channel_id=channel_id,
        )

    service.repository.active_ban.assert_awaited_once_with(
        channel_id=channel_id,
        user_id=access.actor_user_id,
    )

    service.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_participant_is_rejected() -> None:
    service = make_service()
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    service.repository.participant.return_value = None

    with pytest.raises(VoiceChannelPermissionError):
        await service._require_joined_participant(
            call_id=call_id,
            user_id=user_id,
        )

    service.repository.participant.assert_awaited_once_with(
        call_id=call_id,
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_participant_who_left_is_rejected() -> None:
    service = make_service()
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    service.repository.participant.return_value = SimpleNamespace(
        call_id=call_id,
        user_id=user_id,
        state=VOICE_PARTICIPANT_LEFT,
    )

    with pytest.raises(VoiceChannelPermissionError):
        await service._require_joined_participant(
            call_id=call_id,
            user_id=user_id,
        )


@pytest.mark.asyncio
async def test_joined_participant_is_accepted() -> None:
    service = make_service()
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    participant = SimpleNamespace(
        call_id=call_id,
        user_id=user_id,
        state=VOICE_PARTICIPANT_JOINED,
    )

    service.repository.participant.return_value = participant

    result = await service._require_joined_participant(
        call_id=call_id,
        user_id=user_id,
    )

    assert result is participant