from __future__ import annotations

from app.main import app

from tests.modules.monitoring.phase17_contract import (
    SCREENSHOT_ROUTES,
    TIMELINE_ROUTES,
)


def _assert_routes(
    expected: set[
        tuple[
            str,
            str,
        ]
    ],
) -> None:
    schema = app.openapi()

    missing: list[str] = []

    for method, path in sorted(
        expected
    ):
        item = (
            schema["paths"]
            .get(path)
        )

        if not isinstance(
            item,
            dict,
        ):
            missing.append(
                f"{method} {path}"
            )

            continue

        if (
            method.lower()
            not in item
        ):
            missing.append(
                f"{method} {path}"
            )

    assert not missing, (
        "Missing Phase 17 routes: "
        + "; ".join(
            missing
        )
    )


def test_screenshot_routes_exist():
    _assert_routes(
        SCREENSHOT_ROUTES
    )


def test_timeline_routes_exist():
    _assert_routes(
        TIMELINE_ROUTES
    )


def test_screenshot_history_exposes_filters():
    schema = app.openapi()

    path = (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "live-monitoring/screenshots"
    )

    operation = (
        schema["paths"][path]["get"]
    )

    names = {
        item["name"]
        for item
        in operation.get(
            "parameters",
            [],
        )
    }

    expected = {
        "employee_id",
        "device_id",
        "status",
        "start_at",
        "end_at",
        "limit",
        "offset",
    }

    assert (
        expected
        <= names
    )