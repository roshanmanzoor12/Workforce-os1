from __future__ import annotations

import uuid
from types import (
    SimpleNamespace,
)

from app.modules.shifts.access_service import (
    ShiftAccessService,
)


def employee(
    *,
    employee_id: str,
    user_id: str | None = None,
    team_id: str | None = None,
    manager_id: str | None = None,
):
    return SimpleNamespace(
        id=uuid.UUID(
            employee_id
        ),
        user_id=(
            uuid.UUID(user_id)
            if user_id
            else None
        ),
        team_id=(
            uuid.UUID(team_id)
            if team_id
            else None
        ),
        manager_id=(
            uuid.UUID(manager_id)
            if manager_id
            else None
        ),
        is_active=True,
    )


ACTOR_ID = (
    "11111111-1111-1111-"
    "1111-111111111111"
)

TARGET_ID = (
    "22222222-2222-2222-"
    "2222-222222222222"
)

TEAM_ID = (
    "33333333-3333-3333-"
    "3333-333333333333"
)

OTHER_TEAM_ID = (
    "44444444-4444-4444-"
    "4444-444444444444"
)


def test_self_target():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_self_target(
            actor=actor,
            target=actor,
        )
        is True
    )


def test_other_employee_is_not_self():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    target = employee(
        employee_id=TARGET_ID,
        team_id=TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_self_target(
            actor=actor,
            target=target,
        )
        is False
    )


def test_direct_report_is_team_scope():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    target = employee(
        employee_id=TARGET_ID,
        team_id=OTHER_TEAM_ID,
        manager_id=ACTOR_ID,
    )

    assert (
        ShiftAccessService
        .is_team_target(
            actor=actor,
            target=target,
        )
        is True
    )


def test_same_team_is_team_scope():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    target = employee(
        employee_id=TARGET_ID,
        team_id=TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_team_target(
            actor=actor,
            target=target,
        )
        is True
    )


def test_different_team_is_not_team_scope():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    target = employee(
        employee_id=TARGET_ID,
        team_id=OTHER_TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_team_target(
            actor=actor,
            target=target,
        )
        is False
    )


def test_actor_is_not_own_team_target():
    actor = employee(
        employee_id=ACTOR_ID,
        team_id=TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_team_target(
            actor=actor,
            target=actor,
        )
        is False
    )


def test_unlinked_actor_has_no_team_scope():
    target = employee(
        employee_id=TARGET_ID,
        team_id=TEAM_ID,
    )

    assert (
        ShiftAccessService
        .is_team_target(
            actor=None,
            target=target,
        )
        is False
    )