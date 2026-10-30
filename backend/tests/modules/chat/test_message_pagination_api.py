from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from app.modules.chat.pagination import (
    decode_message_cursor,
    encode_message_cursor,
)
from app.modules.chat.pagination_schemas import (
    ChatMessagePagePublic,
)


def test_cursor_is_frontend_safe():
    message_id = uuid.uuid4()

    created_at = datetime.now(
        timezone.utc
    )

    cursor = encode_message_cursor(
        created_at=created_at,
        message_id=message_id,
    )

    assert isinstance(
        cursor,
        str,
    )

    assert cursor

    restored = decode_message_cursor(
        cursor
    )

    assert (
        restored.message_id
        == message_id
    )

    assert (
        restored.created_at
        == created_at
    )


def test_message_page_schema():
    result = ChatMessagePagePublic(
        items=[],
        next_cursor=None,
        has_more=False,
    )

    assert result.items == []

    assert (
        result.next_cursor
        is None
    )

    assert result.has_more is False