from __future__ import annotations

import ast
from pathlib import Path

from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)

from tests.migration_chain_assertions import (
    assert_revision_present_in_runtime_chain,
    tenant_revision_parents,
)


# =========================================================
# PROJECT ROOT
# =========================================================


ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


# =========================================================
# PHASE 12.2 MIGRATION IDENTITY
# =========================================================


PHASE12_2_REVISION = (
    "n4i5j6k7l8m9"
)


PHASE12_2_PARENT = (
    "m3h4i5j6k7l8"
)


# =========================================================
# PATHS
# =========================================================


TENANT_ROUTER_PATH = (
    ROOT
    / "app"
    / "modules"
    / "tenant_api"
    / "router.py"
)


TENANT_ENV_PATH = (
    ROOT
    / "migrations"
    / "tenant"
    / "env.py"
)


LEAVE_ROUTER_PATH = (
    ROOT
    / "app"
    / "modules"
    / "leave"
    / "router.py"
)


TENANT_VERSIONS_PATH = (
    ROOT
    / "migrations"
    / "tenant"
    / "versions"
)


# =========================================================
# MIGRATION HELPERS
# =========================================================


def leave_migration_path() -> Path:
    """
    Find the Phase 12.2 Leave migration by revision ID.

    Do not derive the filename from the current runtime schema
    version. Later phases are allowed to advance the tenant head.
    """

    matches = list(
        TENANT_VERSIONS_PATH.glob(
            f"{PHASE12_2_REVISION}_*.py"
        )
    )

    assert len(matches) == 1, (
        "Expected exactly one Phase 12.2 "
        "Leave migration for revision "
        f"{PHASE12_2_REVISION!r}; "
        f"found {len(matches)}."
    )

    return matches[0]


def migration_assignment(
    source: str,
    name: str,
):
    """
    Read migration metadata from either:

        revision = "..."

    or:

        revision: str = "..."
    """

    tree = ast.parse(
        source
    )

    for node in tree.body:

        # -------------------------------------------------
        # name = value
        # -------------------------------------------------

        if isinstance(
            node,
            ast.Assign,
        ):
            for target in node.targets:
                if (
                    isinstance(
                        target,
                        ast.Name,
                    )
                    and target.id
                    == name
                ):
                    return ast.literal_eval(
                        node.value
                    )

        # -------------------------------------------------
        # name: str = value
        # -------------------------------------------------

        elif isinstance(
            node,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    node.target,
                    ast.Name,
                )
                and node.target.id
                == name
            ):
                assert (
                    node.value
                    is not None
                )

                return ast.literal_eval(
                    node.value
                )

    raise AssertionError(
        f"{name!r} was not found "
        "in Leave migration."
    )


