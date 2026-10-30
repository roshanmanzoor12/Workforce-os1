from __future__ import annotations

from app.config import settings


API_PREFIX = (
    settings.api_v1_prefix
    .rstrip("/")
)


def api_path(
    path: str,
) -> str:
    normalized = (
        path
        if path.startswith("/")
        else f"/{path}"
    )

    return (
        API_PREFIX
        + normalized
    )


LIVE_SCREEN_ENDPOINTS = {
    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/live-sessions"
        ),
    ),

    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/live-sessions/"
            "{session_id}/decision"
        ),
    ),

    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/live-sessions/"
            "{session_id}/activate"
        ),
    ),

    (
        "POST",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/live-sessions/"
            "{session_id}/end"
        ),
    ),

    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/live-sessions/"
            "{session_id}"
        ),
    ),

    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}"
            "/live-monitoring/capabilities"
        ),
    ),
}


__all__ = [
    "API_PREFIX",
    "api_path",
    "LIVE_SCREEN_ENDPOINTS",
]