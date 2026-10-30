from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest

from app.modules.timeline.cursor import (
    TimelineCursor,
    TimelineCursorError,
    decode_timeline_cursor,
    encode_timeline_cursor,
)


def test_cursor_round_trip() -> None:
    original = TimelineCursor(
        occurred_at=datetime(
            2026,
            9,
            16,
            18,
            30,
            tzinfo=timezone.utc,
        ),
        event_id=(
            "goal.created:"
            "11111111-1111-1111-1111-111111111111"
        ),
    )

    encoded = (
        encode_timeline_cursor(
            original
        )
    )

    decoded = (
        decode_timeline_cursor(
            encoded
        )
    )

    assert decoded == original


def test_cursor_is_url_safe() -> None:
    value = encode_timeline_cursor(
        TimelineCursor(
            occurred_at=datetime.now(
                timezone.utc
            ),
            event_id="note.created:test",
        )
    )

    assert "+" not in value
    assert "/" not in value


def test_empty_cursor_rejected() -> None:
    with pytest.raises(
        TimelineCursorError
    ):
        decode_timeline_cursor(
            ""
        )


def test_invalid_cursor_rejected() -> None:
    with pytest.raises(
        TimelineCursorError
    ):
        decode_timeline_cursor(
            "not-a-valid-cursor"
        )


def test_cursor_requires_timezone() -> None:
    cursor = TimelineCursor(
        occurred_at=datetime(
            2026,
            9,
            16,
            12,
            0,
        ),
        event_id="goal.created:test",
    )

    encoded = (
        encode_timeline_cursor(
            cursor
        )
    )

    with pytest.raises(
        TimelineCursorError
    ):
        decode_timeline_cursor(
            encoded
        )