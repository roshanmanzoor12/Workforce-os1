from __future__ import annotations

import ast
from pathlib import Path

from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)

from tests.migration_chain_assertions import (
    assert_revision_present_in_runtime_chain,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


PAYROLL_FOUNDATION = (
    "o5j6k7l8m9n0"
)


PAYSLIP_HEAD = (
    "p6k7l8m9n0o1"
)


VERSIONS = (
    ROOT
    / "migrations"
    / "tenant"
    / "versions"
)


def _migration(
    revision: str,
) -> Path:
    matches = list(
        VERSIONS.glob(
            f"{revision}_*.py"
        )
    )

    assert len(
        matches
    ) == 1

    return matches[0]


def _assignment(
    path: Path,
    name: str,
):
    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    for node in tree.body:
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
                return ast.literal_eval(
                    node.value
                )

    raise AssertionError(
        f"{name} not found"
    )


def test_runtime_schema_is_payslip_head():
    assert (
        CURRENT_TENANT_SCHEMA_VERSION
        == PAYSLIP_HEAD
    )


def test_foundation_remains_in_chain():
    assert_revision_present_in_runtime_chain(
        required_revision=(
            PAYROLL_FOUNDATION
        ),
        current_revision=(
            CURRENT_TENANT_SCHEMA_VERSION
        ),
    )


def test_payslip_revision_identity():
    path = _migration(
        PAYSLIP_HEAD
    )

    assert (
        _assignment(
            path,
            "revision",
        )
        == PAYSLIP_HEAD
    )


def test_payslip_parent_is_payroll_foundation():
    path = _migration(
        PAYSLIP_HEAD
    )

    assert (
        _assignment(
            path,
            "down_revision",
        )
        == PAYROLL_FOUNDATION
    )


def test_payslip_migration_contains_table():
    source = (
        _migration(
            PAYSLIP_HEAD
        )
        .read_text(
            encoding="utf-8"
        )
    )

    assert (
        "payroll_payslips"
        in source
    )

    assert (
        "upgrade"
        in source
    )

    assert (
        "downgrade"
        in source
    )