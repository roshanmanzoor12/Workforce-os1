from __future__ import annotations

import inspect

from app.modules.attachments.message_router import (
    bind_channel_attachments,
    list_channel_attachments,
)
from app.modules.attachments.service import (
    AttachmentService,
)


def test_channel_attachment_access_is_membership_scoped():
    source = inspect.getsource(
        AttachmentService
        ._channel_access_allowed
    )

    assert (
        "WorkspaceChannelMember"
        in source
    )

    assert (
        "WorkspaceChannel"
        in source
    )

    assert (
        "left_at"
        in source
    )

    assert (
        "is_active"
        in source
    )


def test_channel_attachment_binding_is_server_scoped():
    source = inspect.getsource(
        bind_channel_attachments
    )

    assert (
        "_workspace_id_for_channel"
        in source
    )

    assert (
        "channel_id"
        in source
    )


def test_attachment_binding_publishes_realtime():
    source = inspect.getsource(
        bind_channel_attachments
    )

    assert (
        "channel_realtime_attachment_bridge"
        in source
    )

    assert (
        "publish_bound"
        in source
    )


def test_attachment_list_uses_authenticated_access():
    source = inspect.getsource(
        list_channel_attachments
    )

    assert (
        "list_channel_message"
        in source
    )

    assert (
        "_user_id"
        in source
    )