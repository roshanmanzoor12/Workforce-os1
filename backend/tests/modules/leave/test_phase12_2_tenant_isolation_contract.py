from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read(
    relative: str,
) -> str:
    return (
        ROOT
        .joinpath(
            relative
        )
        .read_text(
            encoding="utf-8"
        )
    )


def test_leave_router_uses_tenant_scope():
    source = read(
        "app/modules/leave/router.py"
    )

    assert "TenantScope" in source


def test_integration_router_uses_tenant_scope():
    source = read(
        "app/modules/leave/"
        "integration_router.py"
    )

    assert "TenantScope" in source


def test_leave_routes_do_not_accept_database_name():
    leave_source = read(
        "app/modules/leave/router.py"
    )

    integration_source = read(
        "app/modules/leave/"
        "integration_router.py"
    )

    assert (
        "database_name:"
        not in leave_source
    )

    assert (
        "database_name:"
        not in integration_source
    )


def test_tenant_dependency_resolves_authorized_session():
    source = read(
        "app/db/tenant_dependency.py"
    )

    assert (
        "authorized_tenant_session"
        in source
    )

    assert (
        "workspace_id=workspace_id"
        in source
    )

    assert (
        "user_id=current_user.id"
        in source
    )


def test_client_cannot_supply_tenant_database_url():
    source = read(
        "app/db/tenant_dependency.py"
    )

    assert (
        "database URL"
        in source
        or "database_url"
        not in source
    )