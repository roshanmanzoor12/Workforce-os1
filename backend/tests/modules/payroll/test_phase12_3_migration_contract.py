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


REVISION = (
    "o5j6k7l8m9n0"
)


PARENT = (
    "n4i5j6k7l8m9"
)


EXPECTED_TABLES = {
    "compensation_contracts",
    "payroll_runs",
    "payroll_calculations",
    "payroll_adjustments",
}


def migration_file() -> Path:
    matches = list(
        VERSIONS.glob(
            f"{REVISION}_*.py"
        )
    )

    assert len(matches) == 1

    return matches[0]


def tree() -> ast.Module:
    return ast.parse(
        migration_file()
        .read_text(
            encoding="utf-8"
        )
    )


def assignment(
    name: str,
) -> Any:
    syntax = tree()

    for node in syntax.body:
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

        if isinstance(
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
        f"{name} not found"
    )


def function(
    name: str,
):
    syntax = tree()

    for node in syntax.body:
        if (
            isinstance(
                node,
                ast.FunctionDef,
            )
            and node.name == name
        ):
            return node

    raise AssertionError(
        f"{name} not found"
    )


def operation_tables(
    function_node,
    operation: str,
) -> set[str]:
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
            != operation
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


def test_revision_identity():
    assert (
        assignment(
            "revision"
        )
        == REVISION
    )


def test_revision_parent():
    assert (
        assignment(
            "down_revision"
        )
        == PARENT
    )


def test_upgrade_creates_all_tables():
    created = operation_tables(
        function(
            "upgrade"
        ),
        "create_table",
    )

    assert (
        EXPECTED_TABLES
        <= created
    )


def test_downgrade_drops_all_tables():
    dropped = operation_tables(
        function(
            "downgrade"
        ),
        "drop_table",
    )

    assert (
        EXPECTED_TABLES
        <= dropped
    )


def test_migration_has_snapshot_columns():
    source = (
        migration_file()
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        '"source_snapshot"'
        in source
    )

    assert (
        '"explanation_snapshot"'
        in source
    )

    assert (
        '"policy_version"'
        in source
    )


def test_adjustments_preserve_reason_actor():
    source = (
        migration_file()
        .read_text(
            encoding="utf-8"
        )
    )

    assert '"reason"' in source

    assert (
        '"created_by_user_id"'
        in source
    )