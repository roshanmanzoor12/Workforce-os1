from __future__ import annotations

from fastapi.routing import (
    APIRoute,
)

from app.modules.shifts.router import (
    router,
)
from app.modules.shifts.service import (
    ShiftService,
)


def route_pairs() -> set[
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


def test_my_schedule_route_exists():
    assert (
        "GET",
        "/workspaces/"
        "{workspace_id}/"
        "schedules/me",
    ) in route_pairs()


def test_employee_schedule_route_still_exists():
    assert (
        "GET",
        "/workspaces/"
        "{workspace_id}/"
        "schedules/employees/"
        "{employee_id}",
    ) in route_pairs()


def test_team_resolution_repository_is_used():
    names = (
        ShiftService
        .resolve_employee_day
        .__code__
        .co_names
    )

    assert (
        "active_assignments_for_employee"
        in names
    )


def test_assignment_target_validator_exists():
    assert hasattr(
        ShiftService,
        "_require_assignment_target",
    )


def test_assignment_precedence_exists():
    assert hasattr(
        ShiftService,
        "_assignment_precedence",
    )