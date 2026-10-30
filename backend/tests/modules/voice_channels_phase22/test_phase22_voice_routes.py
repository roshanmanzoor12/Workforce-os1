from __future__ import annotations

from fastapi import FastAPI

from app.main import app


EXPECTED_ROUTES: set[tuple[str, str]] = {
    (
        "GET",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/active-call",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/join",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/leave",
    ),
    (
        "GET",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/participants",
    ),
    (
        "PATCH",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/me",
    ),
    (
        "PATCH",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/participants/"
        "{user_id}/moderation",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/participants/{user_id}/kick",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/bans/{user_id}",
    ),
    (
        "DELETE",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/bans/{user_id}",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/screen-share/start",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/screen-share/stop",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/signal",
    ),
    (
        "GET",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/signals",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/presence",
    ),
    (
        "POST",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/speaking",
    ),
    (
        "GET",
        "/api/v1/workspaces/{workspace_id}/channels/"
        "{channel_id}/voice/capabilities",
    ),
}


def _openapi_routes(application: FastAPI) -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()

    for path, operations in application.openapi().get(
        "paths",
        {},
    ).items():
        if "/voice/" not in path:
            continue

        for method in operations:
            method_upper = method.upper()

            if method_upper in {
                "GET",
                "POST",
                "PATCH",
                "PUT",
                "DELETE",
            }:
                routes.add(
                    (
                        method_upper,
                        path,
                    )
                )

    return routes


def test_voice_routes_are_registered() -> None:
    actual_routes = _openapi_routes(app)
    missing = EXPECTED_ROUTES - actual_routes

    assert not missing, (
        "Missing voice routes: "
        f"{sorted(missing)}"
    )


def test_voice_routes_are_exposed_in_openapi() -> None:
    actual_routes = _openapi_routes(app)
    missing = EXPECTED_ROUTES - actual_routes

    assert not missing, (
        "Missing voice OpenAPI routes: "
        f"{sorted(missing)}"
    )


def test_voice_routes_use_api_v1_prefix() -> None:
    actual_routes = _openapi_routes(app)

    voice_paths = {
        path
        for _, path in actual_routes
    }

    assert voice_paths, (
        "No voice routes were found."
    )

    assert all(
        path.startswith("/api/v1/")
        for path in voice_paths
    ), sorted(voice_paths)


def test_voice_routes_are_not_registered_under_tenant_prefix() -> None:
    actual_routes = _openapi_routes(app)

    invalid_paths = {
        path
        for _, path in actual_routes
        if not path.startswith("/api/v1/")
    }

    assert not invalid_paths, sorted(
        invalid_paths
    )