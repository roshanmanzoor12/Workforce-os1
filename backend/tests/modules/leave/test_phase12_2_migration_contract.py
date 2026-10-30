from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

VERSIONS = (
    ROOT
    / "migrations"
    / "tenant"
    / "versions"
)

REVISION = "n4i5j6k7l8m9"

EXPECTED_TABLES = {
    "leave_types",
    "leave_policies",
    "leave_balances",
    "leave_requests",
}


# =========================================================
# MIGRATION FILE
# =========================================================


def migration_file() -> Path:
    matches = list(
        VERSIONS.glob(
            f"{REVISION}_*.py"
        )
    )

    assert len(matches) == 1, (
        "Expected exactly one migration "
        f"for revision {REVISION}; "
        f"found {len(matches)}."
    )

    return matches[0]


def migration_source() -> str:
    return (
        migration_file()
        .read_text(
            encoding="utf-8"
        )
    )


def migration_tree() -> ast.Module:
    return ast.parse(
        migration_source()
    )


# =========================================================
# ASSIGNMENT EXTRACTION
# =========================================================


def _literal_value(
    node: ast.AST,
) -> Any:
    try:
        return ast.literal_eval(
            node
        )

    except (
        ValueError,
        TypeError,
    ) as exc:
        raise AssertionError(
            "Migration metadata assignment "
            "is not a literal value."
        ) from exc


def assignment_value(
    tree: ast.Module,
    name: str,
) -> Any:
    """
    Support both common Alembic forms:

        revision = "..."
        revision: str = "..."

    as well as Optional[str] / Union typing.
    """

    for node in tree.body:

        # ---------------------------------------------
        # NORMAL ASSIGNMENT
        # ---------------------------------------------

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
                    and target.id == name
                ):
                    return _literal_value(
                        node.value
                    )

        # ---------------------------------------------
        # ANNOTATED ASSIGNMENT
        # ---------------------------------------------

        if isinstance(
            node,
            ast.AnnAssign,
        ):
            target = node.target

            if (
                isinstance(
                    target,
                    ast.Name,
                )
                and target.id == name
            ):
                if node.value is None:
                    raise AssertionError(
                        f"{name} has no value."
                    )

                return _literal_value(
                    node.value
                )

    raise AssertionError(
        f"{name} not found."
    )


# =========================================================
# FUNCTION EXTRACTION
# =========================================================


def function_node(
    tree: ast.Module,
    name: str,
) -> (
    ast.FunctionDef
    | ast.AsyncFunctionDef
):
    for node in tree.body:
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"{name}() not found."
    )


# =========================================================
# OPERATION EXTRACTION
# =========================================================


def _call_name(
    node: ast.Call,
) -> str | None:
    """
    Resolve calls such as:

        op.create_table(...)
        op.drop_table(...)
    """

    function = node.func

    if not isinstance(
        function,
        ast.Attribute,
    ):
        return None

    if not isinstance(
        function.value,
        ast.Name,
    ):
        return None

    if (
        function.value.id
        != "op"
    ):
        return None

    return function.attr


def _first_string_argument(
    node: ast.Call,
) -> str | None:
    if not node.args:
        return None

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
        return first.value

    return None


def operation_tables(
    function: (
        ast.FunctionDef
        | ast.AsyncFunctionDef
    ),
    operation: str,
) -> set[str]:
    result: set[str] = set()

    for node in ast.walk(
        function
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if (
            _call_name(
                node
            )
            != operation
        ):
            continue

        table_name = (
            _first_string_argument(
                node
            )
        )

        if table_name:
            result.add(
                table_name
            )

    return result


# =========================================================
# TESTS
# =========================================================


def test_leave_revision_identity():
    tree = migration_tree()

    assert (
        assignment_value(
            tree,
            "revision",
        )
        == REVISION
    )


def test_leave_revision_has_parent():
    tree = migration_tree()

    parent = (
        assignment_value(
            tree,
            "down_revision",
        )
    )

    assert isinstance(
        parent,
        str,
    )

    assert parent.strip()

    assert parent != REVISION


def test_upgrade_function_exists():
    tree = migration_tree()

    upgrade = function_node(
        tree,
        "upgrade",
    )

    assert upgrade is not None


def test_downgrade_function_exists():
    tree = migration_tree()

    downgrade = function_node(
        tree,
        "downgrade",
    )

    assert downgrade is not None


def test_all_leave_tables_created():
    tree = migration_tree()

    upgrade = function_node(
        tree,
        "upgrade",
    )

    created = operation_tables(
        upgrade,
        "create_table",
    )

    missing = (
        EXPECTED_TABLES
        - created
    )

    assert not missing, (
        "Leave migration does not create: "
        + ", ".join(
            sorted(
                missing
            )
        )
    )


def test_all_leave_tables_dropped_on_downgrade():
    tree = migration_tree()

    downgrade = function_node(
        tree,
        "downgrade",
    )

    dropped = operation_tables(
        downgrade,
        "drop_table",
    )

    missing = (
        EXPECTED_TABLES
        - dropped
    )

    assert not missing, (
        "Leave downgrade does not drop: "
        + ", ".join(
            sorted(
                missing
            )
        )
    )


def test_revision_metadata_is_consistent():
    tree = migration_tree()

    revision = assignment_value(
        tree,
        "revision",
    )

    parent = assignment_value(
        tree,
        "down_revision",
    )

    assert revision == REVISION
    assert isinstance(
        parent,
        str,
    )
    assert parent != revision