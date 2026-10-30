from __future__ import annotations

from pathlib import Path


MIGRATION = Path(
    "migrations/tenant/versions/"
    "d3e4f5a6b7c8_add_meetings_domain.py"
)


def migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8",
    )


def test_migration_exists(
) -> None:
    assert MIGRATION.exists()


def test_revision_chain(
) -> None:
    text = migration_text()

    assert (
        'revision = "d3e4f5a6b7c8"'
        in text
    )

    assert (
        'down_revision = "c2d3e4f5a6b7"'
        in text
    )


def test_meeting_tables_created(
) -> None:
    text = migration_text()

    assert (
        '"meetings"'
        in text
    )

    assert (
        '"meeting_participants"'
        in text
    )


def test_participant_foreign_keys(
) -> None:
    text = migration_text()

    assert (
        '"meetings.id"'
        in text
    )

    assert (
        '"employees.id"'
        in text
    )

    assert (
        'ondelete="CASCADE"'
        in text
    )


def test_unique_meeting_employee(
) -> None:
    text = migration_text()

    assert (
        "uq_meeting_participants_"
        "meeting_employee"
        in text
    )


def test_no_workspace_id(
) -> None:
    text = migration_text()

    assert (
        '"workspace_id"'
        not in text
    )


def test_downgrade_present(
) -> None:
    text = migration_text()

    assert (
        "def downgrade()"
        in text
    )

    assert (
        'op.drop_table(\n'
        '        "meeting_participants"'
        in text
    )

    assert (
        'op.drop_table(\n'
        '        "meetings"'
        in text
    )