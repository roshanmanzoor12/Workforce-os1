from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

PRESENCE_FILE = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "channels"
    / "realtime_presence.py"
)


def _source() -> str:
    return PRESENCE_FILE.read_text(
        encoding="utf-8",
    )


def test_presence_module_parses() -> None:
    ast.parse(
        _source(),
        filename=str(
            PRESENCE_FILE
        ),
    )


def test_presence_uses_central_hardening_config() -> None:
    source = _source()

    required = (
        "get_channel_hardening_settings",
        "presence_online_ttl_seconds",
        "typing_ttl_seconds",
    )

    for token in required:
        assert token in source


def test_presence_uses_lifetime_guard() -> None:
    source = _source()

    assert (
        "PresenceLifetimeGuard"
        in source
    )

    assert ".evaluate(" in source


def test_presence_has_redis_expiry() -> None:
    source = _source()

    assert (
        "redis_client.expire("
        in source
    )


def test_typing_has_redis_expiry() -> None:
    source = _source()

    assert (
        "ex=self.TYPING_TTL_SECONDS"
        in source
    )


def test_stale_presence_is_removed() -> None:
    source = _source()

    assert (
        "evaluation.stale"
        in source
    )

    assert (
        "redis_client.delete("
        in source
    )


def test_typing_has_explicit_expiry_check() -> None:
    source = _source()

    assert (
        "typing_is_active"
        in source
    )