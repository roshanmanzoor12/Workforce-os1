from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.attendance.service import (
    AttendanceService,
)
from app.modules.payroll.source_schemas import (
    PayrollAttendanceSource,
)


class PayrollAttendanceSourceError(
    RuntimeError
):
    pass


def _payload(
    value,
) -> dict:
    if hasattr(
        value,
        "model_dump",
    ):
        return value.model_dump()

    if isinstance(
        value,
        dict,
    ):
        return value

    return {
        key: getattr(
            value,
            key,
        )
        for key in dir(
            value
        )
        if (
            not key.startswith(
                "_"
            )
            and not callable(
                getattr(
                    value,
                    key,
                )
            )
        )
    }


def _number(
    payload: dict,
    names: tuple[
        str,
        ...,
    ],
    *,
    default: int | None = None,
) -> int:
    for name in names:
        value = payload.get(
            name
        )

        if value is not None:
            return max(
                0,
                int(
                    value
                ),
            )

    if default is not None:
        return default

    raise PayrollAttendanceSourceError(
        "Attendance response does not expose "
        "a recognized worked-minutes field."
    )


class PayrollAttendanceSourceService:
    """
    Adapter around the existing AttendanceService.

    The Payroll domain does not trust browser-submitted worked time.

    Attendance response naming has evolved during earlier backend
    phases, therefore normalization is intentionally isolated here.
    """

    WORKED_FIELDS = (
        "worked_minutes",
        "work_minutes",
        "total_worked_minutes",
        "total_work_minutes",
    )

    OVERTIME_FIELDS = (
        "overtime_minutes",
        "approved_overtime_minutes",
        "total_overtime_minutes",
    )

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.attendance = (
            AttendanceService(
                session
            )
        )

    async def resolve(
        self,
        *,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> PayrollAttendanceSource:
        response = await (
            self.attendance
            .list_days(
                employee_id=(
                    employee_id
                ),
                start_date=(
                    period_start
                ),
                end_date=(
                    period_end
                ),
                status=None,
            )
        )

        raw_items = getattr(
            response,
            "items",
            response
            if isinstance(
                response,
                list,
            )
            else [],
        )

        actual_work_minutes = 0
        overtime_minutes = 0

        source_ids: list[str] = []

        for item in raw_items:
            data = _payload(
                item
            )

            actual_work_minutes += (
                _number(
                    data,
                    self.WORKED_FIELDS,
                    default=0,
                )
            )

            overtime_minutes += (
                _number(
                    data,
                    self.OVERTIME_FIELDS,
                    default=0,
                )
            )

            source_id = data.get(
                "id"
            )

            if source_id is not None:
                source_ids.append(
                    str(
                        source_id
                    )
                )

        return PayrollAttendanceSource(
            employee_id=employee_id,
            actual_work_minutes=(
                actual_work_minutes
            ),
            overtime_minutes=(
                overtime_minutes
            ),
            attendance_source_ids=(
                source_ids
            ),
        )


__all__ = [
    "PayrollAttendanceSourceError",
    "PayrollAttendanceSourceService",
]