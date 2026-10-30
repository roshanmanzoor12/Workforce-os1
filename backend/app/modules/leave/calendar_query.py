from __future__ import annotations

import uuid
from datetime import (
    date,
    timedelta,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.leave.calendar_schemas import (
    LeaveCalendarEntryResponse,
    LeaveCalendarResponse,
)
from app.modules.leave.consumption import (
    LeaveConsumptionService,
)
from app.modules.leave.models import (
    LeaveRequestStatus,
)
from app.modules.leave.repository import (
    LeaveRepository,
)


class LeaveCalendarQueryService:
    """
    Read model for self/team/workspace Leave calendars.

    Request visibility is handled by LeaveAccessService before
    this service is invoked.

    This service stays tenant-domain only.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            LeaveRepository(
                session
            )
        )

        self.consumption = (
            LeaveConsumptionService(
                session
            )
        )

    async def employee_calendar(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        status: (
            LeaveRequestStatus | None
        ) = None,
    ) -> LeaveCalendarResponse:
        if end_date < start_date:
            raise ValueError(
                "end_date cannot be "
                "before start_date."
            )

        if (
            end_date - start_date
        ).days > 366:
            raise ValueError(
                "Leave calendar range "
                "cannot exceed 367 days."
            )

        requests = await (
            self.repository.list_requests(
                employee_id=(
                    employee_id
                ),
                status=status,
                start_date=start_date,
                end_date=end_date,
            )
        )

        items: list[
            LeaveCalendarEntryResponse
        ] = []

        for leave_request in requests:
            leave_type = await (
                self.repository.get_type(
                    leave_request
                    .leave_type_id
                )
            )

            if leave_type is None:
                continue

            first_day = max(
                start_date,
                leave_request.start_date,
            )

            last_day = min(
                end_date,
                leave_request.end_date,
            )

            current = first_day

            while current <= last_day:
                consumption = await (
                    self.consumption
                    .for_employee_date(
                        employee_id=(
                            employee_id
                        ),
                        leave_date=current,
                    )
                )

                # Consumption is authoritative only for approved
                # leave. Pending/rejected/cancelled requests still
                # appear in the calendar but do not create payable
                # leave minutes.
                approved_request_match = (
                    leave_request.status
                    == LeaveRequestStatus
                    .APPROVED
                    and consumption.request_id
                    == leave_request.id
                )

                items.append(
                    LeaveCalendarEntryResponse(
                        request_id=(
                            leave_request.id
                        ),
                        employee_id=(
                            employee_id
                        ),
                        leave_type_id=(
                            leave_type.id
                        ),
                        leave_type_name=(
                            leave_type.name
                        ),
                        leave_type_code=(
                            leave_type.code
                        ),
                        calendar_date=current,
                        request_start_date=(
                            leave_request
                            .start_date
                        ),
                        request_end_date=(
                            leave_request
                            .end_date
                        ),
                        request_status=(
                            leave_request.status
                        ),
                        is_paid_leave=(
                            bool(
                                approved_request_match
                                and consumption
                                .is_paid_leave
                            )
                        ),
                        chargeable_leave_day=(
                            bool(
                                approved_request_match
                                and consumption
                                .chargeable_leave_day
                            )
                        ),
                        scheduled_minutes=(
                            consumption
                            .scheduled_minutes
                            if approved_request_match
                            else 0
                        ),
                        paid_leave_minutes=(
                            consumption
                            .paid_leave_minutes
                            if approved_request_match
                            else 0
                        ),
                        unpaid_leave_minutes=(
                            consumption
                            .unpaid_leave_minutes
                            if approved_request_match
                            else 0
                        ),
                    )
                )

                current += timedelta(
                    days=1
                )

        items.sort(
            key=lambda item: (
                item.calendar_date,
                str(
                    item.request_id
                ),
            )
        )

        return LeaveCalendarResponse(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            items=items,
            total_entries=len(
                items
            ),
        )


__all__ = [
    "LeaveCalendarQueryService",
]