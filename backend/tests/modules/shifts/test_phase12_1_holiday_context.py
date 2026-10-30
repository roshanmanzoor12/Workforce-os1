from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.holidays.models import (
    HolidayTreatment,
)
from app.modules.shifts.holiday_context import (
    ShiftHolidayContextService,
)
from app.modules.shifts.schemas import (
    ResolvedScheduleDayResponse,
)


EMPLOYEE_ID = uuid.UUID(
    "11111111-1111-1111-"
    "1111-111111111111"
)

HOLIDAY_ID = uuid.UUID(
    "22222222-2222-2222-"
    "2222-222222222222"
)


@pytest.mark.asyncio
async def test_no_holiday_keeps_day_unchanged():
    service = object.__new__(
        ShiftHolidayContextService
    )

    service.holidays = (
        SimpleNamespace(
            resolve_workspace_holiday_for_date=(
                AsyncMock(
                    return_value=None
                )
            )
        )
    )

    day = (
        ResolvedScheduleDayResponse(
            employee_id=EMPLOYEE_ID,
            schedule_date=(
                date(
                    2026,
                    12,
                    1,
                )
            ),
            source=(
                "employee_assignment"
            ),
            scheduled_minutes=480,
            payable_minutes=480,
            is_working_day=True,
        )
    )

    result = await service.apply(
        day
    )

    assert result.is_holiday is False
    assert result.holiday_id is None
    assert result.holiday_name is None
    assert (
        result.holiday_treatment
        is None
    )

    assert (
        result.payable_minutes
        == 480
    )


@pytest.mark.asyncio
async def test_paid_holiday_adds_metadata():
    service = object.__new__(
        ShiftHolidayContextService
    )

    holiday = SimpleNamespace(
        id=HOLIDAY_ID,
        name="Founders Day",
        treatment=(
            HolidayTreatment.PAID
        ),
    )

    service.holidays = (
        SimpleNamespace(
            resolve_workspace_holiday_for_date=(
                AsyncMock(
                    return_value=holiday
                )
            )
        )
    )

    day = (
        ResolvedScheduleDayResponse(
            employee_id=EMPLOYEE_ID,
            schedule_date=(
                date(
                    2026,
                    12,
                    2,
                )
            ),
            source=(
                "team_assignment"
            ),
            scheduled_minutes=480,
            payable_minutes=480,
            is_working_day=True,
        )
    )

    result = await service.apply(
        day
    )

    assert result.is_holiday is True

    assert (
        result.holiday_id
        == HOLIDAY_ID
    )

    assert (
        result.holiday_name
        == "Founders Day"
    )

    assert (
        result.holiday_treatment
        == HolidayTreatment.PAID
    )


@pytest.mark.asyncio
async def test_holiday_context_does_not_change_payable_minutes():
    service = object.__new__(
        ShiftHolidayContextService
    )

    holiday = SimpleNamespace(
        id=HOLIDAY_ID,
        name="Unpaid Holiday",
        treatment=(
            HolidayTreatment.UNPAID
        ),
    )

    service.holidays = (
        SimpleNamespace(
            resolve_workspace_holiday_for_date=(
                AsyncMock(
                    return_value=holiday
                )
            )
        )
    )

    day = (
        ResolvedScheduleDayResponse(
            employee_id=EMPLOYEE_ID,
            schedule_date=(
                date(
                    2026,
                    12,
                    3,
                )
            ),
            source=(
                "employee_assignment"
            ),
            scheduled_minutes=480,
            payable_minutes=480,
            is_working_day=True,
        )
    )

    result = await service.apply(
        day
    )

    assert result.is_holiday is True

    assert (
        result.holiday_treatment
        == HolidayTreatment.UNPAID
    )

    # Scheduling exposes policy context.
    # Payroll decides monetary/payable treatment.
    assert (
        result.payable_minutes
        == 480
    )