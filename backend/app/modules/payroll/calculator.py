from __future__ import annotations

from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from app.modules.payroll.models import (
    CompensationBasis,
)
from app.modules.payroll.schemas import (
    PayrollCalculationInput,
    PayrollCalculationPreview,
)


MONEY_QUANT = Decimal(
    "0.01"
)

RATE_QUANT = Decimal(
    "0.000001"
)

MINUTE_RATE_QUANT = Decimal(
    "0.00000001"
)


def quantize_money(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )


def quantize_rate(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        RATE_QUANT,
        rounding=ROUND_HALF_UP,
    )


def quantize_minute_rate(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        MINUTE_RATE_QUANT,
        rounding=ROUND_HALF_UP,
    )


class PayrollCalculator:
    """
    Pure deterministic payroll math.

    It does not query the database.

    Schedule, attendance, leave, holiday and approval services
    prepare authoritative inputs; this calculator converts those
    inputs into authoritative monetary values.
    """

    @staticmethod
    def rates(
        *,
        basis: CompensationBasis,
        base_amount: Decimal,
        monthly_divisor_days: Decimal,
        standard_day_minutes: int,
    ) -> tuple[
        Decimal,
        Decimal,
        Decimal,
    ]:
        minutes_per_day = Decimal(
            standard_day_minutes
        )

        hours_per_day = (
            minutes_per_day
            / Decimal(
                "60"
            )
        )

        if basis == (
            CompensationBasis.MONTHLY
        ):
            daily_rate = (
                base_amount
                / monthly_divisor_days
            )

        elif basis == (
            CompensationBasis.DAILY
        ):
            daily_rate = base_amount

        elif basis == (
            CompensationBasis.HOURLY
        ):
            daily_rate = (
                base_amount
                * hours_per_day
            )

        elif basis == (
            CompensationBasis
            .FIXED_CONTRACT
        ):
            # Fixed-contract amount is interpreted as the
            # authoritative base amount for the payroll period.
            # Rate fields are still derived for transparent
            # explanation of time-based deductions/overtime.
            daily_rate = (
                base_amount
                / monthly_divisor_days
            )

        else:
            raise ValueError(
                "Unsupported compensation "
                "basis."
            )

        hourly_rate = (
            daily_rate
            / hours_per_day
        )

        minute_rate = (
            hourly_rate
            / Decimal(
                "60"
            )
        )

        return (
            quantize_rate(
                daily_rate
            ),
            quantize_rate(
                hourly_rate
            ),
            quantize_minute_rate(
                minute_rate
            ),
        )

    @classmethod
    def calculate(
        cls,
        request: PayrollCalculationInput,
    ) -> PayrollCalculationPreview:
        (
            daily_rate,
            hourly_rate,
            minute_rate,
        ) = cls.rates(
            basis=request.basis,
            base_amount=(
                request.base_amount
            ),
            monthly_divisor_days=(
                request
                .monthly_divisor_days
            ),
            standard_day_minutes=(
                request
                .standard_day_minutes
            ),
        )

        payable_minutes = max(
            0,
            (
                request
                .actual_work_minutes
                + request
                .paid_leave_minutes
            ),
        )

        # Cap normal payable units at the scheduled amount.
        # Overtime is calculated separately.
        normal_payable_minutes = min(
            payable_minutes,
            request.scheduled_minutes,
        )

        if request.basis in {
            CompensationBasis.MONTHLY,
            CompensationBasis
            .FIXED_CONTRACT,
        }:
            scheduled_base = (
                request.base_amount
            )

            unpaid_minutes = max(
                0,
                (
                    request
                    .scheduled_minutes
                    - normal_payable_minutes
                ),
            )

            unpaid_deduction = (
                minute_rate
                * Decimal(
                    unpaid_minutes
                )
            )

            base_pay = max(
                Decimal(
                    "0"
                ),
                scheduled_base
                - unpaid_deduction,
            )

        else:
            base_pay = (
                minute_rate
                * Decimal(
                    normal_payable_minutes
                )
            )

        overtime_minutes = (
            request.overtime_minutes
            if request.overtime_enabled
            else 0
        )

        overtime_pay = (
            minute_rate
            * Decimal(
                overtime_minutes
            )
            * request
            .overtime_multiplier
        )

        base_pay = quantize_money(
            base_pay
        )

        overtime_pay = quantize_money(
            overtime_pay
        )

        additions_total = (
            quantize_money(
                request
                .additions_total
            )
        )

        deductions_total = (
            quantize_money(
                request
                .deductions_total
            )
        )

        gross_pay = quantize_money(
            base_pay
            + overtime_pay
            + additions_total
        )

        net_pay = quantize_money(
            gross_pay
            - deductions_total
        )

        if net_pay < 0:
            net_pay = Decimal(
                "0.00"
            )

        return (
            PayrollCalculationPreview(
                employee_id=(
                    request.employee_id
                ),
                currency=(
                    request.currency
                    .strip()
                    .upper()
                ),
                daily_rate=(
                    daily_rate
                ),
                hourly_rate=(
                    hourly_rate
                ),
                minute_rate=(
                    minute_rate
                ),
                scheduled_minutes=(
                    request
                    .scheduled_minutes
                ),
                payable_minutes=(
                    normal_payable_minutes
                ),
                paid_leave_minutes=(
                    request
                    .paid_leave_minutes
                ),
                unpaid_leave_minutes=(
                    request
                    .unpaid_leave_minutes
                ),
                overtime_minutes=(
                    overtime_minutes
                ),
                base_pay=(
                    base_pay
                ),
                overtime_pay=(
                    overtime_pay
                ),
                additions_total=(
                    additions_total
                ),
                deductions_total=(
                    deductions_total
                ),
                gross_pay=(
                    gross_pay
                ),
                net_pay=(
                    net_pay
                ),
            )
        )


__all__ = [
    "MONEY_QUANT",
    "RATE_QUANT",
    "MINUTE_RATE_QUANT",
    "quantize_money",
    "quantize_rate",
    "quantize_minute_rate",
    "PayrollCalculator",
]