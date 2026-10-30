from __future__ import annotations

import re


_WHITESPACE_RE = re.compile(
    r"\s+"
)


def normalize_search_text(
    value: str | None,
) -> str:
    if not value:
        return ""

    return (
        _WHITESPACE_RE
        .sub(
            " ",
            value
            .strip()
            .casefold(),
        )
    )


def search_tokens(
    query: str,
) -> list[str]:
    normalized = (
        normalize_search_text(
            query
        )
    )

    return [
        token
        for token
        in normalized.split(" ")
        if token
    ]


def field_match_score(
    *,
    query: str,
    value: str | None,
    weight: float = 1.0,
) -> float:
    normalized_query = (
        normalize_search_text(
            query
        )
    )

    normalized_value = (
        normalize_search_text(
            value
        )
    )

    if (
        not normalized_query
        or not normalized_value
    ):
        return 0.0

    if (
        normalized_value
        == normalized_query
    ):
        return 100.0 * weight

    if normalized_value.startswith(
        normalized_query
    ):
        return 80.0 * weight

    if (
        normalized_query
        in normalized_value
    ):
        return 60.0 * weight

    tokens = search_tokens(
        normalized_query
    )

    if not tokens:
        return 0.0

    matched = sum(
        1
        for token in tokens
        if token in normalized_value
    )

    if matched == 0:
        return 0.0

    ratio = (
        matched
        / len(tokens)
    )

    return (
        40.0
        * ratio
        * weight
    )


def combined_score(
    *,
    query: str,
    fields: list[
        tuple[
            str,
            str | None,
            float,
        ]
    ],
) -> tuple[
    float,
    list[str],
]:
    score = 0.0

    matched_fields: list[str] = []

    for (
        field_name,
        value,
        weight,
    ) in fields:
        field_score = (
            field_match_score(
                query=query,
                value=value,
                weight=weight,
            )
        )

        if field_score <= 0:
            continue

        matched_fields.append(
            field_name
        )

        if field_score > score:
            score = field_score

        else:
            score += (
                field_score
                * 0.10
            )

    return (
        round(
            score,
            3,
        ),
        matched_fields,
    )


__all__ = [
    "normalize_search_text",
    "search_tokens",
    "field_match_score",
    "combined_score",
]