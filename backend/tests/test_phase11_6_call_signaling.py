from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.modules.calls.enums import (
    CallKind,
    CallParticipantState,
    CallScope,
    CallSignalType,
    CallStatus,
    ScreenShareState,
)
from app.modules.calls.schemas import (
    CreateCallRequest,
)
from app.modules.calls.signaling import (
    build_call_created_event,
    build_call_ended_event,
    build_call_participant_event,
    build_call_signal_event,
    build_screen_share_event,
)


def test_call_scope_values() -> None:
    assert (
        CallScope.CONVERSATION.value
        == "CONVERSATION"
    )

    assert (
        CallScope.CHANNEL.value
        == "CHANNEL"
    )


def test_call_kind_values() -> None:
    assert CallKind.VOICE.value == "VOICE"
    assert CallKind.VIDEO.value == "VIDEO"


def test_call_status_values() -> None:
    assert (
        CallStatus.RINGING.value
        == "RINGING"
    )

    assert (
        CallStatus.ACTIVE.value
        == "ACTIVE"
    )

    assert (
        CallStatus.ENDED.value
        == "ENDED"
    )


def test_participant_state_values() -> None:
    assert (
        CallParticipantState.INVITED.value
        == "INVITED"
    )

    assert (
        CallParticipantState.JOINED.value
        == "JOINED"
    )


def test_screen_share_values() -> None:
    assert (
        ScreenShareState.STOPPED.value
        == "STOPPED"
    )

    assert (
        ScreenShareState.ACTIVE.value
        == "ACTIVE"
    )


def test_conversation_call_schema() -> None:
    conversation_id = uuid.uuid4()

    request = CreateCallRequest(
        scope=CallScope.CONVERSATION,
        kind=CallKind.VIDEO,
        conversation_id=conversation_id,
    )

    assert (
        request.conversation_id
        == conversation_id
    )

    assert request.channel_id is None


def test_channel_call_schema() -> None:
    channel_id = uuid.uuid4()

    request = CreateCallRequest(
        scope=CallScope.CHANNEL,
        kind=CallKind.VOICE,
        channel_id=channel_id,
    )

    assert (
        request.channel_id
        == channel_id
    )

    assert request.conversation_id is None


def test_conversation_requires_id() -> None:
    with pytest.raises(
        ValidationError
    ):
        CreateCallRequest(
            scope=(
                CallScope.CONVERSATION
            ),
            kind=CallKind.VOICE,
        )


def test_channel_requires_id() -> None:
    with pytest.raises(
        ValidationError
    ):
        CreateCallRequest(
            scope=CallScope.CHANNEL,
            kind=CallKind.VOICE,
        )


def test_call_created_event() -> None:
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conversation_id = uuid.uuid4()

    event = build_call_created_event(
        call_id=call_id,
        started_by_user_id=user_id,
        scope="CONVERSATION",
        conversation_id=(
            conversation_id
        ),
        channel_id=None,
        kind="VIDEO",
    )

    assert (
        event["type"]
        == "call.created"
    )

    assert (
        event["data"]["call_id"]
        == str(call_id)
    )


def test_joined_event() -> None:
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = build_call_participant_event(
        event_type=(
            "call.participant.joined"
        ),
        call_id=call_id,
        user_id=user_id,
    )

    assert (
        event["type"]
        == "call.participant.joined"
    )


def test_screen_share_started_event() -> None:
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = build_screen_share_event(
        call_id=call_id,
        user_id=user_id,
        active=True,
    )

    assert (
        event["type"]
        == "call.screen_share.started"
    )


def test_screen_share_stopped_event() -> None:
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = build_screen_share_event(
        call_id=call_id,
        user_id=user_id,
        active=False,
    )

    assert (
        event["type"]
        == "call.screen_share.stopped"
    )


def test_signal_event() -> None:
    call_id = uuid.uuid4()
    sender = uuid.uuid4()
    target = uuid.uuid4()

    event = build_call_signal_event(
        call_id=call_id,
        sender_user_id=sender,
        target_user_id=target,
        signal_type=(
            CallSignalType.OFFER
        ),
        payload={
            "sdp": "test"
        },
    )

    assert (
        event["type"]
        == "call.signal"
    )

    assert (
        event["data"]["signal_type"]
        == "OFFER"
    )

    assert (
        event["data"]["target_user_id"]
        == str(target)
    )


def test_signal_event_has_no_storage_secrets() -> None:
    event = build_call_signal_event(
        call_id=uuid.uuid4(),
        sender_user_id=uuid.uuid4(),
        target_user_id=None,
        signal_type=(
            CallSignalType.ICE_CANDIDATE
        ),
        payload={
            "candidate": "abc"
        },
    )

    text = str(event)

    assert "MINIO_ACCESS_KEY" not in text
    assert "MINIO_SECRET_KEY" not in text
    assert "database_url" not in text


def test_call_ended_event() -> None:
    call_id = uuid.uuid4()
    user_id = uuid.uuid4()

    event = build_call_ended_event(
        call_id=call_id,
        ended_by_user_id=user_id,
    )

    assert (
        event["type"]
        == "call.ended"
    )