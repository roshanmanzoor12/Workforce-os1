from __future__ import annotations

from app.modules.reports.permissions import (
    ReportsAccess,
)
from app.modules.reports.schemas import (
    ReportFormat,
    ReportScope,
)
from app.modules.reports.service import (
    ReportsService,
)


def test_self_only_capabilities():
    access = ReportsAccess(
        can_read_self=True,
        can_read_team=False,
        can_read_workspace=False,
        can_export=False,
    )

    payload = (
        ReportsService
        .capabilities(
            access
        )
    )

    assert (
        payload.effective_scopes
        == [
            ReportScope.SELF
        ]
    )

    assert (
        payload.can_export
        is False
    )

    assert (
        payload.export_formats
        == []
    )


def test_team_capabilities():
    access = ReportsAccess(
        can_read_self=True,
        can_read_team=True,
        can_read_workspace=False,
        can_export=True,
    )

    payload = (
        ReportsService
        .capabilities(
            access
        )
    )

    assert (
        ReportScope.SELF
        in payload.effective_scopes
    )

    assert (
        ReportScope.TEAM
        in payload.effective_scopes
    )

    assert (
        ReportScope.WORKSPACE
        not in payload.effective_scopes
    )


def test_workspace_export_capabilities():
    access = ReportsAccess(
        can_read_self=True,
        can_read_team=True,
        can_read_workspace=True,
        can_export=True,
    )

    payload = (
        ReportsService
        .capabilities(
            access
        )
    )

    assert (
        payload.can_export
        is True
    )

    assert (
        ReportFormat.JSON
        in payload.export_formats
    )

    assert (
        ReportFormat.CSV
        in payload.export_formats
    )


def test_catalog_hides_unavailable_scopes():
    access = ReportsAccess(
        can_read_self=True,
        can_read_team=False,
        can_read_workspace=False,
        can_export=False,
    )

    catalog = (
        ReportsService
        .catalog(
            access
        )
    )

    for item in catalog.items:
        assert (
            item.supported_scopes
            == [
                ReportScope.SELF
            ]
        )

        assert (
            item.supported_formats
            == []
        )