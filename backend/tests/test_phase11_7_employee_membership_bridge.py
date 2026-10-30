from __future__ import annotations

from pathlib import Path


def test_bridge_uses_workspace_memberships(
) -> None:
    text = Path(
        "app/modules/employees/"
        "membership_bridge.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "WorkspaceMembershipRepository"
        in text
    )


def test_bridge_requires_active_member(
) -> None:
    text = Path(
        "app/modules/employees/"
        "membership_bridge.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "require_active_member"
        in text
    )

    assert (
        "MEMBERSHIP_STATUS_ACTIVE"
        in text
    )


def test_bridge_requires_manager(
) -> None:
    text = Path(
        "app/modules/employees/"
        "membership_bridge.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "WORKSPACE_ROLE_OWNER" in text
    assert "WORKSPACE_ROLE_ADMIN" in text


def test_employee_user_link_is_optional(
) -> None:
    text = Path(
        "app/modules/employees/"
        "membership_bridge.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "if employee_user_id is None"
        in text
    )


def test_access_service_separates_databases(
) -> None:
    text = Path(
        "app/modules/employees/"
        "access_service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "control_session" in text
    assert "tenant_session" in text


def test_employee_service_not_modified_to_select_tenant(
) -> None:
    text = Path(
        "app/modules/employees/service.py"
    ).read_text(
        encoding="utf-8"
    )

    forbidden = [
        "tenant_database_url",
        "database_name",
        "connection_string",
    ]

    for token in forbidden:
        assert token not in text