from __future__ import annotations

from app.config import settings
from app.main import app


def test_employee_monitoring_detail_route_exists():
    prefix = (
        settings.api_v1_prefix
        .rstrip("/")
    )

    path = (
        prefix
        + "/workspaces/{workspace_id}"
        + "/employee-monitoring/{employee_id}"
    )

    schema = app.openapi()

    assert path in schema["paths"], (
        "Missing Employee Monitoring "
        f"Detail route: {path}"
    )

    assert (
        "get"
        in schema["paths"][path]
    )


def test_employee_monitoring_detail_is_browser_workspace_route():
    prefix = (
        settings.api_v1_prefix
        .rstrip("/")
    )

    path = (
        prefix
        + "/workspaces/{workspace_id}"
        + "/employee-monitoring/{employee_id}"
    )

    assert (
        "/device-agent/"
        not in path
    )