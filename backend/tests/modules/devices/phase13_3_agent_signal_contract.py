from __future__ import annotations

from app.config import settings


# =========================================================
# API PREFIX
# =========================================================


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
# CANONICAL AGENT SIGNAL CONTRACT
# =========================================================


EXPECTED_AGENT_SIGNAL_ENDPOINTS = {
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
        "GET",
        api_path(
            "/device-agent/app-history"
        ),
    ),
}


# =========================================================
# PRIVACY FORBIDDEN FIELDS
# =========================================================


FORBIDDEN_ACTIVITY_FIELDS = frozenset(
    {
        "keystrokes",
        "keys",
        "keylog",
        "keylogger",
        "typed_text",
        "typedtext",
        "clipboard",
        "clipboard_text",
        "password",
        "passwords",
    }
)


FORBIDDEN_APPLICATION_FIELDS = frozenset(
    {
        "keystrokes",
        "typed_text",
        "clipboard",
        "password",
        "screen_pixels",
        "screenshot_bytes",
    }
)


__all__ = [
    "API_PREFIX",
    "api_path",
    "EXPECTED_AGENT_SIGNAL_ENDPOINTS",
    "FORBIDDEN_ACTIVITY_FIELDS",
    "FORBIDDEN_APPLICATION_FIELDS",
]