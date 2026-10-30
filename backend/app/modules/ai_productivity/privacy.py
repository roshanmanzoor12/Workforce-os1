from __future__ import annotations

import re

from app.modules.ai_productivity.schemas import (
    AIContextItem,
    AIProductivityContext,
)


SECRET_PATTERNS: tuple[
    re.Pattern[str],
    ...,
] = (
    re.compile(
        (
            r"(?i)"
            r"(password\s*[:=]\s*)"
            r"([^\s,;]+)"
        )
    ),
    re.compile(
        (
            r"(?i)"
            r"(api[_-]?key\s*[:=]\s*)"
            r"([^\s,;]+)"
        )
    ),
    re.compile(
        (
            r"(?i)"
            r"(secret\s*[:=]\s*)"
            r"([^\s,;]+)"
        )
    ),
    re.compile(
        (
            r"(?i)"
            r"(authorization\s*[:=]\s*bearer\s+)"
            r"([^\s,;]+)"
        )
    ),
)


def redact_obvious_secrets(
    text: str,
) -> str:
    redacted = text

    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(
            r"\1[REDACTED]",
            redacted,
        )

    return redacted


def truncate_text(
    text: str,
    limit: int,
) -> str:
    if len(
        text
    ) <= limit:
        return text

    suffix = "\n[TRUNCATED]"

    available = max(
        0,
        limit - len(
            suffix
        ),
    )

    return (
        text[:available]
        + suffix
    )


def sanitize_ai_context(
    context: AIProductivityContext,
    *,
    max_item_characters: int,
    max_context_characters: int,
) -> AIProductivityContext:
    sanitized_items: list[
        AIContextItem
    ] = []

    consumed = 0

    for item in context.items:
        title = redact_obvious_secrets(
            item.title
        )

        content = (
            item.content
            or ""
        )

        content = redact_obvious_secrets(
            content
        )

        content = truncate_text(
            content,
            max_item_characters,
        )

        item_size = (
            len(
                title
            )
            + len(
                content
            )
        )

        remaining = (
            max_context_characters
            - consumed
        )

        if remaining <= 0:
            break

        if item_size > remaining:
            content_limit = max(
                0,
                remaining
                - len(
                    title
                ),
            )

            content = truncate_text(
                content,
                content_limit,
            )

            item_size = (
                len(
                    title
                )
                + len(
                    content
                )
            )

        sanitized_items.append(
            AIContextItem(
                source=item.source,
                id=item.id,
                title=title,
                content=content,
            )
        )

        consumed += item_size

    return AIProductivityContext(
        employee_id=context.employee_id,
        items=sanitized_items,
        total_items=len(
            sanitized_items
        ),
    )


__all__ = [
    "redact_obvious_secrets",
    "truncate_text",
    "sanitize_ai_context",
]