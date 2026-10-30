from __future__ import annotations

from enum import StrEnum


class RealtimeClientCommandType(
    StrEnum
):
    PING = "ping"

    TYPING_START = (
        "typing.start"
    )

    TYPING_STOP = (
        "typing.stop"
    )

    RESUME = "resume"


class RealtimeServerEventType(
    StrEnum
):
    PONG = "pong"

    COMMAND_ACCEPTED = (
        "command.accepted"
    )

    COMMAND_REJECTED = (
        "command.rejected"
    )

    RESUME_REQUIRED = (
        "resume.required"
    )


__all__ = [
    "RealtimeClientCommandType",
    "RealtimeServerEventType",
]