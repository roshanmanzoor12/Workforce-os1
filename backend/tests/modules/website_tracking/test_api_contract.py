from __future__ import annotations

from fastapi.routing import (
    APIRoute,
)

from app.modules.website_tracking.website_tracking_api_router import (
    router,
)


EXPECTED_ROUTES = {
    (
        "/device-agent/website-observation",
        "POST",
    ),
    (
        "/device-agent/website-status",
        "GET",
    ),
    (
        "/device-agent/website-history",
        "GET",
    ),
}


def get_api_routes(
) -> list[APIRoute]:
    return [
        route
        for route in router.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]


def test_exact_number_of_phase11_routes(
) -> None:
    routes = get_api_routes()

    assert len(routes) == 3


def test_all_phase11_routes_registered(
) -> None:
    actual: set[
        tuple[
            str,
            str,
        ]
    ] = set()

    for route in get_api_routes():
        for method in route.methods:
            if method in {
                "POST",
                "GET",
            }:
                actual.add(
                    (
                        route.path,
                        method,
                    )
                )

    assert actual == EXPECTED_ROUTES


def test_observation_route_contract(
) -> None:
    route = next(
        route
        for route in get_api_routes()
        if (
            route.path
            == (
                "/device-agent/"
                "website-observation"
            )
        )
    )

    assert (
        "POST"
        in route.methods
    )

    assert (
        route.name
        == "report_device_website_observation"
    )


def test_status_route_contract(
) -> None:
    route = next(
        route
        for route in get_api_routes()
        if (
            route.path
            == (
                "/device-agent/"
                "website-status"
            )
        )
    )

    assert (
        "GET"
        in route.methods
    )

    assert (
        route.name
        == "get_device_current_website_status"
    )


def test_history_route_contract(
) -> None:
    route = next(
        route
        for route in get_api_routes()
        if (
            route.path
            == (
                "/device-agent/"
                "website-history"
            )
        )
    )

    assert (
        "GET"
        in route.methods
    )

    assert (
        route.name
        == "get_device_website_history"
    )


def test_no_workspace_or_database_route_parameters(
) -> None:
    for route in get_api_routes():
        path = route.path.lower()

        assert "workspace" not in path
        assert "database" not in path
        assert "tenant" not in path