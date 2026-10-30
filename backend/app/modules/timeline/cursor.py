from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime


class TimelineCursorError(
    ValueError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class TimelineCursor:
    occurred_at: datetime
    event_id: str


def encode_timeline_cursor(
    cursor: TimelineCursor,
) -> str:
    payload = {
        "occurred_at": (
            cursor.occurred_at.isoformat()
        ),
        "event_id": cursor.event_id,
    }

    raw = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode(
        "utf-8"
    )

    return (
        base64.urlsafe_b64encode(
            raw
        )
        .decode(
            "ascii"
        )
        .rstrip("=")
    )


def decode_timeline_cursor(
    value: str,
) -> TimelineCursor:
    if not value:
        raise TimelineCursorError(
            "Timeline cursor cannot be empty."
        )

    try:
        padding = "=" * (
            (-len(value)) % 4
        )

        raw = (
            base64.urlsafe_b64decode(
                value + padding
            )
        )

        payload = json.loads(
            raw.decode(
                "utf-8"
            )
        )

        occurred_at = (
            datetime.fromisoformat(
                payload[
                    "occurred_at"
                ]
            )
        )

        event_id = payload[
            "event_id"
        ]

    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise TimelineCursorError(
            "Invalid timeline cursor."
        ) from exc

    if (
        not isinstance(
            event_id,
            str,
        )
        or not event_id
    ):
        raise TimelineCursorError(
            "Invalid timeline cursor."
        )

    if occurred_at.tzinfo is None:
        raise TimelineCursorError(
            "Timeline cursor timestamp "
            "must include timezone information."
        )

    return TimelineCursor(
        occurred_at=occurred_at,
        event_id=event_id,
    )


__all__ = [
    "TimelineCursor",
    "TimelineCursorError",
    "encode_timeline_cursor",
    "decode_timeline_cursor",
]