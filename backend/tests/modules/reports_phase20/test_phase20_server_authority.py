from __future__ import annotations

from app.main import app

from tests.modules.reports_phase20.phase20_contract import (
    SOURCE_ROUTE_MARKERS,
    find_matching_get_paths,
)


def test_reports_have_server_side_source_contracts():
    paths = app.openapi()[
        "paths"
    ]

    authoritative_sources = 0

    for markers in (
        SOURCE_ROUTE_MARKERS
        .values()
    ):
        if find_matching_get_paths(
            paths,
            markers,
        ):
            authoritative_sources += 1

    assert (
        authoritative_sources
        >= 6
    ), (
        "Phase 20 requires backend "
        "authoritative report sources. "
        "Too many source domains are "
        "currently unavailable."
    )


def test_productivity_report_has_backend_source():
    paths = app.openapi()[
        "paths"
    ]

    matches = (
        find_matching_get_paths(
            paths,
            SOURCE_ROUTE_MARKERS[
                "productivity"
            ],
        )
    )

    assert matches


def test_audit_report_has_backend_source():
    paths = app.openapi()[
        "paths"
    ]

    matches = (
        find_matching_get_paths(
            paths,
            SOURCE_ROUTE_MARKERS[
                "audit"
            ],
        )
    )

    assert matches