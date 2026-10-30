from __future__ import annotations

from pathlib import Path

from app.main import app


def test_meeting_self_routes_registered(
) -> None:
    paths = app.openapi()["paths"]

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "me/invitations"
        in paths
    )

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "me/{meeting_id}/response"
        in paths
    )


def test_self_router_registered_before_dynamic_router(
) -> None:
    text = Path(
        "app/modules/tenant_api/router.py"
    ).read_text(
        encoding="utf-8",
    )

    self_position = text.index(
        "router.include_router(\n"
        "    meetings_self_router"
    )

    dynamic_position = text.index(
        "router.include_router(\n"
        "    meetings_router"
    )

    assert (
        self_position
        < dynamic_position
    )


def test_monitoring_routes_registered(
) -> None:
    paths = app.openapi()["paths"]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/"
            "live-access"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/"
            "manage-access"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/"
            "settings-access"
        ),
    ]

    for path in required:
        assert path in paths