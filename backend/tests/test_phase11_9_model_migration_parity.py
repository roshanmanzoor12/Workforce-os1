from __future__ import annotations

from app.modules.goals.models import Goal
from app.modules.knowledge.models import (
    KnowledgeEntry,
)
from app.modules.notes.models import Note


def test_goal_columns() -> None:
    columns = {
        column.name
        for column
        in Goal.__table__.columns
    }

    assert columns == {
        "id",
        "owner_employee_id",
        "title",
        "description",
        "status",
        "priority",
        "progress_percent",
        "start_date",
        "due_date",
        "completed_at",
        "created_at",
        "updated_at",
    }


def test_note_columns() -> None:
    columns = {
        column.name
        for column
        in Note.__table__.columns
    }

    assert columns == {
        "id",
        "owner_employee_id",
        "title",
        "content",
        "is_pinned",
        "is_archived",
        "created_at",
        "updated_at",
    }


def test_knowledge_columns() -> None:
    columns = {
        column.name
        for column
        in KnowledgeEntry.__table__.columns
    }

    assert columns == {
        "id",
        "owner_employee_id",
        "title",
        "content",
        "category",
        "status",
        "visibility",
        "created_at",
        "updated_at",
    }


def test_goal_employee_fk() -> None:
    targets = {
        fk.target_fullname
        for fk
        in Goal.__table__
        .columns[
            "owner_employee_id"
        ]
        .foreign_keys
    }

    assert targets == {
        "employees.id",
    }


def test_note_employee_fk() -> None:
    targets = {
        fk.target_fullname
        for fk
        in Note.__table__
        .columns[
            "owner_employee_id"
        ]
        .foreign_keys
    }

    assert targets == {
        "employees.id",
    }


def test_knowledge_employee_fk() -> None:
    targets = {
        fk.target_fullname
        for fk
        in KnowledgeEntry.__table__
        .columns[
            "owner_employee_id"
        ]
        .foreign_keys
    }

    assert targets == {
        "employees.id",
    }


def test_no_duplicate_workspace_scope() -> None:
    for model in (
        Goal,
        Note,
        KnowledgeEntry,
    ):
        assert (
            "workspace_id"
            not in model.__table__.columns
        )


def test_primary_keys() -> None:
    for model in (
        Goal,
        Note,
        KnowledgeEntry,
    ):
        assert (
            model.__table__
            .primary_key
            .columns
            .keys()
            == [
                "id",
            ]
        )