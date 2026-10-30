from __future__ import annotations

import uuid

from datetime import (
    datetime,
    timezone,
)

from app.modules.reports.exporter import (
    flatten_report_data,
    report_filename,
    report_to_csv,
)
from app.modules.reports.schemas import (
    ReportKey,
    ReportParametersResponse,
    ReportRunResponse,
    ReportScope,
)


def sample_report():
    return ReportRunResponse(
        workspace_id=(
            uuid.uuid4()
        ),
        report=(
            ReportKey.ATTENDANCE
        ),
        scope=(
            ReportScope.SELF
        ),
        generated_at=datetime(
            2026,
            9,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        parameters=(
            ReportParametersResponse(
                limit=500
            )
        ),
        data={
            "total_records": 3,
            "daily": [
                {
                    "date": (
                        "2026-09-30"
                    ),
                    "value": 3,
                }
            ],
        },
    )


def test_flatten_nested_report():
    rows = list(
        flatten_report_data(
            {
                "a": {
                    "b": 1,
                },
                "c": [
                    2,
                ],
            }
        )
    )

    assert (
        "data.a.b",
        "1",
    ) in rows

    assert (
        "data.c[0]",
        "2",
    ) in rows


def test_csv_contains_metadata_and_data():
    content = report_to_csv(
        sample_report()
    )

    assert "path,value" in content

    assert (
        "meta.report"
        in content
    )

    assert (
        "data.total_records"
        in content
    )


def test_export_filename_is_safe():
    name = report_filename(
        sample_report()
    )

    assert name.startswith(
        "workforceos_attendance_"
    )

    assert name.endswith(
        ".csv"
    )