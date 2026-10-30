from datetime import date

from app.modules.holidays.models import (
    HolidayTreatment,
)
from app.modules.holidays.schemas import (
    HolidayCreateRequest,
    HolidayUpdateRequest,
)


def test_create_paid_holiday():
    request = HolidayCreateRequest(
        holiday_date=date(
            2026,
            8,
            14,
        ),
        name="Independence Day",
        treatment=(
            HolidayTreatment.PAID
        ),
        region="PK",
    )

    assert (
        request.treatment
        == HolidayTreatment.PAID
    )

    assert request.region == "PK"


def test_create_unpaid_holiday():
    request = HolidayCreateRequest(
        holiday_date=date(
            2026,
            12,
            1,
        ),
        name="Company Closure",
        treatment=(
            HolidayTreatment.UNPAID
        ),
    )

    assert (
        request.treatment
        == HolidayTreatment.UNPAID
    )


def test_holiday_update_is_partial():
    request = HolidayUpdateRequest(
        is_active=False
    )

    assert (
        request.is_active
        is False
    )

    assert (
        request.holiday_date
        is None
    )