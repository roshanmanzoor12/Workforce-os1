from __future__ import annotations

import inspect

from app.modules.channels.repository import (
    WorkspaceChannelRepository,
)
from app.modules.channels.service import (
    WorkspaceChannelService,
)


def test_service_supports_message_update():
    assert hasattr(
        WorkspaceChannelService,
        "update_message",
    ), (
        "Channel router calls "
        "WorkspaceChannelService."
        "update_message(), but the "
        "service does not expose it."
    )


def test_service_supports_message_delete():
    assert hasattr(
        WorkspaceChannelService,
        "delete_message",
    ), (
        "Channel router calls "
        "WorkspaceChannelService."
        "delete_message(), but the "
        "service does not expose it."
    )


def test_repository_supports_message_lookup():
    assert hasattr(
        WorkspaceChannelRepository,
        "get_message",
    )


def test_repository_supports_message_update():
    assert hasattr(
        WorkspaceChannelRepository,
        "update_message",
    )


def test_repository_supports_message_delete():
    assert hasattr(
        WorkspaceChannelRepository,
        "delete_message",
    )


def test_message_update_requires_channel_access():
    if not hasattr(
        WorkspaceChannelService,
        "update_message",
    ):
        return

    source = inspect.getsource(
        WorkspaceChannelService
        .update_message
    )

    assert (
        "_require_active_member"
        in source
        or
        "_require_manager"
        in source
    )


def test_message_delete_requires_channel_access():
    if not hasattr(
        WorkspaceChannelService,
        "delete_message",
    ):
        return

    source = inspect.getsource(
        WorkspaceChannelService
        .delete_message
    )

    assert (
        "_require_active_member"
        in source
        or
        "_require_manager"
        in source
    )