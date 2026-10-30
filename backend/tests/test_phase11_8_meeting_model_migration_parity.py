from __future__ import annotations

from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)


def test_meeting_model_table(
) -> None:
    assert (
        Meeting.__tablename__
        == "meetings"
    )


def test_participant_model_table(
) -> None:
    assert (
        MeetingParticipant.__tablename__
        == "meeting_participants"
    )


def test_meeting_columns(
) -> None:
    columns = {
        column.name
        for column
        in Meeting.__table__.columns
    }

    assert columns == {
        "title",
        "description",
        "meeting_type",
        "status",
        "scheduled_start_at",
        "scheduled_end_at",
        "started_at",
        "ended_at",
        "location",
        "created_by_user_id",
        "id",
        "created_at",
        "updated_at",
    }


def test_participant_columns(
) -> None:
    columns = {
        column.name
        for column
        in MeetingParticipant
        .__table__
        .columns
    }

    assert columns == {
        "meeting_id",
        "employee_id",
        "participant_role",
        "status",
        "id",
        "created_at",
        "updated_at",
    }


def test_meeting_has_no_workspace_id(
) -> None:
    assert (
        "workspace_id"
        not in Meeting.__table__.columns
    )


def test_participant_has_no_workspace_id(
) -> None:
    assert (
        "workspace_id"
        not in (
            MeetingParticipant
            .__table__
            .columns
        )
    )


def test_employee_fk_matches_model(
) -> None:
    targets = {
        fk.target_fullname
        for fk
        in MeetingParticipant
        .__table__
        .columns["employee_id"]
        .foreign_keys
    }

    assert (
        targets
        == {
            "employees.id",
        }
    )


def test_meeting_fk_matches_model(
) -> None:
    targets = {
        fk.target_fullname
        for fk
        in MeetingParticipant
        .__table__
        .columns["meeting_id"]
        .foreign_keys
    }

    assert (
        targets
        == {
            "meetings.id",
        }
    )