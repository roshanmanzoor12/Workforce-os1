from __future__ import annotations

from collections.abc import Iterable

from app.main import app

from tests.modules.channels_phase21.phase21_contract import (
    CHANNEL_ROUTES,
    REALTIME_ROUTES,
    require_path,
)


def test_channel_http_routes_exist():
    paths = app.openapi()["paths"]

    for route_name, contract in CHANNEL_ROUTES.items():
        expected_path = contract[0]
        method = contract[1]

        resolved = require_path(
            paths,
            expected_path,
        )

        assert method in paths[resolved], (
            f"{route_name} missing "
            f"{method.upper()}"
        )


def test_realtime_http_routes_exist():
    paths = app.openapi()["paths"]

    for route_name, contract in REALTIME_ROUTES.items():
        expected_path = contract[0]
        method = contract[1]

        resolved = require_path(
            paths,
            expected_path,
        )

        assert method in paths[resolved], (
            f"{route_name} missing "
            f"{method.upper()}"
        )


def _walk_routes(
    routes: Iterable[object],
    prefix: str = "",
):
    for route in routes:
        included_router = getattr(
            route,
            "original_router",
            None,
        )

        if included_router is not None:
            include_context = getattr(
                route,
                "include_context",
                None,
            )

            included_prefix = getattr(
                include_context,
                "prefix",
                "",
            ) or ""

            yield from _walk_routes(
                included_router.routes,
                f"{prefix}{included_prefix}",
            )
            continue

        route_path = getattr(
            route,
            "path",
            None,
        ) or ""

        full_path = f"{prefix}{route_path}"

        nested_routes = getattr(
            route,
            "routes",
            None,
        )

        if nested_routes:
            yield from _walk_routes(
                nested_routes,
                full_path,
            )
        else:
            yield route, full_path


def test_realtime_websocket_route_exists():
    expected_suffix = (
        "/workspaces/{workspace_id}"
        "/channels/{channel_id}"
        "/realtime/ws"
    )

    websocket_paths = {
        full_path
        for route, full_path in _walk_routes(app.routes)
        if type(route).__name__.endswith("WebSocketRoute")
    }

    assert any(
        path.endswith(expected_suffix)
        for path in websocket_paths
    ), (
        "Expected channel realtime WebSocket route ending with "
        f"{expected_suffix!r}; discovered routes: "
        f"{sorted(websocket_paths)!r}"
    )