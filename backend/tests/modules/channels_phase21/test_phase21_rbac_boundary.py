from __future__ import annotations

import inspect

from app.modules.channels.router import (
    create_workspace_channel,
    list_workspace_channels,
)
from app.modules.channels.service import (
    WorkspaceChannelService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_channel_permissions_exist():
    assert (
        WorkspacePermission
        .CHANNELS_READ
        .value
        == "channels.read"
    )

    assert (
        WorkspacePermission
        .CHANNELS_CREATE
        .value
        == "channels.create"
    )

    assert (
        WorkspacePermission
        .CHANNELS_MANAGE
        .value
        == "channels.manage"
    )


def test_create_channel_uses_permission_model():
    router_source = inspect.getsource(
        create_workspace_channel
    )

    service_source = inspect.getsource(
        WorkspaceChannelService
        .create_channel
    )

    combined = (
        router_source
        + "\n"
        + service_source
    )

    assert (
        "CHANNELS_CREATE"
        in combined
        or
        "channels.create"
        in combined
    ), (
        "Channel creation still appears "
        "to rely on workspace creator "
        "ownership instead of the current "
        "CHANNELS_CREATE permission."
    )


def test_list_channel_uses_permission_model():
    router_source = inspect.getsource(
        list_workspace_channels
    )

    service_source = inspect.getsource(
        WorkspaceChannelService
        .list_channels
    )

    combined = (
        router_source
        + "\n"
        + service_source
    )

    assert (
        "CHANNELS_READ"
        in combined
        or
        "channels.read"
        in combined
    ), (
        "Channel listing should enforce "
        "the canonical CHANNELS_READ "
        "permission as well as membership."
    )


def test_manage_channel_uses_permission_model():
    source = inspect.getsource(
        WorkspaceChannelService
    )

    assert (
        "CHANNELS_MANAGE"
        in source
        or
        "channels.manage"
        in source
    ), (
        "Channel management currently "
        "appears role-local only."
    )


def test_no_browser_secret_contract():
    source = inspect.getsource(
        WorkspaceChannelService
    ).lower()

    forbidden = {
        "device_secret",
        "client_secret",
        "refresh_token",
        "private_key",
    }

    for item in forbidden:
        assert item not in source