from __future__ import annotations

from collections.abc import Mapping


ANALYTICS_BASE = (
    "/workspaces/{workspace_id}/analytics"
)


ANALYTICS_ENDPOINTS = {
    "overview": (
        f"{ANALYTICS_BASE}/overview"
    ),

    "activity": (
        f"{ANALYTICS_BASE}/activity"
    ),

    "attendance": (
        f"{ANALYTICS_BASE}/attendance"
    ),

    "productivity": (
        f"{ANALYTICS_BASE}/productivity"
    ),

    "apps": (
        f"{ANALYTICS_BASE}/apps"
    ),

    "websites": (
        f"{ANALYTICS_BASE}/websites"
    ),

    "goals": (
        f"{ANALYTICS_BASE}/goals"
    ),

    "trends": (
        f"{ANALYTICS_BASE}/trends"
    ),
}


def find_openapi_path(
    paths: Mapping[str, object],
    expected_suffix: str,
) -> str | None:
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
        "Required Phase 19 "
        "analytics route missing: "
        f"{expected_suffix}"
    )

    return resolved


__all__ = [
    "ANALYTICS_BASE",
    "ANALYTICS_ENDPOINTS",
    "find_openapi_path",
    "require_openapi_path",
]
