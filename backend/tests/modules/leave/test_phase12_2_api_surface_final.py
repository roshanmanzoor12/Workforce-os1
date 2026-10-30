from __future__ import annotations

from pathlib import Path

from app.modules.leave.integration_router import (
    router as integration_router,
)
from app.modules.leave.router import (
    router as leave_router,
)


def direct_paths(
    router,
) -> set[str]:
    return {
        route.path
        for route in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_primary_leave_api_surface():
    paths = direct_paths(
        leave_router
    )

    expected_fragments = {
        "/leave/types",
        "/leave/policies",
        "/leave/me/requests",
        "/leave/me/balances",
        "/leave/requests",
        "/leave/employees/",
    }

    joined = "\n".join(
        sorted(
            paths
        )
    )

    for fragment in (
        expected_fragments
    ):
        assert fragment in joined


def test_leave_decision_routes_present():
    joined = "\n".join(
        sorted(
            direct_paths(
                leave_router
            )
        )
    )

    assert "/approve" in joined
    assert "/reject" in joined
    assert "/cancel" in joined


def test_leave_integration_api_surface():
    paths = direct_paths(
        integration_router
    )

    joined = "\n".join(
        sorted(
            paths
        )
    )

    assert (
        "/calendar"
        in joined
    )

    assert (
        "/attendance-context/"
        in joined
    )

    assert (
        "/consumption/"
        in joined
    )

    assert (
        "/payroll-context"
        in joined
    )


def test_tenant_router_registers_both_leave_routers():
    source = (
        Path(
            "app/modules/tenant_api/"
            "router.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "leave_router"
        in source
    )

    assert (
        "leave_integration_router"
        in source
    )

    assert (
        "include_router"
        in source
    )