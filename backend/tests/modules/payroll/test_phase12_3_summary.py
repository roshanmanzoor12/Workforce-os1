from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.modules.payroll.models import (
    PayrollCalculation,
    PayrollCalculationStatus,
    PayrollRun,
    PayrollRunStatus,
)
from app.modules.payroll.summary import (
    PayrollSummaryBuilder,
)


def build_run():
    return PayrollRun(
        id=uuid.uuid4(),
        period_start=date(
            2026,
            9,
            1,
        ),
        period_end=date(
            2026,
            9,
            30,
        ),
        currency="PKR",
        status=(
            PayrollRunStatus.REVIEW
        ),
        policy_version=(
            "phase12.3-v1"
        ),
    )


def row(
    *,
    net_pay: str,
    gross_pay: str,
):
    return PayrollCalculation(
        id=uuid.uuid4(),
        payroll_run_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        compensation_contract_id=(
            uuid.uuid4()
        ),
        status=(
            PayrollCalculationStatus
            .CALCULATED
        ),
        currency="PKR",
        base_amount=Decimal(
            "150000"
        ),
        daily_rate=Decimal(
            "6818.18"
        ),
        hourly_rate=Decimal(
            "852.27"
        ),
        minute_rate=Decimal(
            "14.20"
        ),
        scheduled_minutes=10560,
        payable_minutes=10080,
        paid_leave_minutes=480,
        unpaid_leave_minutes=0,
        overtime_minutes=60,
        base_pay=Decimal(
            "150000"
        ),
        overtime_pay=Decimal(
            "1278.41"
        ),
        additions_total=Decimal(
            "5000"
        ),
        deductions_total=Decimal(
            "1000"
        ),
        gross_pay=Decimal(
            gross_pay
        ),
        net_pay=Decimal(
            net_pay
        ),
        source_snapshot={},
        explanation_snapshot={},
        policy_version=(
            "phase12.3-v1"
        ),
    )


def test_summary_empty():
    result = (
        PayrollSummaryBuilder.build(
            run=build_run(),
            calculations=[],
        )
    )

    assert result.employees == 0
    assert result.net_pay == Decimal(
        "0"
    )


def test_summary_totals():
    result = (
        PayrollSummaryBuilder.build(
            run=build_run(),
            calculations=[
                row(
                    gross_pay="154000",
                    net_pay="153000",
                ),
                row(
                    gross_pay="160000",
                    net_pay="158000",
                ),
            ],
        )
    )

    assert result.employees == 2

    assert result.gross_pay == Decimal(
        "314000"
    )

    assert result.net_pay == Decimal(
        "311000"
    )

    assert (
        result.overtime_minutes
        == 120
    )

    assert (
        result.paid_leave_minutes
        == 960
    )