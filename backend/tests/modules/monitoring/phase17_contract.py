from __future__ import annotations

from app.config import settings


API_PREFIX = (
    settings.api_v1_prefix
    .rstrip("/")
)


def api_path(
    value: str,
) -> str:
    path = (
        value
        if value.startswith("/")
        else f"/{value}"
    )

    return (
        API_PREFIX
        + path
    )


SCREENSHOT_ROUTES = {
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots"
        ),
    ),
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots/"
            "{request_id}/complete"
        ),
    ),
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots/"
            "{request_id}/deny"
        ),
    ),
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots/"
            "{request_id}/fail"
        ),
    ),
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/screenshots/"
            "{request_id}/media"
        ),
    ),
}


TIMELINE_ROUTES = {
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/timeline/capabilities"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/timeline/me"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/timeline/employees/"
            "{employee_id}"
        ),
    ),
}


__all__ = [
    "API_PREFIX",
    "api_path",
    "SCREENSHOT_ROUTES",
    "TIMELINE_ROUTES",
]