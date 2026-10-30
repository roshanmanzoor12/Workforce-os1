from __future__ import annotations

from fastapi.routing import (
    APIRoute,
)

from app.modules.shifts.router import (
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


def test_shift_template_routes_exist():
    routes = route_contract()

    expected = {
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/shifts",
        ),
        (
            "POST",
            "/workspaces/"
            "{workspace_id}/shifts",
        ),
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/shifts/"
            "{shift_id}",
        ),
        (
            "PATCH",
            "/workspaces/"
            "{workspace_id}/shifts/"
            "{shift_id}",
        ),
        (
            "DELETE",
            "/workspaces/"
            "{workspace_id}/shifts/"
            "{shift_id}",
        ),
    }

    assert expected.issubset(
        routes
    )


def test_shift_assignment_routes_exist():
    routes = route_contract()

    expected = {
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/"
            "shift-assignments",
        ),
        (
            "POST",
            "/workspaces/"
            "{workspace_id}/"
            "shift-assignments",
        ),
        (
            "PATCH",
            "/workspaces/"
            "{workspace_id}/"
            "shift-assignments/"
            "{assignment_id}",
        ),
        (
            "DELETE",
            "/workspaces/"
            "{workspace_id}/"
            "shift-assignments/"
            "{assignment_id}",
        ),
    }

    assert expected.issubset(
        routes
    )


def test_schedule_exception_routes_exist():
    routes = route_contract()

    expected = {
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/"
            "schedule-exceptions",
        ),
        (
            "POST",
            "/workspaces/"
            "{workspace_id}/"
            "schedule-exceptions",
        ),
        (
            "PATCH",
            "/workspaces/"
            "{workspace_id}/"
            "schedule-exceptions/"
            "{exception_id}",
        ),
        (
            "DELETE",
            "/workspaces/"
            "{workspace_id}/"
            "schedule-exceptions/"
            "{exception_id}",
        ),
    }

    assert expected.issubset(
        routes
    )


def test_schedule_publication_routes_exist():
    routes = route_contract()

    expected = {
        (
            "GET",
            "/workspaces/"
            "{workspace_id}/"
            "schedules/publications",
        ),
        (
            "POST",
            "/workspaces/"
            "{workspace_id}/"
            "schedules/publish",
        ),
    }

    assert expected.issubset(
        routes
    )


def test_employee_schedule_route_exists():
    routes = route_contract()

    assert (
        "GET",
        "/workspaces/"
        "{workspace_id}/"
        "schedules/employees/"
        "{employee_id}",
    ) in routes