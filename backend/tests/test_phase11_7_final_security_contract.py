from __future__ import annotations

from pathlib import Path


TENANT_DEPENDENCY = Path(
    "app/modules/tenant_api/"
    "dependencies.py"
)

EMPLOYEE_ROUTER = Path(
    "app/modules/employees/"
    "router.py"
)

ATTENDANCE_ROUTER = Path(
    "app/modules/attendance/"
    "router.py"
)


def read(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8",
    )


def test_verified_user_required(
) -> None:
    text = read(
        TENANT_DEPENDENCY
    )

    assert (
        "get_current_verified_user"
        in text
    )


def test_control_membership_required(
) -> None:
    text = read(
        TENANT_DEPENDENCY
    )

    required = [
        "WorkspaceMembershipRepository",
        "get_active_for_user",
        "MEMBERSHIP_STATUS_ACTIVE",
    ]

    for token in required:
        assert token in text


def test_backend_registered_tenant_resolver_required(
) -> None:
    text = read(
        TENANT_DEPENDENCY
    )

    assert (
        "get_registered_tenant_session_resolver"
        in text
    )

    assert (
        "tenant_session = await resolver"
        in text
    )


def test_no_stale_request_state_routing(
) -> None:
    text = read(
        TENANT_DEPENDENCY
    )

    assert (
        "authorized_tenant_session"
        not in text
    )

    assert (
        "request.state"
        not in text
    )


def test_no_database_credentials_in_http_layer(
) -> None:
    files = [
        TENANT_DEPENDENCY,
        EMPLOYEE_ROUTER,
        ATTENDANCE_ROUTER,
    ]

    forbidden = [
        "postgresql://",
        "asyncpg://",
        "database_url:",
        "database_name:",
        "connection_string:",
        "tenant_password:",
    ]

    for path in files:
        text = read(
            path
        ).lower()

        for token in forbidden:
            assert token not in text


def test_employee_mutations_have_rbac(
) -> None:
    text = read(
        EMPLOYEE_ROUTER
    )

    assert (
        "EMPLOYEE_WRITE_ROLES"
        in text
    )

    assert (
        "require_employee_write_access"
        in text
    )


def test_attendance_admin_changes_have_rbac(
) -> None:
    text = read(
        ATTENDANCE_ROUTER
    )

    assert (
        "ATTENDANCE_WRITE_ROLES"
        in text
    )

    assert (
        "require_attendance_write_access"
        in text
    )