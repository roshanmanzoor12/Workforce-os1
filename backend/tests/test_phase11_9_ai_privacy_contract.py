from __future__ import annotations

import uuid

from app.modules.ai_productivity.enums import (
    AIProductivitySource,
)
from app.modules.ai_productivity.privacy import (
    redact_obvious_secrets,
    sanitize_ai_context,
)
from app.modules.ai_productivity.schemas import (
    AIContextItem,
    AIProductivityContext,
)


def test_password_redaction() -> None:
    value = redact_obvious_secrets(
        "password=secret123"
    )

    assert "secret123" not in value
    assert "[REDACTED]" in value


def test_api_key_redaction() -> None:
    value = redact_obvious_secrets(
        "api_key=abc123"
    )

    assert "abc123" not in value
    assert "[REDACTED]" in value


def test_bearer_redaction() -> None:
    value = redact_obvious_secrets(
        (
            "Authorization: Bearer "
            "token-value"
        )
    )

    assert "token-value" not in value
    assert "[REDACTED]" in value


def test_context_item_limit() -> None:
    context = AIProductivityContext(
        employee_id=uuid.uuid4(),
        items=[
            AIContextItem(
                source=(
                    AIProductivitySource.NOTES
                ),
                id=uuid.uuid4(),
                title="Example",
                content="x" * 10000,
            )
        ],
        total_items=1,
    )

    safe = sanitize_ai_context(
        context,
        max_item_characters=1000,
        max_context_characters=2000,
    )

    assert safe.total_items == 1

    assert (
        len(
            safe.items[0].content
            or ""
        )
        <= 1000
    )


def test_context_total_limit() -> None:
    items = [
        AIContextItem(
            source=(
                AIProductivitySource.NOTES
            ),
            id=uuid.uuid4(),
            title=f"Note {index}",
            content="x" * 1000,
        )
        for index in range(
            20
        )
    ]

    context = AIProductivityContext(
        employee_id=uuid.uuid4(),
        items=items,
        total_items=len(items),
    )

    safe = sanitize_ai_context(
        context,
        max_item_characters=1000,
        max_context_characters=2500,
    )

    size = sum(
        len(
            item.title
        )
        + len(
            item.content
            or ""
        )
        for item in safe.items
    )

    assert size <= 2500


def test_sanitized_total_matches_items() -> None:
    context = AIProductivityContext(
        employee_id=uuid.uuid4(),
        items=[
            AIContextItem(
                source=(
                    AIProductivitySource.GOALS
                ),
                id=uuid.uuid4(),
                title="Goal",
                content="Content",
            )
        ],
        total_items=1,
    )

    safe = sanitize_ai_context(
        context,
        max_item_characters=1000,
        max_context_characters=2000,
    )

    assert safe.total_items == len(
        safe.items
    )