from __future__ import annotations

from tests.modules.reports_phase20.phase20_contract import (
    REPORT_CATALOG,
)


def test_report_catalog_is_complete():
    assert set(
        REPORT_CATALOG
    ) == {
        "attendance",
        "payroll",
        "productivity",
        "device_health",
        "monitoring_summary",
        "goals",
        "audit",
    }


def test_report_catalog_has_no_duplicates():
    assert (
        len(
            REPORT_CATALOG
        )
        == len(
            set(
                REPORT_CATALOG
            )
        )
    )