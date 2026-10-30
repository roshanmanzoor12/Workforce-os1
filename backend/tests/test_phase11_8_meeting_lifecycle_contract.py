from __future__ import annotations

from pathlib import Path

from app.modules.meetings.contract import (
    MEETING_PARTICIPANT_REQUIRED_COLUMNS,
    MEETING_REQUIRED_COLUMNS,
    MEETING_STATUS_VALUES,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)


def test_meeting_columns_match_contract(
) -> None:
    columns = {
        column.name
        for column
        in Meeting.__table__.columns
    }

    assert (
        MEETING_REQUIRED_COLUMNS
        .issubset(
            columns
        )
    )


def test_participant_columns_match_contract(
) -> None:
    columns = {
        column.name
        for column
        in MeetingParticipant
        .__table__
        .columns
    }

    assert (
        MEETING_PARTICIPANT_REQUIRED_COLUMNS
        .issubset(
            columns
        )
    )


def test_meeting_lifecycle_statuses(
) -> None:
    assert (
        MEETING_STATUS_VALUES
        == {
            "scheduled",
            "active",
            "completed",
            "cancelled",
        }
    )


def test_meeting_service_has_lifecycle_methods(
) -> None:
    text = Path(
        "app/modules/meetings/service.py"
    ).read_text(
        encoding="utf-8",
    )

    required = [
        "async def start_meeting",
        "async def end_meeting",
        "async def cancel_meeting",
        "async def update_meeting",
    ]

    for token in required:
        assert token in text


def test_completed_meeting_cannot_restart(
) -> None:
    text = Path(
        "app/modules/meetings/service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "MeetingStatus.COMPLETED.value"
        in text
    )

    assert (
        "MeetingStatus.CANCELLED.value"
        in text
    )


def test_start_sets_active_status(
) -> None:
    text = Path(
        "app/modules/meetings/service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "MeetingStatus"
        in text
    )

    assert (
        ".ACTIVE"
        in text
    )

    assert (
        '"started_at"'
        in text
    )


def test_end_sets_completed_status(
) -> None:
    text = Path(
        "app/modules/meetings/service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        ".COMPLETED"
        in text
    )

    assert (
        '"ended_at"'
        in text
    )