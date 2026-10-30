from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from app.modules.calls.enums import (
    CallSignalType,
)


def utc_iso() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def build_call_created_event(
    *,
    call_id: uuid.UUID,
    started_by_user_id: uuid.UUID,
    scope: str,
    conversation_id: (
        uuid.UUID | None
    ),
    channel_id: (
        uuid.UUID | None
    ),
    kind: str,
) -> dict[str, object]:
    return {
        "type": "call.created",
        "data": {
            "call_id": str(call_id),
            "started_by_user_id": str(
                started_by_user_id
            ),
            "scope": scope,
            "conversation_id": (
                str(conversation_id)
                if conversation_id
                else None
            ),
            "channel_id": (
                str(channel_id)
                if channel_id
                else None
            ),
            "kind": kind,
            "created_at": utc_iso(),
        },
    }


def build_call_participant_event(
    *,
    event_type: str,
    call_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, object]:
    return {
        "type": event_type,
        "data": {
            "call_id": str(call_id),
            "user_id": str(user_id),
            "at": utc_iso(),
        },
    }


def build_call_ended_event(
    *,
    call_id: uuid.UUID,
    ended_by_user_id: uuid.UUID,
) -> dict[str, object]:
    return {
        "type": "call.ended",
        "data": {
            "call_id": str(call_id),
            "ended_by_user_id": str(
                ended_by_user_id
            ),
            "ended_at": utc_iso(),
        },
    }


def build_screen_share_event(
    *,
    call_id: uuid.UUID,
    user_id: uuid.UUID,
    active: bool,
) -> dict[str, object]:
    return {
        "type": (
            "call.screen_share.started"
            if active
            else "call.screen_share.stopped"
        ),
        "data": {
            "call_id": str(call_id),
            "user_id": str(user_id),
            "at": utc_iso(),
        },
    }


def build_call_signal_event(
    *,
    call_id: uuid.UUID,
    sender_user_id: uuid.UUID,
    target_user_id: (
        uuid.UUID | None
    ),
    signal_type: CallSignalType,
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        "type": "call.signal",
        "data": {
            "call_id": str(call_id),
            "sender_user_id": str(
                sender_user_id
            ),
            "target_user_id": (
                str(target_user_id)
                if target_user_id
                else None
            ),
            "signal_type": (
                signal_type.value
            ),
            "payload": payload,
            "created_at": utc_iso(),
        },
    }