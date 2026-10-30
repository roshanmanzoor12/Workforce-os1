from __future__ import annotations

from collections.abc import Mapping


PRODUCTIVITY_BASE = (
    "/workspaces/{workspace_id}/"
    "productivity-insights"
)

ANALYTICS_BASE = (
    "/workspaces/{workspace_id}/"
    "analytics"
)

AI_BASE = (
    "/workspaces/{workspace_id}/"
    "ai-productivity"
)

TIMELINE_BASE = (
    "/workspaces/{workspace_id}/"
    "timeline"
)


PRODUCTIVITY_ENDPOINTS = {
    "overview": (
        f"{PRODUCTIVITY_BASE}/overview"
    ),

    "activity": (
        f"{PRODUCTIVITY_BASE}/activity"
    ),

    "usage": (
        f"{PRODUCTIVITY_BASE}/usage"
    ),

    "goals": (
        f"{PRODUCTIVITY_BASE}/goals"
    ),

    "comparison": (
        f"{PRODUCTIVITY_BASE}/comparison"
    ),
}


def find_openapi_path(
    paths: Mapping[str, object],
    expected_suffix: str,
) -> str | None:
    """
    Resolve an OpenAPI route without assuming whether
    the application mounted it under /api/v1 or another
    global prefix.

    The domain route itself must match exactly.
    """

    if expected_suffix in paths:
        return expected_suffix

    for path in paths:
        if path.endswith(
            expected_suffix
        ):
            return path

    return None


def require_openapi_path(
    paths: Mapping[str, object],
    expected_suffix: str,
) -> str:
    resolved = find_openapi_path(
        paths,
        expected_suffix,
    )

    assert (
        resolved is not None
    ), (
        "Required Phase 18 route missing: "
        f"{expected_suffix}"
    )

    return resolved


__all__ = [
    "PRODUCTIVITY_BASE",
    "ANALYTICS_BASE",
    "AI_BASE",
    "TIMELINE_BASE",
    "PRODUCTIVITY_ENDPOINTS",
    "find_openapi_path",
    "require_openapi_path",
]