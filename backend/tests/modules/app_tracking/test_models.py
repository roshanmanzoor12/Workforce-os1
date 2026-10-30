from __future__ import annotations

from app.modules.app_tracking.models import (
    AppObservation,
    AppUsageInterval,
)


def test_app_observation_table_name() -> None:
    assert (
        AppObservation.__tablename__
        == "app_observations"
    )


def test_app_usage_interval_table_name() -> None:
    assert (
        AppUsageInterval.__tablename__
        == "app_usage_intervals"
    )


def test_app_observation_columns() -> None:
    columns = {
        column.name
        for column
        in AppObservation.__table__.columns
    }

    assert columns == {
        "id",
        "device_id",
        "employee_id",
        "app_key",
        "process_name",
        "executable_path",
        "window_title",
        "observed_at",
        "received_at",
        "created_at",
    }


def test_app_usage_interval_columns() -> None:
    columns = {
        column.name
        for column
        in AppUsageInterval.__table__.columns
    }

    assert columns == {
        "id",
        "device_id",
        "employee_id",
        "app_key",
        "process_name",
        "executable_path",
        "last_window_title",
        "status",
        "started_at",
        "ended_at",
        "last_observed_at",
        "duration_seconds",
        "created_at",
        "updated_at",
    }


def test_app_usage_interval_indexes() -> None:
    names = {
        index.name
        for index
        in AppUsageInterval.__table__.indexes
    }

    assert (
        "ix_app_usage_intervals_device_started_at"
        in names
    )

    assert (
        "ix_app_usage_intervals_employee_started_at"
        in names
    )

    assert (
        "ix_app_usage_intervals_app_key_started_at"
        in names
    )

    assert (
        "uq_app_usage_one_open_per_device"
        in names
    )


def test_app_usage_interval_constraints() -> None:
    names = {
        constraint.name
        for constraint
        in AppUsageInterval.__table__.constraints
        if constraint.name is not None
    }

    assert any(
        name.endswith(
            "ck_app_usage_intervals_status"
        )
        for name in names
    )

    assert any(
        name.endswith(
            "ck_app_usage_intervals_duration_nonnegative"
        )
        for name in names
    )

    assert any(
        name.endswith(
            "ck_app_usage_intervals_valid_time_range"
        )
        for name in names
    )