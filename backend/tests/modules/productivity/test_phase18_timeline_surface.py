from __future__ import annotations

from app.main import app

from tests.modules.productivity.phase18_contract import (
    TIMELINE_BASE,
    require_openapi_path,
)


def test_timeline_capabilities_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        (
            f"{TIMELINE_BASE}/"
            "capabilities"
        ),
    )

    assert (
        "get"
        in paths[
            resolved
        ]
    )


def test_self_timeline_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        f"{TIMELINE_BASE}/me",
    )

    assert (
        "get"
        in paths[
            resolved
        ]
    )


def test_employee_timeline_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        (
            f"{TIMELINE_BASE}/"
            "employees/"
            "{employee_id}"
        ),
    )

    assert (
        "get"
        in paths[
            resolved
        ]
    )