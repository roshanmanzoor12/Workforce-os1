from __future__ import annotations

from app.main import app

from tests.modules.reports_phase20.phase20_contract import (
    SOURCE_ROUTE_MARKERS,
    find_matching_get_paths,
)


def test_report_source_domains_have_get_contracts():
    paths = app.openapi()[
        "paths"
    ]

    missing: list[str] = []

    for (
        source_name,
        markers,
    ) in SOURCE_ROUTE_MARKERS.items():
        matches = (
            find_matching_get_paths(
                paths,
                markers,
            )
        )

        if not matches:
            missing.append(
                source_name
            )

    assert not missing, (
        "No readable backend source "
        "route found for report "
        f"domains: {missing}"
    )