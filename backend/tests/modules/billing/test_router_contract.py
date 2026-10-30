from fastapi.routing import APIRoute

from app.modules.billing.router import (
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
            result.add(
                (
                    method,
                    route.path,
                )
            )

    return result


def test_billing_router_prefix():
    assert router.prefix == "/billing"


def test_billing_router_contract():
    contract = route_contract()

    assert (
        "GET",
        "/billing/plans",
    ) in contract

    assert (
        "GET",
        "/billing/subscription",
    ) in contract

    assert (
        "GET",
        "/billing/entitlements",
    ) in contract

    assert (
        "GET",
        "/billing/workspace-access",
    ) in contract


def test_billing_router_has_exactly_four_routes():
    routes = [
        route
        for route in router.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]

    assert len(routes) == 4