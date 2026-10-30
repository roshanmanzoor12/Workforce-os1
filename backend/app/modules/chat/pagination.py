from __future__ import annotations

import base64
import binascii
import json
import uuid
from dataclasses import dataclass
from datetime import datetime


MAX_MESSAGE_CURSOR_LENGTH = 2048


@dataclass(frozen=True, slots=True)
class MessageCursor:
    created_at: datetime
    message_id: uuid.UUID


def encode_message_cursor(
    *,
    created_at: datetime,
    message_id: uuid.UUID,
) -> str:
    if not isinstance(created_at, datetime):
        raise ValueError(
            "Message cursor timestamp must be a datetime."
        )

    if (
        created_at.tzinfo is None
        or created_at.utcoffset() is None
    ):
        raise ValueError(
            "Message cursor timestamp must be timezone-aware."
        )

    if not isinstance(message_id, uuid.UUID):
        raise ValueError(
            "Message cursor message ID must be a UUID."
        )

    payload = {
        "created_at": created_at.isoformat(),
        "message_id": str(message_id),
    }

    raw = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    return (
        base64.urlsafe_b64encode(raw)
        .decode("ascii")
        .rstrip("=")
    )


def decode_message_cursor(
    value: str,
) -> MessageCursor:
    if not isinstance(value, str):
        raise ValueError(
            "Invalid message cursor."
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "Message cursor is required."
        )

    if len(normalized) > MAX_MESSAGE_CURSOR_LENGTH:
        raise ValueError(
            "Invalid message cursor."
        )

    padding = "=" * (-len(normalized) % 4)

    try:
        raw = base64.b64decode(
            normalized + padding,
            altchars=b"-_",
            validate=True,
        )

        payload = json.loads(
            raw.decode("utf-8")
        )

        if not isinstance(payload, dict):
            raise ValueError(
                "Message cursor payload must be an object."
            )

        timestamp_value = payload["created_at"]
        message_id_value = payload["message_id"]

        if (
            not isinstance(timestamp_value, str)
            or not isinstance(message_id_value, str)
        ):
            raise ValueError(
                "Message cursor fields must be strings."
            )

        created_at = datetime.fromisoformat(
            timestamp_value
        )

        message_id = uuid.UUID(
            message_id_value
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        binascii.Error,
    ) as exc:
        raise ValueError(
            "Invalid message cursor."
        ) from exc

    if (
        created_at.tzinfo is None
        or created_at.utcoffset() is None
    ):
        raise ValueError(
            "Message cursor timestamp must be timezone-aware."
        )

    return MessageCursor(
        created_at=created_at,
        message_id=message_id,
    )


__all__ = [
    "MessageCursor",
    "decode_message_cursor",
    "encode_message_cursor",
]