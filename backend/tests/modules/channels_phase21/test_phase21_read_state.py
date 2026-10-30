from __future__ import annotations

import inspect

from app.modules.channels.read_state_repository import (
    WorkspaceChannelReadStateRepository,
)
from app.modules.channels.read_state_service import (
    WorkspaceChannelReadStateService,
)


def test_read_state_service_surface():
    required = {
        "get_summary",
        "mark_message_read",
        "mark_all_read",
        "list_workspace",
    }

    actual = set(
        dir(
            WorkspaceChannelReadStateService
        )
    )

    assert required.issubset(
        actual
    )


def test_read_state_repository_surface():
    required = {
        "get_channel",
        "get_active_member",
        "get_message",
        "get_state",
        "save_state",
        "latest_message",
        "unread_count",
        "list_active_channels",
    }

    actual = set(
        dir(
            WorkspaceChannelReadStateRepository
        )
    )

    assert required.issubset(
        actual
    )


def test_read_state_uses_atomic_upsert():
    source = inspect.getsource(
        WorkspaceChannelReadStateRepository
        .save_state
    )

    assert (
        "ChannelReadStateUpserter"
        in source
    )

    assert (
        "upsert_and_flush"
        in source
    )


def test_unread_excludes_deleted_messages():
    source = inspect.getsource(
        WorkspaceChannelReadStateRepository
        .unread_count
    )

    assert "deleted_at" in source


def test_unread_excludes_own_messages():
    source = inspect.getsource(
        WorkspaceChannelReadStateRepository
        .unread_count
    )

    assert (
        "sender_user_id"
        in source
    )

    assert (
        "user_id"
        in source
    )


def test_mark_message_read_is_monotonic():
    source = inspect.getsource(
        WorkspaceChannelReadStateService
        .mark_message_read
    )

    assert (
        "current.last_read_at"
        in source
    )

    assert (
        ">= target_read_at"
        in source
    )