from __future__ import annotations

import importlib.util
from pathlib import Path


EXPECTED_REVISION = "a9b2c4d6e7f8"
EXPECTED_DOWN_REVISION = "f8a1c3d4e5b6"


def migration_path() -> Path:
    backend_root = (
        Path(__file__)
        .resolve()
        .parents[3]
    )

    return (
        backend_root
        / "migrations"
        / "tenant"
        / "versions"
        / "a9b2c4d6e7f8_add_work_sessions.py"
    )


def load_migration_module():
    path = migration_path()

    assert path.exists()

    specification = (
        importlib.util.spec_from_file_location(
            "phase09_work_sessions_migration",
            path,
        )
    )

    assert specification is not None
    assert specification.loader is not None

    module = (
        importlib.util.module_from_spec(
            specification
        )
    )

    specification.loader.exec_module(
        module
    )

    return module


def test_migration_revision_chain() -> None:
    module = load_migration_module()

    assert module.revision == EXPECTED_REVISION
    assert module.down_revision == EXPECTED_DOWN_REVISION


def test_migration_exposes_upgrade_and_downgrade() -> None:
    module = load_migration_module()

    assert callable(
        module.upgrade
    )

    assert callable(
        module.downgrade
    )


def test_migration_contains_work_sessions_table() -> None:
    source = migration_path().read_text(
        encoding="utf-8"
    )

    assert '"work_sessions"' in source

    assert '"device_id"' in source
    assert '"employee_id"' in source

    assert '"status"' in source
    assert '"current_state"' in source

    assert '"started_at"' in source
    assert '"ended_at"' in source
    assert '"last_observed_at"' in source

    assert '"active_seconds"' in source
    assert '"idle_seconds"' in source


def test_migration_contains_open_session_uniqueness() -> None:
    source = migration_path().read_text(
        encoding="utf-8"
    )

    assert (
        '"uq_work_sessions_one_open_per_device"'
        in source
    )

    assert (
        "status = 'open'"
        in source
    )


def test_migration_contains_required_indexes() -> None:
    source = migration_path().read_text(
        encoding="utf-8"
    )

    assert (
        '"ix_work_sessions_device_started_at"'
        in source
    )

    assert (
        '"ix_work_sessions_employee_started_at"'
        in source
    )

    assert (
        '"ix_work_sessions_status_last_observed_at"'
        in source
    )