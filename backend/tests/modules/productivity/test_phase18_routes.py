from __future__ import annotations

from app.main import app

from tests.modules.productivity.phase18_contract import (
    AI_BASE,
    ANALYTICS_BASE,
    PRODUCTIVITY_ENDPOINTS,
    require_openapi_path,
)


def test_productivity_insights_routes_exist():
    paths = app.openapi()[
        "paths"
    ]

    for (
        endpoint_name,
        expected_path,
    ) in PRODUCTIVITY_ENDPOINTS.items():
        resolved = (
            require_openapi_path(
                paths,
                expected_path,
            )
        )

        assert (
            "get"
            in paths[
                resolved
            ]
        ), (
            "Productivity endpoint "
            f"{endpoint_name!r} "
            "must support GET."
        )


def test_analytics_productivity_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        (
            f"{ANALYTICS_BASE}/"
            "productivity"
        ),
    )

    assert (
        "get"
        in paths[
            resolved
        ]
    )


def test_ai_productivity_capabilities_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        (
            f"{AI_BASE}/"
            "capabilities"
        ),
    )

    assert (
        "get"
        in paths[
            resolved
        ]
    )


def test_ai_productivity_run_route_exists():
    paths = app.openapi()[
        "paths"
    ]

    resolved = require_openapi_path(
        paths,
        f"{AI_BASE}/run",
    )

    assert (
        "post"
        in paths[
            resolved
        ]
    )