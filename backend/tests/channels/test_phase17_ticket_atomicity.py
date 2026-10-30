from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

TICKET_FILE = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "channels"
    / "realtime_ticket.py"
)


def _source() -> str:
    return TICKET_FILE.read_text(
        encoding="utf-8",
    )


def test_ticket_module_parses() -> None:
    ast.parse(
        _source(),
        filename=str(
            TICKET_FILE
        ),
    )


def test_ticket_consume_uses_atomic_redis_script() -> None:
    source = _source()

    assert "_ATOMIC_CONSUME_LUA" in source
    assert "redis_client.eval(" in source


def test_ticket_consume_does_not_use_get_then_delete() -> None:
    source = _source()

    assert (
        "await redis_client.get("
        not in source
    )


def test_ticket_ttl_comes_from_hardening_config() -> None:
    source = _source()

    assert (
        "get_channel_hardening_settings"
        in source
    )

    assert (
        "ticket_ttl_seconds"
        in source
    )


def test_ticket_identity_is_server_side() -> None:
    source = _source()

    required = (
        "workspace_id",
        "channel_id",
        "user_id",
    )

    for token in required:
        assert token in source


def test_ticket_uses_secure_random_value() -> None:
    source = _source()

    assert (
        "secrets.token_urlsafe"
        in source
    )