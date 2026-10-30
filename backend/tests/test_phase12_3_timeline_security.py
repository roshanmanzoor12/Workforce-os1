from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from app.modules.timeline.security import (
    sanitize_timeline_metadata,
)


def test_forbidden_metadata_removed() -> None:
    result = sanitize_timeline_metadata(
        {
            "device_id": str(
                uuid4()
            ),
            "password": "abc",
            "device_secret": "secret",
            "database_name": "tenant_test",
            "cluster_key": "cluster",
            "status": "active",
        }
    )

    assert (
        "password"
        not in result
    )

    assert (
        "device_secret"
        not in result
    )

    assert (
        "database_name"
        not in result
    )

    assert (
        "cluster_key"
        not in result
    )

    assert (
        result[
            "status"
        ]
        == "active"
    )


def test_nested_secrets_removed() -> None:
    result = sanitize_timeline_metadata(
        {
            "device": {
                "hostname": "PC-01",
                "device_secret": "bad",
            }
        }
    )

    device = result[
        "device"
    ]

    assert (
        device[
            "hostname"
        ]
        == "PC-01"
    )

    assert (
        "device_secret"
        not in device
    )


def test_datetime_serialized() -> None:
    now = datetime(
        2026,
        9,
        18,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = sanitize_timeline_metadata(
        {
            "timestamp": now,
        }
    )

    assert (
        result[
            "timestamp"
        ]
        == now.isoformat()
    )


def test_large_string_truncated() -> None:
    result = sanitize_timeline_metadata(
        {
            "value": (
                "x"
                * 5000
            )
        }
    )

    assert (
        result[
            "value"
        ].endswith(
            "[TRUNCATED]"
        )
    )

    assert (
        len(
            result[
                "value"
            ]
        )
        < 5000
    )


def test_authorization_removed() -> None:
    result = sanitize_timeline_metadata(
        {
            "authorization": (
                "Bearer token"
            ),
            "safe": True,
        }
    )

    assert (
        "authorization"
        not in result
    )

    assert (
        result[
            "safe"
        ]
        is True
    )