from __future__ import annotations

import inspect

from app.modules.channels.realtime_events import (
    WorkspaceChannelRealtimeEventPublisher,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeEventType,
)


def test_required_channel_event_types_exist():
    values = {
        item.value
        for item
        in WorkspaceChannelRealtimeEventType
    }

    required = {
        "channel.created",
        "channel.updated",
        "channel.archived",
        "message.created",
        "message.updated",
        "message.deleted",
        "channel.attachment.bound",
    }

    assert required.issubset(
        values
    )


def test_event_publisher_surface():
    required = {
        "channel_created",
        "channel_updated",
        "channel_archived",
        "message_created",
        "message_updated",
        "message_deleted",
        "attachment_bound",
    }

    actual = set(
        dir(
            WorkspaceChannelRealtimeEventPublisher
        )
    )

    assert required.issubset(
        actual
    )


def test_message_payload_is_public_only():
    source = inspect.getsource(
        WorkspaceChannelRealtimeEventPublisher
        .message_payload
    )

    required = {
        '"id"',
        '"channel_id"',
        '"sender_user_id"',
        '"message_type"',
        '"content"',
        '"edited_at"',
        '"deleted_at"',
        '"created_at"',
    }

    for field in required:
        assert field in source

    forbidden = {
        "password",
        "secret",
        "token",
        "credential",
    }

    lowered = source.lower()

    for item in forbidden:
        assert item not in lowered


def test_realtime_publish_is_not_database_mutation():
    source = inspect.getsource(
        WorkspaceChannelRealtimeEventPublisher
    )

    assert (
        "session.commit"
        not in source
    )

    assert (
        "session.flush"
        not in source
    )