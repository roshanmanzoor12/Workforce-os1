from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_int(
    name: str,
    default: int,
    *,
    minimum: int = 1,
) -> int:
    raw = os.getenv(
        name,
        str(default),
    ).strip()

    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer."
        ) from exc

    if value < minimum:
        raise RuntimeError(
            f"{name} must be >= {minimum}."
        )

    return value


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    raw = os.getenv(
        name,
        "true" if default else "false",
    )

    normalized = raw.strip().lower()

    if normalized in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    raise RuntimeError(
        f"{name} must be a boolean value."
    )


@dataclass(
    frozen=True,
    slots=True,
)
class ChannelHardeningSettings:
    """
    Production-hardening settings for channel realtime.

    Defaults intentionally preserve the Phase 16C user experience while
    adding conservative production limits.
    """

    ticket_ttl_seconds: int

    websocket_connect_limit: int
    websocket_connect_window_seconds: int

    message_event_limit: int
    message_event_window_seconds: int

    typing_event_limit: int
    typing_event_window_seconds: int

    heartbeat_limit: int
    heartbeat_window_seconds: int

    presence_online_ttl_seconds: int
    presence_idle_after_seconds: int
    typing_ttl_seconds: int

    replay_batch_size: int
    replay_max_events: int

    redis_operation_timeout_seconds: int

    require_membership_revalidation: bool
    fail_closed_on_access_error: bool

    @classmethod
    def from_environment(
        cls,
    ) -> "ChannelHardeningSettings":
        return cls(
            ticket_ttl_seconds=_env_int(
                "WF_CHANNEL_REALTIME_TICKET_TTL_SECONDS",
                60,
            ),

            websocket_connect_limit=_env_int(
                "WF_CHANNEL_WS_CONNECT_LIMIT",
                30,
            ),
            websocket_connect_window_seconds=_env_int(
                "WF_CHANNEL_WS_CONNECT_WINDOW_SECONDS",
                60,
            ),

            message_event_limit=_env_int(
                "WF_CHANNEL_MESSAGE_EVENT_LIMIT",
                120,
            ),
            message_event_window_seconds=_env_int(
                "WF_CHANNEL_MESSAGE_EVENT_WINDOW_SECONDS",
                60,
            ),

            typing_event_limit=_env_int(
                "WF_CHANNEL_TYPING_EVENT_LIMIT",
                90,
            ),
            typing_event_window_seconds=_env_int(
                "WF_CHANNEL_TYPING_EVENT_WINDOW_SECONDS",
                60,
            ),

            heartbeat_limit=_env_int(
                "WF_CHANNEL_HEARTBEAT_LIMIT",
                120,
            ),
            heartbeat_window_seconds=_env_int(
                "WF_CHANNEL_HEARTBEAT_WINDOW_SECONDS",
                60,
            ),

            presence_online_ttl_seconds=_env_int(
                "WF_CHANNEL_PRESENCE_TTL_SECONDS",
                90,
            ),
            presence_idle_after_seconds=_env_int(
                "WF_CHANNEL_PRESENCE_IDLE_AFTER_SECONDS",
                60,
            ),
            typing_ttl_seconds=_env_int(
                "WF_CHANNEL_TYPING_TTL_SECONDS",
                8,
            ),

            replay_batch_size=_env_int(
                "WF_CHANNEL_REPLAY_BATCH_SIZE",
                200,
            ),
            replay_max_events=_env_int(
                "WF_CHANNEL_REPLAY_MAX_EVENTS",
                1000,
            ),

            redis_operation_timeout_seconds=_env_int(
                "WF_CHANNEL_REDIS_TIMEOUT_SECONDS",
                5,
            ),

            require_membership_revalidation=_env_bool(
                "WF_CHANNEL_WS_REVALIDATE_MEMBERSHIP",
                True,
            ),
            fail_closed_on_access_error=_env_bool(
                "WF_CHANNEL_WS_FAIL_CLOSED",
                True,
            ),
        )


@lru_cache(
    maxsize=1
)
def get_channel_hardening_settings(
) -> ChannelHardeningSettings:
    return (
        ChannelHardeningSettings
        .from_environment()
    )