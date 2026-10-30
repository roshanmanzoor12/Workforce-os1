from __future__ import annotations

from datetime import (
    date,
    datetime,
)
from enum import Enum
from typing import Any
from uuid import UUID


FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "secret",
        "secret_hash",
        "device_secret",
        "credential_secret",
        "database_name",
        "database_url",
        "tenant_database",
        "tenant_password",
        "cluster_key",
        "authorization",
        "access_token",
        "refresh_token",
        "x-device-secret",
    }
)


MAX_METADATA_DEPTH = 4
MAX_STRING_LENGTH = 2000
MAX_LIST_ITEMS = 100
MAX_MAPPING_ITEMS = 100


def normalize_metadata_key(
    key: object,
) -> str:
    return str(
        key
    ).strip()


def is_forbidden_metadata_key(
    key: str,
) -> bool:
    normalized = (
        key.strip()
        .lower()
        .replace(
            "-",
            "_",
        )
    )

    return (
        normalized
        in {
            item.replace(
                "-",
                "_",
            )
            for item
            in FORBIDDEN_METADATA_KEYS
        }
    )


def sanitize_metadata_value(
    value: Any,
    *,
    depth: int = 0,
) -> Any:
    if depth > MAX_METADATA_DEPTH:
        return None

    if value is None:
        return None

    if isinstance(
        value,
        (
            bool,
            int,
            float,
        ),
    ):
        return value

    if isinstance(
        value,
        UUID,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Enum,
    ):
        return sanitize_metadata_value(
            value.value,
            depth=depth + 1,
        )

    if isinstance(
        value,
        str,
    ):
        if (
            len(value)
            <= MAX_STRING_LENGTH
        ):
            return value

        return (
            value[
                :MAX_STRING_LENGTH
            ]
            + "[TRUNCATED]"
        )

    if isinstance(
        value,
        dict,
    ):
        return sanitize_timeline_metadata(
            value,
            depth=depth + 1,
        )

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        return [
            sanitize_metadata_value(
                item,
                depth=depth + 1,
            )
            for item
            in list(value)[
                :MAX_LIST_ITEMS
            ]
        ]

    return str(
        value
    )[
        :MAX_STRING_LENGTH
    ]


def sanitize_timeline_metadata(
    metadata: dict[
        str,
        Any,
    ],
    *,
    depth: int = 0,
) -> dict[
    str,
    Any,
]:
    if depth > MAX_METADATA_DEPTH:
        return {}

    safe: dict[
        str,
        Any,
    ] = {}

    items = list(
        metadata.items()
    )[
        :MAX_MAPPING_ITEMS
    ]

    for raw_key, value in items:
        key = normalize_metadata_key(
            raw_key
        )

        if not key:
            continue

        if is_forbidden_metadata_key(
            key
        ):
            continue

        safe[
            key
        ] = sanitize_metadata_value(
            value,
            depth=depth + 1,
        )

    return safe


__all__ = [
    "FORBIDDEN_METADATA_KEYS",
    "MAX_METADATA_DEPTH",
    "MAX_STRING_LENGTH",
    "MAX_LIST_ITEMS",
    "MAX_MAPPING_ITEMS",
    "normalize_metadata_key",
    "is_forbidden_metadata_key",
    "sanitize_metadata_value",
    "sanitize_timeline_metadata",
]