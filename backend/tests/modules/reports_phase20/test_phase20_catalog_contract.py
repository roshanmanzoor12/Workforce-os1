from __future__ import annotations

from app.modules.reports.schemas import (
    ReportFormat,
    ReportKey,
    ReportScope,
)
from app.modules.reports.service import (
    REPORT_CATALOG,
)


def test_report_catalog_contains_all_required_reports():
    assert {
        definition.key
        for definition
        in REPORT_CATALOG
    } == {
        ReportKey.ATTENDANCE,
        ReportKey.PAYROLL,
        ReportKey.PRODUCTIVITY,
        ReportKey.DEVICE_HEALTH,
        (
            ReportKey
            .MONITORING_SUMMARY
        ),
        ReportKey.GOALS,
        ReportKey.AUDIT,
    }


def test_catalog_has_unique_report_keys():
    keys = [
        definition.key
        for definition
        in REPORT_CATALOG
    ]

    assert (
        len(
            keys
        )
        == len(
            set(
                keys
            )
        )
    )


def test_catalog_uses_server_export_formats():
    for definition in (
        REPORT_CATALOG
    ):
        assert (
            ReportFormat.JSON
            in (
                definition
                .supported_formats
            )
        )

        assert (
            ReportFormat.CSV
            in (
                definition
                .supported_formats
            )
        )


def test_audit_is_workspace_only():
    audit = next(
        definition
        for definition
        in REPORT_CATALOG
        if (
            definition.key
            == ReportKey.AUDIT
        )
    )

    assert (
        audit.supported_scopes
        == [
            ReportScope.WORKSPACE
        ]
    )