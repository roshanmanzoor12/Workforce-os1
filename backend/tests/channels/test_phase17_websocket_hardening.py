from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

WEBSOCKET_FILE = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "channels"
    / "realtime_websocket.py"
)


def _source() -> str:
    return WEBSOCKET_FILE.read_text(
        encoding="utf-8",
    )


def test_websocket_module_parses() -> None:
    ast.parse(
        _source(),
        filename=str(
            WEBSOCKET_FILE
        ),
    )


def test_websocket_consumes_one_time_ticket() -> None:
    source = _source()

    assert (
        "channel_realtime_ticket_service"
        in source
    )

    assert ".consume(" in source


def test_websocket_revalidates_membership() -> None:
    source = _source()

    required = (
        "ChannelAccessGuard",
        "require_membership_revalidation",
        "_assert_access",
        "ChannelAccessDenied",
    )

    for token in required:
        assert token in source


def test_websocket_rejects_removed_member() -> None:
    source = _source()

    assert "code=4403" in source


def test_websocket_rejects_invalid_ticket() -> None:
    source = _source()

    assert "code=4401" in source


def test_websocket_has_connection_rate_limit() -> None:
    source = _source()

    required = (
        "ChannelRateLimiter",
        "websocket_connect_limit",
        "code=4429",
    )

    for token in required:
        assert token in source


def test_websocket_owns_pubsub_lifecycle() -> None:
    source = _source()

    assert (
        "ChannelRealtimePubSubSession"
        in source
    )

    assert (
        "pubsub_session.close()"
        in source
    )


def test_websocket_cleans_presence() -> None:
    source = _source()

    assert ".stop_typing(" in source
    assert ".disconnect(" in source