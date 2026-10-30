from __future__ import annotations

import sys
from pathlib import Path


# =========================================================
# BACKEND IMPORT ROOT
# =========================================================

BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

backend_root_text = str(
    BACKEND_ROOT
)

if (
    backend_root_text
    not in sys.path
):
    sys.path.insert(
        0,
        backend_root_text,
    )


# =========================================================
# APPLICATION IMPORTS
# =========================================================

from app.modules.channels.hardening.config import (  # noqa: E402
    get_channel_hardening_settings,
)


# =========================================================
# ASSERTION HELPER
# =========================================================

def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise SystemExit(
            "FAIL: " + message
        )


# =========================================================
# CERTIFICATION
# =========================================================

def main() -> None:
    settings = (
        get_channel_hardening_settings()
    )

    require(
        5
        <= settings.ticket_ttl_seconds
        <= 300,
        (
            "ticket_ttl_seconds must be "
            "between 5 and 300."
        ),
    )

    require(
        settings.websocket_connect_limit
        > 0,
        (
            "websocket_connect_limit "
            "must be positive."
        ),
    )

    require(
        settings.websocket_connect_window_seconds
        > 0,
        (
            "websocket connect window "
            "must be positive."
        ),
    )

    require(
        settings.message_event_limit
        > 0,
        (
            "message_event_limit "
            "must be positive."
        ),
    )

    require(
        settings.message_event_window_seconds
        > 0,
        (
            "message event window "
            "must be positive."
        ),
    )

    require(
        settings.typing_event_limit
        > 0,
        (
            "typing_event_limit "
            "must be positive."
        ),
    )

    require(
        settings.typing_event_window_seconds
        > 0,
        (
            "typing event window "
            "must be positive."
        ),
    )

    require(
        settings.heartbeat_limit
        > 0,
        (
            "heartbeat_limit "
            "must be positive."
        ),
    )

    require(
        settings.heartbeat_window_seconds
        > 0,
        (
            "heartbeat window "
            "must be positive."
        ),
    )

    require(
        settings.presence_online_ttl_seconds
        > settings.presence_idle_after_seconds,
        (
            "presence TTL must exceed "
            "idle threshold."
        ),
    )

    require(
        settings.presence_idle_after_seconds
        > 0,
        (
            "presence idle threshold "
            "must be positive."
        ),
    )

    require(
        settings.typing_ttl_seconds
        > 0,
        (
            "typing TTL must be positive."
        ),
    )

    require(
        settings.replay_batch_size
        > 0,
        (
            "replay_batch_size "
            "must be positive."
        ),
    )

    require(
        settings.replay_max_events
        >= settings.replay_batch_size,
        (
            "replay_max_events must "
            "be >= replay_batch_size."
        ),
    )

    require(
        settings.redis_operation_timeout_seconds
        > 0,
        (
            "Redis timeout must "
            "be positive."
        ),
    )

    require(
        settings.require_membership_revalidation
        is True,
        (
            "production realtime membership "
            "revalidation must be enabled."
        ),
    )

    require(
        settings.fail_closed_on_access_error
        is True,
        (
            "realtime authorization must "
            "fail closed."
        ),
    )

    print(
        "PASS Phase 17 production "
        "configuration contract"
    )


if __name__ == "__main__":
    main()