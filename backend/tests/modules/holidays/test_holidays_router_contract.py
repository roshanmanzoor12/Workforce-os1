from __future__ import annotations

from fastapi.routing import (
    APIRoute,
)

from app.modules.holidays.router import (
    router,
)


def route_contract() -> set[
    tuple[str, str]
]:
    result: set[
        tuple[str, str]
    ] = set()

    for route in router.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        for method in route.methods:
            if method in {
                "HEAD",
                "OPTIONS",
            }:
                continue

            result.add(
                (
                    method,
                    route.path,
                )
            )

    return result


def test_holiday_routes_exist():
    routes = route_contract()

    expected = {
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/holidays",
        ),
        (
            "POST",
            "/workspaces/"
            "{workspace_id}/holidays",
        ),
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/holidays/"
            "{holiday_id}",
        ),
        (
            "PATCH",
            "/workspaces/"
            "{workspace_id}/holidays/"
            "{holiday_id}",
        ),
        (
            "DELETE",
            "/workspaces/"
            "{workspace_id}/holidays/"
            "{holiday_id}",
        ),
    }

    assert expected == routes