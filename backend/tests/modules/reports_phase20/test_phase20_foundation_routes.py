from __future__ import annotations

from app.main import app


CATALOG = (
    "/api/v1/workspaces/"
    "{workspace_id}/reports/catalog"
)

CAPABILITIES = (
    "/api/v1/workspaces/"
    "{workspace_id}/reports/capabilities"
)


def test_report_catalog_route_mounted():
    paths = app.openapi()[
        "paths"
    ]

    assert (
        CATALOG
        in paths
    )

    assert (
        "get"
        in paths[
            CATALOG
        ]
    )


def test_report_capabilities_route_mounted():
    paths = app.openapi()[
        "paths"
    ]

    assert (
        CAPABILITIES
        in paths
    )

    assert (
        "get"
        in paths[
            CAPABILITIES
        ]
    )


def test_reports_foundation_is_read_only():
    paths = app.openapi()[
        "paths"
    ]

    for path in (
        CATALOG,
        CAPABILITIES,
    ):
        operations = set(
            paths[
                path
            ]
        )

        assert not (
            operations
            & {
                "post",
                "put",
                "patch",
                "delete",
            }
        )