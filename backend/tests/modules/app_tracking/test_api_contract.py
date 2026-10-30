from __future__ import annotations

from app.modules.app_tracking.app_tracking_api_router import (
    router,
)


EXPECTED_ROUTES = {
    (
        "/device-agent/app-observation",
        "POST",
    ),
    (
        "/device-agent/app-status",
        "GET",
    ),
    (
        "/device-agent/app-history",
        "GET",
    ),
}


def get_routes() -> list[object]:
    return list(
        router.routes
    )


def get_route_by_path(
    path: str,
) -> object:
    matching = [
        route
        for route in get_routes()
        if getattr(
            route,
            "path",
            None,
        )
        == path
    ]

    assert len(
        matching
    ) == 1, (
        f"Expected exactly one route for {path!r}. "
        f"Available routes: "
        f"{[getattr(route, 'path', None) for route in get_routes()]}"
    )

    return matching[0]


def route_pairs() -> set[
    tuple[str, str]
]:
    result: set[
        tuple[str, str]
    ] = set()

    for route in get_routes():
        path = getattr(
            route,
            "path",
            None,
        )

        methods = getattr(
            route,
            "methods",
            None,
        )

        if (
            path is None
            or methods is None
        ):
            continue

        for method in methods:
            result.add(
                (
                    path,
                    method,
                )
            )

    return result


def test_app_tracking_router_is_not_empty() -> None:
    assert len(
        get_routes()
    ) >= 3


def test_app_tracking_expected_routes_exist() -> None:
    available = route_pairs()

    missing = (
        EXPECTED_ROUTES
        - available
    )

    assert not missing, (
        f"Missing App Tracking routes: {sorted(missing)}. "
        f"Available routes: {sorted(available)}"
    )


def test_app_tracking_observation_route() -> None:
    route = get_route_by_path(
        "/device-agent/app-observation"
    )

    methods = getattr(
        route,
        "methods",
        set(),
    )

    assert methods == {
        "POST"
    }

    assert (
        getattr(
            route,
            "response_model",
            None,
        )
        is not None
    )


def test_app_tracking_status_route() -> None:
    route = get_route_by_path(
        "/device-agent/app-status"
    )

    methods = getattr(
        route,
        "methods",
        set(),
    )

    assert methods == {
        "GET"
    }

    assert (
        getattr(
            route,
            "response_model",
            None,
        )
        is not None
    )


def test_app_tracking_history_route() -> None:
    route = get_route_by_path(
        "/device-agent/app-history"
    )

    methods = getattr(
        route,
        "methods",
        set(),
    )

    assert methods == {
        "GET"
    }

    assert (
        getattr(
            route,
            "response_model",
            None,
        )
        is not None
    )


def test_app_tracking_routes_are_unique() -> None:
    route_keys = [
        (
            getattr(
                route,
                "path",
                None,
            ),
            tuple(
                sorted(
                    getattr(
                        route,
                        "methods",
                        set(),
                    )
                    or set()
                )
            ),
        )
        for route in get_routes()
    ]

    assert len(
        route_keys
    ) == len(
        set(
            route_keys
        )
    )