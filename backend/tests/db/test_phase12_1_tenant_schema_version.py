from __future__ import annotations

import ast
from pathlib import Path

from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)


EXPECTED_HEAD = (
    "p6k7l8m9n0o1"
)


def test_current_schema_version_matches_phase12_head():
    assert (
        CURRENT_TENANT_SCHEMA_VERSION
        == EXPECTED_HEAD
    )


def test_tenant_env_registers_shift_models():
    path = (
        Path("migrations")
        / "tenant"
        / "env.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    imported_modules = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imported_modules.add(
                    node.module
                )

    assert (
        "app.modules.shifts"
        in imported_modules
    )


def test_tenant_env_registers_holiday_models():
    path = (
        Path("migrations")
        / "tenant"
        / "env.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    imported_modules = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.ImportFrom,
        ):
            if node.module:
                imported_modules.add(
                    node.module
                )

    assert (
        "app.modules.holidays"
        in imported_modules
    )
