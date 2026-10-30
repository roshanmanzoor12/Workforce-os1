from __future__ import annotations

from app.main import app

from tests.modules.reports_phase20.phase20_contract import (
    find_report_paths,
)


def test_report_api_inventory_is_inspectable(
    capsys,
):
    paths = app.openapi()[
        "paths"
    ]

    report_paths = (
        find_report_paths(
            paths
        )
    )

    print(
        "PHASE20_REPORT_PATH_COUNT="
        f"{len(report_paths)}"
    )

    for path in report_paths:
        print(
            f"PHASE20_REPORT_PATH={path}"
        )

    captured = (
        capsys.readouterr()
    )

    assert (
        "PHASE20_REPORT_PATH_COUNT="
        in captured.out
    )