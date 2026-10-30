from __future__ import annotations

from pathlib import Path


DEPENDENCY_FILE = Path(
    "app/modules/tenant_api/dependencies.py"
)

EMPLOYEE_ROUTER_FILE = Path(
    "app/modules/employees/router.py"
)

ATTENDANCE_ROUTER_FILE = Path(
    "app/modules/attendance/router.py"
)


def read(
    path: Path,
) -> str:
    return path.read_text(
        encoding="utf-8",
    )


def test_rest_dependencies_require_verified_user(
) -> None:
    text = read(
        DEPENDENCY_FILE
    )

    assert (
        "get_current_verified_user"
        in text
    )


def test_rest_dependencies_use_control_db(
) -> None:
    text = read(
        DEPENDENCY_FILE
    )

    assert (
        "get_control_db"
        in text
    )


def test_rest_dependencies_validate_workspace_membership(
) -> None:
    text = read(
        DEPENDENCY_FILE
    )

    required = [
        "WorkspaceMembershipRepository",
        "get_active_for_user",
        "MEMBERSHIP_STATUS_ACTIVE",
    ]

    for token in required:
        assert token in text


def test_context_uses_registered_tenant_resolver(
) -> None:
    """
    Current canonical tenant-routing contract:

        verified user
        -> active WorkspaceMembership
        -> registered backend resolver
        -> tenant AsyncSession

    request.state.authorized_tenant_session is intentionally
    NOT part of this architecture.
    """

    text = read(
        DEPENDENCY_FILE
    )

    required = [
        "get_registered_tenant_session_resolver",
        "resolver =",
        "tenant_session = await resolver",
        "AsyncSession",
        "AuthorizedTenantContext",
    ]

    for token in required:
        assert token in text


def test_context_does_not_depend_on_request_state_session(
) -> None:
    text = read(
        DEPENDENCY_FILE
    )

    assert (
        "authorized_tenant_session"
        not in text
    )

    assert (
        "request.state"
        not in text
    )


def test_frontend_does_not_supply_db_coordinates(
) -> None:
    files = [
        DEPENDENCY_FILE,
        EMPLOYEE_ROUTER_FILE,
        ATTENDANCE_ROUTER_FILE,
    ]

    forbidden = [
        "database_url:",
        "database_name:",
        "connection_string:",
        "tenant_password:",
        "postgresql://",
        "asyncpg://",
    ]

    for path in files:
        text = read(
            path
        ).lower()

        for token in forbidden:
            assert token not in text


def test_employee_router_uses_trusted_tenant_scope(
) -> None:
    text = read(
        EMPLOYEE_ROUTER_FILE
    )

    assert (
        "TenantScope"
        in text
    )

    assert (
        "scope.session"
        in text
    )


def test_attendance_router_uses_trusted_tenant_scope(
) -> None:
    text = read(
        ATTENDANCE_ROUTER_FILE
    )

    assert (
        "TenantScope"
        in text
    )

    assert (
        "scope.session"
        in text
    )


def test_employee_mutations_require_manager_role(
) -> None:
    text = read(
        EMPLOYEE_ROUTER_FILE
    )

    assert (
        "EMPLOYEE_WRITE_ROLES"
        in text
    )

    assert (
        "owner"
        in text
    )

    assert (
        "admin"
        in text
    )

    assert (
        "require_employee_write_access"
        in text
    )


def test_attendance_admin_mutations_require_manager_role(
) -> None:
    text = read(
        ATTENDANCE_ROUTER_FILE
    )

    assert (
        "ATTENDANCE_WRITE_ROLES"
        in text
    )

    assert (
        "owner"
        in text
    )

    assert (
        "admin"
        in text
    )

    assert (
        "require_attendance_write_access"
        in text
    )


def test_tenant_dependency_returns_authorized_context(
) -> None:
    text = read(
        DEPENDENCY_FILE
    )

    required = [
        "workspace_id=workspace_id",
        "actor_user_id=actor_user_id",
        "control_session=control_session",
        "tenant_session=tenant_session",
    ]

    for token in required:
        assert token in text