from __future__ import annotations

from pathlib import Path


MIGRATION = Path(
    "migrations/tenant/versions/"
    "f6a7b8c9d0e1_add_knowledge_entries.py"
)


def migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8",
    )


def test_migration_exists() -> None:
    assert MIGRATION.exists()


def test_revision_chain() -> None:
    content = migration_text()

    assert (
        'revision = "f6a7b8c9d0e1"'
        in content
    )

    assert (
        'down_revision = "e4f5a6b7c8d9"'
        in content
    )


def test_table_created() -> None:
    content = migration_text()

    assert (
        '"knowledge_entries"'
        in content
    )


def test_employee_fk() -> None:
    content = migration_text()

    assert (
        '"employees.id"'
        in content
    )

    assert (
        "fk_knowledge_entries_"
        "owner_employee_id_employees"
        in content.replace(
            '"\n                "',
            "",
        )
    )


def test_constraints() -> None:
    content = migration_text()

    assert (
        "ck_knowledge_entries_status"
        in content
    )

    assert (
        "ck_knowledge_entries_visibility"
        in content
    )

    assert (
        "ck_knowledge_entries_category"
        in content
    )


def test_indexes() -> None:
    content = migration_text()

    required = [
        "ix_knowledge_entries_owner",
        "ix_knowledge_entries_status",
        "ix_knowledge_entries_visibility",
        "ix_knowledge_entries_category",
    ]

    for name in required:
        assert name in content


def test_no_workspace_id() -> None:
    assert (
        '"workspace_id"'
        not in migration_text()
    )


def test_downgrade() -> None:
    content = migration_text()

    assert "def downgrade()" in content

    assert (
        'op.drop_table(\n'
        '        "knowledge_entries"'
        in content
    )