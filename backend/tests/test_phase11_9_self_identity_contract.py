from __future__ import annotations

from pathlib import Path


GOAL_SELF = Path(
    "app/modules/goals/self_service.py"
)

NOTE_SELF = Path(
    "app/modules/notes/self_service.py"
)


def test_goal_self_service_uses_user_link() -> None:
    text = GOAL_SELF.read_text(
        encoding="utf-8",
    )

    assert "Employee.user_id" in text
    assert "actor_user_id" in text

    assert (
        "employee.id"
        in text
    )


def test_note_self_service_uses_user_link() -> None:
    text = NOTE_SELF.read_text(
        encoding="utf-8",
    )

    assert "Employee.user_id" in text
    assert "actor_user_id" in text

    assert (
        "employee.id"
        in text
    )


def test_goal_self_create_overrides_owner() -> None:
    text = GOAL_SELF.read_text(
        encoding="utf-8",
    )

    assert (
        "owner_employee_id=("
        in text
    )

    assert (
        "employee.id"
        in text
    )


def test_note_self_create_overrides_owner() -> None:
    text = NOTE_SELF.read_text(
        encoding="utf-8",
    )

    assert (
        "owner_employee_id=("
        in text
    )

    assert (
        "employee.id"
        in text
    )


def test_self_services_do_not_accept_database_name() -> None:
    goal_text = GOAL_SELF.read_text(
        encoding="utf-8",
    )

    note_text = NOTE_SELF.read_text(
        encoding="utf-8",
    )

    assert (
        "database_name"
        not in goal_text
    )

    assert (
        "database_name"
        not in note_text
    )


def test_self_services_do_not_use_request_state() -> None:
    goal_text = GOAL_SELF.read_text(
        encoding="utf-8",
    )

    note_text = NOTE_SELF.read_text(
        encoding="utf-8",
    )

    assert (
        "request.state"
        not in goal_text
    )

    assert (
        "request.state"
        not in note_text
    )