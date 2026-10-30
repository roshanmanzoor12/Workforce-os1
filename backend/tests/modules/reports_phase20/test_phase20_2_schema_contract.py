from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest

from pydantic import (
    ValidationError,
)

from app.modules.reports.schemas import (
    ReportKey,
    ReportRunRequest,
    ReportScope,
)


def test_run_request_supports_all_reports():
    expected = {
        "attendance",
        "payroll",
        "productivity",
        "device_health",
        "monitoring_summary",
        "goals",
        "audit",
    }

    actual = {
        item.value
        for item
        in ReportKey
    }

    assert actual == expected


def test_run_request_supports_scope_filters():
    payload = ReportRunRequest(
        report=(
            ReportKey.ATTENDANCE
        ),
        scope=(
            ReportScope.TEAM
        ),
        status="present",
        limit=250,
    )

    assert (
        payload.scope
        == ReportScope.TEAM
    )

    assert payload.limit == 250


def test_invalid_date_window_rejected():
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValidationError
    ):
        ReportRunRequest(
            report=(
                ReportKey.ATTENDANCE
            ),
            scope=(
                ReportScope.SELF
            ),
            start_at=now,
            end_at=now,
        )


def test_limit_is_bounded():
    with pytest.raises(
        ValidationError
    ):
        ReportRunRequest(
            report=(
                ReportKey.GOALS
            ),
            scope=(
                ReportScope.SELF
            ),
            limit=5001,
        )