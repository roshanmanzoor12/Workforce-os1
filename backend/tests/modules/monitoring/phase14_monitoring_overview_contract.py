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


# =========================================================
# PAGE-LEVEL BROWSER CONTRACT
# =========================================================


MONITORING_OVERVIEW_ENDPOINTS = {
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/monitoring-control"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/monitoring-control/live-access"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/monitoring-control/manage-access"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/monitoring-control/settings-access"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/monitoring-control/view-access"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/devices/readiness"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/timeline/capabilities"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/timeline/me"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/timeline/employees/{employee_id}"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/workforce-intelligence/overview"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/workforce-intelligence/employees"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/workforce-intelligence/trends"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/workforce-intelligence/signals"
        ),
    ),
    (
        "GET",
        api_path(
            "/workspaces/{workspace_id}/workforce-intelligence/capabilities"
        ),
    ),
}


# =========================================================
# AGENT-EVIDENCE CONTRACT
# =========================================================


AGENT_EVIDENCE_ENDPOINTS = {
    (
        "POST",
        api_path(
            "/device-agent/activity-state"
        ),
    ),
    (
        "GET",
        api_path(
            "/device-agent/activity-status"
        ),
    ),
    (
        "POST",
        api_path(
            "/device-agent/app-observation"
        ),
    ),
    (
        "GET",
        api_path(
            "/device-agent/app-status"
        ),
    ),
    (
        "POST",
        api_path(
            "/device-agent/website-observation"
        ),
    ),
    (
        "GET",
        api_path(
            "/device-agent/website-status"
        ),
    ),
}


FORBIDDEN_MONITORING_FIELDS = frozenset(
    {
        "keystrokes",
        "keylog",
        "keylogger",
        "typed_text",
        "clipboard",
        "clipboard_text",
        "password",
        "passwords",
        "device_secret",
        "secret_hash",
    }
)


__all__ = [
    "API_PREFIX",
    "api_path",
    "MONITORING_OVERVIEW_ENDPOINTS",
    "AGENT_EVIDENCE_ENDPOINTS",
    "FORBIDDEN_MONITORING_FIELDS",
]