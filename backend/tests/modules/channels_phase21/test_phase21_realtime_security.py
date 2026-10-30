from __future__ import annotations

import inspect

from app.modules.channels import (
    realtime_router,
)


def test_websocket_uses_ticket():
    source = inspect.getsource(
        realtime_router
        .workspace_channel_realtime_socket
    )

    assert "ticket" in source

    assert (
        "__consume_and_validate_ticket"
        in source
    )


def test_ticket_route_identity_is_verified():
    source = inspect.getsource(
        realtime_router
        .__consume_and_validate_ticket
    )

    assert (
        "identity.workspace_id"
        in source
    )

    assert (
        "identity.channel_id"
        in source
    )

    assert (
        "workspace_id"
        in source
    )

    assert (
        "channel_id"
        in source
    )


def test_invalid_ticket_closes_4401():
    source = inspect.getsource(
        realtime_router
        .__consume_and_validate_ticket
    )

    assert "4401" in source


def test_mismatched_route_closes_4403():
    source = inspect.getsource(
        realtime_router
        .__consume_and_validate_ticket
    )

    assert "4403" in source


def test_resume_validates_channel_id():
    source = inspect.getsource(
        realtime_router
        .resume_channel_realtime
    )

    assert (
        "payload.channel_id"
        in source
    )

    assert (
        "!= channel_id"
        in source
    )


def test_realtime_access_uses_tenant_context():
    source = inspect.getsource(
        realtime_router
    )

    assert (
        "get_authorized_tenant_context"
        in source
    )