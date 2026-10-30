from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION_PATH = (
    Path(__file__)
    .resolve()
    .parents[3]
    / "migrations"
    / "tenant"
    / "versions"
    / "f8a1c3d4e5b6_add_activity_state_events.py"
)


def load_migration_module():
    assert MIGRATION_PATH.exists()

    specification = (
        importlib.util
        .spec_from_file_location(
            "phase08_activity_migration",
            MIGRATION_PATH,
        )
    )

    assert specification is not None
    assert specification.loader is not None

    module = (
        importlib.util
        .module_from_spec(
            specification
        )
    )

    specification.loader.exec_module(
        module
    )

    return module


def test_activity_migration_revision() -> None:
    migration = load_migration_module()

    assert (
        migration.revision
        == "f8a1c3d4e5b6"
    )


def test_activity_migration_parent() -> None:
    migration = load_migration_module()

    assert (
        migration.down_revision
        == "c5e4d7a91b26"
    )


def test_activity_migration_has_upgrade() -> None:
    migration = load_migration_module()

    assert callable(
        migration.upgrade
    )


def test_activity_migration_has_downgrade() -> None:
    migration = load_migration_module()

    assert callable(
        migration.downgrade
    )