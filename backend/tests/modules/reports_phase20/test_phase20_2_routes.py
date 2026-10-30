from __future__ import annotations

from app.main import app


BASE = (
    "/api/v1/workspaces/"
    "{workspace_id}/reports"
)


def test_report_run_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    path = f"{BASE}/run"

    assert path in paths

    assert (
        "post"
        in paths[path]
    )


def test_report_export_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    path = f"{BASE}/export"

    assert path in paths

    assert (
        "post"
        in paths[path]
    )


def test_reports_foundation_routes_still_exist():
    paths = app.openapi()[
        "paths"
    ]

    assert (
        f"{BASE}/catalog"
        in paths
    )

    assert (
        f"{BASE}/capabilities"
        in paths
    )


def test_no_report_mutation_routes():
    paths = app.openapi()[
        "paths"
    ]

    for suffix in (
        "/catalog",
        "/capabilities",
    ):
        operations = set(
            paths[
                f"{BASE}{suffix}"
            ]
        )

        assert not (
            operations
            & {
                "post",
                "patch",
                "put",
                "delete",
            }
        )