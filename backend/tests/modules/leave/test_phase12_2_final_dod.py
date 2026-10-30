from __future__ import annotations

import importlib
from pathlib import Path

from app.db.tenant_base import (
    TenantBase,
)
from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)

# Import tenant model modules so metadata is populated.
from app.modules.leave import (
    models as leave_models,
)
from tests.migration_chain_assertions import (
    assert_revision_present_in_runtime_chain,
)

ROOT = Path(__file__).resolve().parents[3]


def test_runtime_schema_contains_phase12_2():
    assert_revision_present_in_runtime_chain(
        required_revision=(
            "n4i5j6k7l8m9"
        ),
        current_revision=(
            CURRENT_TENANT_SCHEMA_VERSION
        ),
    )


def test_leave_tables_registered_in_tenant_metadata():
    tables = set(
        TenantBase.metadata.tables
    )

    expected = {
        "leave_types",
        "leave_policies",
        "leave_balances",
        "leave_requests",
    }

    assert (
        expected
        <= tables
    )


def test_required_leave_modules_import():
    modules = [
        "app.modules.leave.models",
        "app.modules.leave.schemas",
        "app.modules.leave.repository",
        "app.modules.leave.balance_service",
        "app.modules.leave.calendar_service",
        "app.modules.leave.service",
        "app.modules.leave.access_service",
        "app.modules.leave.audit",
        "app.modules.leave.router",
        "app.modules.leave.consumption",
        "app.modules.leave.attendance_context",
        "app.modules.leave.payroll_context",
        "app.modules.leave.calendar_query",
        "app.modules.leave.integration_router",
    ]

    for module_name in modules:
        assert (
            importlib.import_module(
                module_name
            )
            is not None
        )


def test_tenant_alembic_env_registers_leave_models():
    source = (
        ROOT
        .joinpath(
            "migrations/tenant/env.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "app.modules.leave"
        in source
    )

    assert (
        "leave_models"
        in source
    )


def test_tenant_router_registers_leave_integration():
    source = (
        ROOT
        .joinpath(
            "app/modules/tenant_api/"
            "router.py"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "leave_router"
        in source
    )

    assert (
        "leave_integration_router"
        in source
    )


def test_phase12_2_migration_exists():
    matches = list(
        ROOT
        .joinpath(
            "migrations/tenant/"
            "versions"
        )
        .glob(
            "n4i5j6k7l8m9_*.py"
        )
    )

    assert len(matches) == 1