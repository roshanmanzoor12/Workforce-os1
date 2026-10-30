from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.leave.balance_service import (
    LeaveBalanceService,
)
from app.modules.leave.calendar_service import (
    LeaveCalendarService,
)


def test_single_day_leave_counts_as_one():
    result = (
        LeaveCalendarService
        .inclusive_calendar_days(
            start_date=date(
                2026,
                10,
                1,
            ),
            end_date=date(
                2026,
                10,
                1,
            ),
        )
    )

    assert result == Decimal("1")


def test_multi_day_leave_is_inclusive():
    result = (
        LeaveCalendarService
        .inclusive_calendar_days(
            start_date=date(
                2026,
                10,
                1,
            ),
            end_date=date(
                2026,
                10,
                5,
            ),
        )
    )

    assert result == Decimal("5")


def test_invalid_leave_range_rejected():
    with pytest.raises(
        ValueError
    ):
        (
            LeaveCalendarService
            .inclusive_calendar_days(
                start_date=date(
                    2026,
                    10,
                    5,
                ),
                end_date=date(
                    2026,
                    10,
                    1,
                ),
            )
        )


def test_available_balance_math():
    balance = SimpleNamespace(
        allocated_days=(
            Decimal("20")
        ),
        carried_forward_days=(
            Decimal("2")
        ),
        adjustment_days=(
            Decimal("1")
        ),
        used_days=(
            Decimal("6")
        ),
        pending_days=(
            Decimal("3")
        ),
    )

    assert (
        LeaveBalanceService
        .available_days(
            balance
        )
        == Decimal("14")
    )