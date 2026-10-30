from __future__ import annotations

import inspect

from app.modules.voice_channels.repository import (
    VoiceChannelRepository,
)
from app.modules.voice_channels.service import (
    VoiceChannelService,
)


REQUIRED_SERVICE_METHODS = {
    "active_call",
    "join",
    "leave",
    "participants",
    "self_state",
    "moderator_state",
    "kick",
    "ban",
    "unban",
    "screen_share",
    "signal",
    "poll_signals",
    "heartbeat",
    "speaking",
    "capabilities",
}


REQUIRED_REPOSITORY_METHODS = {
    "active_call",
    "create_call",
    "get_call",
    "end_call",
    "participant",
    "joined_participants",
    "join",
    "leave",
    "refresh_participant",
    "active_ban",
    "ban",
    "unban",
}


def test_voice_service_surface_exists() -> None:
    missing = {
        name
        for name in REQUIRED_SERVICE_METHODS
        if not callable(
            getattr(
                VoiceChannelService,
                name,
                None,
            )
        )
    }

    assert not missing, (
        "VoiceChannelService is missing methods: "
        f"{sorted(missing)}"
    )


def test_voice_repository_surface_exists() -> None:
    missing = {
        name
        for name in REQUIRED_REPOSITORY_METHODS
        if not callable(
            getattr(
                VoiceChannelRepository,
                name,
                None,
            )
        )
    }

    assert not missing, (
        "VoiceChannelRepository is missing methods: "
        f"{sorted(missing)}"
    )


def test_voice_service_methods_are_async() -> None:
    async_methods = {
        name
        for name in REQUIRED_SERVICE_METHODS
        if inspect.iscoroutinefunction(
            getattr(
                VoiceChannelService,
                name,
                None,
            )
        )
    }

    synchronous_methods = (
        REQUIRED_SERVICE_METHODS
        - async_methods
        - {"capabilities"}
    )

    assert not synchronous_methods, (
        "Voice service methods must be async: "
        f"{sorted(synchronous_methods)}"
    )


def test_voice_repository_database_methods_are_async() -> None:
    synchronous_methods = {
        name
        for name in REQUIRED_REPOSITORY_METHODS
        if not inspect.iscoroutinefunction(
            getattr(
                VoiceChannelRepository,
                name,
                None,
            )
        )
    }

    assert not synchronous_methods, (
        "Voice repository methods must be async: "
        f"{sorted(synchronous_methods)}"
    )


def test_voice_capabilities_method_is_available() -> None:
    capabilities = getattr(
        VoiceChannelService,
        "capabilities",
        None,
    )

    assert callable(capabilities)