def migration_operation_tables(
    *,
    operation: str,
) -> set[str]:
    """
    Extract table names passed to:

        op.create_table(...)
        op.drop_table(...)

    from the Phase 12.2 migration.
    """

    source = (
        leave_migration_path()
        .read_text(
            encoding="utf-8"
        )
    )

    tree = ast.parse(
        source
    )

    function_node = None

    for node in tree.body:
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name
            == operation
        ):
            function_node = node
            break

    assert (
        function_node
        is not None
    ), (
        f"Migration function "
        f"{operation!r} not found."
    )

    expected_call = (
        "create_table"
        if operation == "upgrade"
        else "drop_table"
    )

    tables: set[str] = set()

    for node in ast.walk(
        function_node
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if not isinstance(
            node.func,
            ast.Attribute,
        ):
            continue

        if (
            node.func.attr
            != expected_call
        ):
            continue

        if not isinstance(
            node.func.value,
            ast.Name,
        ):
            continue

        if (
            node.func.value.id
            != "op"
        ):
            continue

        if not node.args:
            continue

        first = node.args[0]

        if (
            isinstance(
                first,
                ast.Constant,
            )
            and isinstance(
                first.value,
                str,
            )
        ):
            tables.add(
                first.value
            )

    return tables


# =========================================================
# RUNTIME SCHEMA / MIGRATION ANCESTRY
# =========================================================


def test_runtime_schema_contains_phase12_2():
    """
    The global tenant head may advance in future phases.

    Phase 12.2 only requires its revision to remain in the
    ancestry of the current runtime schema.
    """

    assert_revision_present_in_runtime_chain(
        required_revision=(
            PHASE12_2_REVISION
        ),
        current_revision=(
            CURRENT_TENANT_SCHEMA_VERSION
        ),
    )


def test_phase12_2_revision_is_in_migration_graph():
    graph = (
        tenant_revision_parents()
    )

    assert (
        PHASE12_2_REVISION
        in graph
    )


# =========================================================
# PERMISSIONS
# =========================================================


def test_leave_permissions_registered():
    assert (
        WorkspacePermission
        .LEAVE_VIEW
        .value
        == "leave.view"
    )

    assert (
        WorkspacePermission
        .LEAVE_MANAGE
        .value
        == "leave.manage"
    )

    assert (
        WorkspacePermission
        .LEAVE_SELF_READ
        .value
        == "leave.self.read"
    )

    assert (
        WorkspacePermission
        .LEAVE_TEAM_READ
        .value
        == "leave.team.read"
    )

    assert (
        WorkspacePermission
        .LEAVE_ALL_READ
        .value
        == "leave.all.read"
    )

    assert (
        WorkspacePermission
        .LEAVE_APPROVE
        .value
        == "leave.approve"
    )

    assert (
        WorkspacePermission
        .LEAVE_POLICY_MANAGE
        .value
        == "leave.policy.manage"
    )

    assert (
        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value
        == "leave.balance.manage"
    )


# =========================================================
# TENANT ROUTER SOURCE REGISTRATION
# =========================================================


def test_leave_router_import_registered():
    source = (
        TENANT_ROUTER_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "app.modules.leave.router"
        in source
    )

    assert (
        "leave_router"
        in source
    )


def test_leave_router_include_registered():
    source = (
        TENANT_ROUTER_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    tree = ast.parse(
        source
    )

    found = False

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if not isinstance(
            node.func,
            ast.Attribute,
        ):
            continue

        if (
            node.func.attr
            != "include_router"
        ):
            continue

        if not node.args:
            continue

        first = node.args[0]

        if (
            isinstance(
                first,
                ast.Name,
            )
            and first.id
            == "leave_router"
        ):
            found = True
            break

    assert found


# =========================================================
# LEAVE ROUTER CONTRACT
# =========================================================


def test_leave_router_source_contains_expected_routes():
    source = (
        LEAVE_ROUTER_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    required_routes = {
        '"/me/requests"',
        '"/me/balances"',
        (
            '"/requests/'
            '{request_id}/approve"'
        ),
        (
            '"/requests/'
            '{request_id}/reject"'
        ),
        '"/types"',
        '"/policies"',
    }

    for route in required_routes:
        assert route in source


# =========================================================
# ALEMBIC MODEL REGISTRATION
# =========================================================


def test_tenant_env_registers_leave_models():
    source = (
        TENANT_ENV_PATH
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


# =========================================================
# MIGRATION EXISTS
# =========================================================


def test_leave_migration_exists():
    path = (
        leave_migration_path()
    )

    assert path.exists()

    assert (
        path.name.startswith(
            PHASE12_2_REVISION
        )
    )


# =========================================================
# MIGRATION REVISION CHAIN
# =========================================================


def test_leave_migration_revision_chain():
    source = (
        leave_migration_path()
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        migration_assignment(
            source,
            "revision",
        )
        == PHASE12_2_REVISION
    )

    assert (
        migration_assignment(
            source,
            "down_revision",
        )
        == PHASE12_2_PARENT
    )


# =========================================================
# TABLE CONTRACT
# =========================================================


def test_leave_migration_creates_required_tables():
    required_tables = {
        "leave_types",
        "leave_policies",
        "leave_balances",
        "leave_requests",
    }

    created = (
        migration_operation_tables(
            operation="upgrade"
        )
    )

    assert (
        required_tables
        <= created
    )


def test_leave_migration_drops_required_tables():
    required_tables = {
        "leave_types",
        "leave_policies",
        "leave_balances",
        "leave_requests",
    }

    dropped = (
        migration_operation_tables(
            operation="downgrade"
        )
    )

    assert (
        required_tables
        <= dropped
    )