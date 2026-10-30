from __future__ import annotations

from pathlib import Path


MIGRATION = Path(
    "migrations/tenant/versions/"
    "e4f5a6b7c8d9_add_goals_and_notes.py"
)


def text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8",
    )


def test_migration_exists() -> None:
    assert MIGRATION.exists()


def test_revision_chain() -> None:
    content = text()

    assert (
        'revision = "e4f5a6b7c8d9"'
        in content
    )

    assert (
        'down_revision = "d3e4f5a6b7c8"'
        in content
    )


def test_goals_created() -> None:
    content = text()

    assert (
        'op.create_table(\n'
        '        "goals"'
        in content
    )


def test_notes_created() -> None:
    content = text()

    assert (
        'op.create_table(\n'
        '        "notes"'
        in content
    )


def test_employee_foreign_keys() -> None:
    content = text()

    assert (
        '"employees.id"'
        in content
    )

    assert (
        "fk_goals_owner_employee_id_employees"
        in content
    )

    assert (
        "fk_notes_owner_employee_id_employees"
        in content
    )


def test_no_workspace_id() -> None:
    content = text()

    assert (
        '"workspace_id"'
        not in content
    )


def test_goal_constraints() -> None:
    content = text()

    assert "ck_goals_status" in content
    assert "ck_goals_priority" in content

    assert (
        "ck_goals_progress_percent"
        in content
    )


def test_downgrade() -> None:
    content = text()

    assert "def downgrade()" in content
    assert '"notes"' in content
    assert '"goals"' in content