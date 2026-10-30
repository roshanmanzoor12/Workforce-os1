from __future__ import annotations

from pathlib import Path

from app.main import app
from app.modules.timeline.security import (
    FORBIDDEN_METADATA_KEYS,
)


TIMELINE_ROOT = Path(
    "app/modules/timeline"
)


FORBIDDEN_BROWSER_FIELDS = {
    "database_name",
    "database_url",
    "tenant_database",
    "tenant_password",
    "cluster_key",
    "device_secret",
    "credential_secret",
    "secret_hash",
    "x-device-secret",
}


def timeline_openapi_text(
) -> str:
    schema = app.openapi()

    timeline_paths = {
        path: operation
        for path, operation
        in schema[
            "paths"
        ].items()
        if "/timeline" in path
    }

    return str(
        timeline_paths
    ).lower()


def test_timeline_openapi_does_not_accept_database_routing_fields(
) -> None:
    text = (
        timeline_openapi_text()
    )

    forbidden = {
        "database_name",
        "database_url",
        "tenant_database",
        "tenant_password",
        "cluster_key",
    }

    for field in forbidden:
        assert field not in text


def test_timeline_openapi_does_not_accept_device_credentials(
) -> None:
    text = (
        timeline_openapi_text()
    )

    forbidden = {
        "device_secret",
        "credential_secret",
        "secret_hash",
        "x-device-secret",
    }

    for field in forbidden:
        assert field not in text


def test_security_denylist_contains_sensitive_fields(
) -> None:
    normalized = {
        item.lower()
        for item
        in FORBIDDEN_METADATA_KEYS
    }

    expected = {
        "database_name",
        "database_url",
        "tenant_database",
        "tenant_password",
        "cluster_key",
        "device_secret",
        "credential_secret",
        "secret_hash",
        "x-device-secret",
    }

    assert (
        expected
        .issubset(
            normalized
        )
    )


def test_timeline_does_not_use_request_state_tenant_session(
) -> None:
    for path in (
        TIMELINE_ROOT
        .glob(
            "*.py"
        )
    ):
        text = (
            path.read_text(
                encoding="utf-8",
            )
        )

        assert (
            "request.state"
            not in text
        )


def test_timeline_router_has_no_device_agent_auth_headers(
) -> None:
    router_path = (
        TIMELINE_ROOT
        / "router.py"
    )

    text = (
        router_path
        .read_text(
            encoding="utf-8",
        )
        .lower()
    )

    assert (
        "x-device-uuid"
        not in text
    )

    assert (
        "x-device-secret"
        not in text
    )


def test_timeline_public_contract_has_no_forbidden_browser_fields(
) -> None:
    text = (
        timeline_openapi_text()
    )

    for field in (
        FORBIDDEN_BROWSER_FIELDS
    ):
        assert field not in text