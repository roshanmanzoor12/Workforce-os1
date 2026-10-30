from __future__ import annotations

import uuid
from decimal import Decimal

from app.modules.payroll.calculator import (
    PayrollCalculator,
)
from app.modules.payroll.models import (
    CompensationBasis,
)
from app.modules.payroll.schemas import (
    PayrollCalculationInput,
)


def request(
    **overrides,
) -> PayrollCalculationInput:
    values = {
        "employee_id": uuid.uuid4(),
        "compensation_contract_id": (
            uuid.uuid4()
        ),
        "basis": (
            CompensationBasis.MONTHLY
        ),
        "base_amount": Decimal(
            "150000"
        ),
        "currency": "PKR",
        "standard_day_minutes": 480,
        "monthly_divisor_days": Decimal(
            "22"
        ),
        "overtime_multiplier": Decimal(
            "1.5"
        ),
        "overtime_enabled": True,
        "scheduled_minutes": (
            22 * 480
        ),
        "actual_work_minutes": (
            22 * 480
        ),
        "paid_leave_minutes": 0,
        "unpaid_leave_minutes": 0,
        "overtime_minutes": 0,
        "additions_total": Decimal(
            "0"
        ),
        "deductions_total": Decimal(
            "0"
        ),
    }

    values.update(
        overrides
    )

    return PayrollCalculationInput(
        **values
    )


def test_monthly_150k_rates():
    result = (
        PayrollCalculator
        .calculate(
            request()
        )
    )

    assert result.daily_rate == Decimal(
        "6818.181818"
    )

    assert result.hourly_rate == Decimal(
        "852.272727"
    )

    assert result.minute_rate == Decimal(
        "14.20454545"
    )


def test_monthly_full_period_base_pay():
    result = (
        PayrollCalculator
        .calculate(
            request()
        )
    )

    assert result.base_pay == Decimal(
        "150000.00"
    )

    assert result.net_pay == Decimal(
        "150000.00"
    )


def test_one_unpaid_day_reduces_monthly_pay():
    result = (
        PayrollCalculator
        .calculate(
            request(
                actual_work_minutes=(
                    21 * 480
                ),
                unpaid_leave_minutes=480,
            )
        )
    )

    assert result.base_pay == Decimal(
        "143181.82"
    )


def test_paid_leave_is_payable():
    result = (
        PayrollCalculator
        .calculate(
            request(
                actual_work_minutes=(
                    21 * 480
                ),
                paid_leave_minutes=480,
            )
        )
    )

    assert result.base_pay == Decimal(
        "150000.00"
    )


def test_overtime_uses_multiplier():
    result = (
        PayrollCalculator
        .calculate(
            request(
                overtime_minutes=60,
            )
        )
    )

    assert result.overtime_pay == Decimal(
        "1278.41"
    )


def test_disabled_overtime_is_zero():
    result = (
        PayrollCalculator
        .calculate(
            request(
                overtime_enabled=False,
                overtime_minutes=120,
            )
        )
    )

    assert result.overtime_minutes == 0
    assert result.overtime_pay == Decimal(
        "0.00"
    )


def test_additions_and_deductions():
    result = (
        PayrollCalculator
        .calculate(
            request(
                additions_total=Decimal(
                    "5000"
                ),
                deductions_total=Decimal(
                    "1000"
                ),
            )
        )
    )

    assert result.gross_pay == Decimal(
        "155000.00"
    )

    assert result.net_pay == Decimal(
        "154000.00"
    )


def test_hourly_basis():
    result = (
        PayrollCalculator
        .calculate(
            request(
                basis=(
                    CompensationBasis
                    .HOURLY
                ),
                base_amount=Decimal(
                    "1000"
                ),
                scheduled_minutes=480,
                actual_work_minutes=480,
            )
        )
    )

    assert result.hourly_rate == Decimal(
        "1000.000000"
    )

    assert result.base_pay == Decimal(
        "8000.00"
    )