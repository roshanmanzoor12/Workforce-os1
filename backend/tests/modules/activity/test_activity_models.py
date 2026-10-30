from __future__ import annotations

from sqlalchemy import CheckConstraint, Index

from app.modules.activity.models import (
    ACTIVITY_STATE_ACTIVE,
    ACTIVITY_STATE_IDLE,
    ActivityStateEvent,
)


def test_activity_state_constants() -> None:
    assert (
        ACTIVITY_STATE_ACTIVE
        == "active"
    )

    assert (
        ACTIVITY_STATE_IDLE
        == "idle"
    )


def test_activity_table_name() -> None:
    assert (
        ActivityStateEvent.__tablename__
        == "activity_state_events"
    )


def test_activity_table_contains_expected_columns() -> None:
    columns = {
        column.name
        for column
        in ActivityStateEvent.__table__.columns
    }

    expected = {
        "id",
        "device_id",
        "employee_id",
        "state",
        "idle_seconds",
        "last_input_at",
        "observed_at",
        "received_at",
        "created_at",
    }

    assert expected <= columns


def test_activity_state_check_constraint_exists() -> None:
    constraints = [
        constraint
        for constraint
        in ActivityStateEvent
        .__table__
        .constraints
        if isinstance(
            constraint,
            CheckConstraint,
        )
    ]

    names = {
        constraint.name
        for constraint
        in constraints
        if constraint.name is not None
    }

    assert any(
        name.endswith(
            "ck_activity_state_events_state"
        )
        for name in names
    )


def test_activity_idle_seconds_constraint_exists() -> None:
    constraints = [
        constraint
        for constraint
        in ActivityStateEvent
        .__table__
        .constraints
        if isinstance(
            constraint,
            CheckConstraint,
        )
    ]

    names = {
        constraint.name
        for constraint
        in constraints
        if constraint.name is not None
    }

    assert any(
        name.endswith(
            "ck_activity_state_events_idle_seconds_nonnegative"
        )
        for name in names
    )


def test_activity_expected_indexes_exist() -> None:
    indexes = {
        index.name
        for index
        in ActivityStateEvent
        .__table__
        .indexes
        if isinstance(
            index,
            Index,
        )
    }

    assert (
        "ix_activity_state_events_device_observed_at"
        in indexes
    )

    assert (
        "ix_activity_state_events_employee_observed_at"
        in indexes
    )

    assert (
        "ix_activity_state_events_received_at"
        in indexes
    )