from __future__ import annotations

from app.main import app

from tests.modules.analytics_phase19.phase19_contract import (
    ANALYTICS_ENDPOINTS,
    require_openapi_path,
)


def test_all_phase19_analytics_routes_exist():
    paths = app.openapi()[
        "paths"
    ]

    assert (
        len(
            ANALYTICS_ENDPOINTS
        )
        == 8
    )

    for (
        endpoint_name,
        expected_path,
    ) in ANALYTICS_ENDPOINTS.items():
        resolved = require_openapi_path(
            paths,
            expected_path,
        )

        assert (
            "get"
            in paths[
                resolved
            ]
        ), (
            "Analytics endpoint "
            f"{endpoint_name!r} "
            "must support GET."
        )


def test_analytics_routes_are_read_only():
    paths = app.openapi()[
        "paths"
    ]

    forbidden_methods = {
        "post",
        "put",
        "patch",
        "delete",
    }

    for expected_path in (
        ANALYTICS_ENDPOINTS.values()
    ):
        resolved = require_openapi_path(
            paths,
            expected_path,
        )

        methods = set(
            paths[
                resolved
            ]
        )

        assert not (
            methods
            & forbidden_methods
        )