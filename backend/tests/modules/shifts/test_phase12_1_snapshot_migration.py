from __future__ import annotations

import ast
from pathlib import Path


MIGRATION = (
    Path("migrations")
    / "tenant"
    / "versions"
    / (
        "m3h4i5j6k7l8_"
        "phase12_1_schedule_"
        "publication_snapshots.py"
    )
)


def text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8"
    )


def test_snapshot_migration_exists():
    assert MIGRATION.exists()


def test_snapshot_migration_parses():
    ast.parse(
        text()
    )


def test_snapshot_revision():
    source = text()

    assert "m3h4i5j6k7l8" in source
    assert "l2g3h4i5j6k7" in source


def test_snapshot_table_created():
    assert (
        "schedule_publication_days"
        in text()
    )


def test_snapshot_unique_contract():
    source = text()

    assert (
        "uq_schedule_publication_day_"
        in source
    )

    assert (
        "publication_employee_date"
        in source
    )


def test_snapshot_downgrade():
    assert (
        "def downgrade()"
        in text()
    )