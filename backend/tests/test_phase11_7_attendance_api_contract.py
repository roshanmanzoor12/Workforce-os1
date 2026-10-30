from __future__ import annotations

from pathlib import Path


def test_attendance_api_uses_authorized_context(
) -> None:
    text = Path(
        "app/modules/attendance/api.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "AuthorizedTenantContext" in text
    assert "AttendanceAccessService" in text


def test_attendance_api_exposes_required_operations(
) -> None:
    text = Path(
        "app/modules/attendance/api.py"
    ).read_text(
        encoding="utf-8"
    )

    required = [
        "record_event",
        "get_day",
        "update_day",
        "list_days",
        "employee_summary",
    ]

    for token in required:
        assert token in text


def test_attendance_access_enforces_membership(
) -> None:
    text = Path(
        "app/modules/attendance/access_service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "require_active_member" in text
    assert "require_manager" in text


def test_attendance_access_separates_databases(
) -> None:
    text = Path(
        "app/modules/attendance/access_service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "control_session" in text
    assert "tenant_session" in text