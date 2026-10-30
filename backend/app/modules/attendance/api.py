from __future__ import annotations

import uuid
from datetime import date

from app.modules.attendance.access_service import (
    AttendanceAccessService,
)
from app.modules.attendance.enums import (
    AttendanceStatus,
)
from app.modules.attendance.schemas import (
    AttendanceDayUpdateRequest,
    AttendanceEventCreateRequest,
)
from app.modules.tenant_api.context import (
    AuthorizedTenantContext,
)


class AttendanceApi:
    def __init__(
        self,
        context: AuthorizedTenantContext,
    ) -> None:
        self.context = context

        self.service = AttendanceAccessService(
            workspace_id=context.workspace_id,
            actor_user_id=context.actor_user_id,
            control_session=context.control_session,
            tenant_session=context.tenant_session,
        )

    async def record_event(
        self,
        *,
        employee_id: uuid.UUID,
        request: AttendanceEventCreateRequest,
    ):
        return await self.service.record_event(
            employee_id=employee_id,
            request=request,
        )

    async def get_day(
        self,
        attendance_day_id: uuid.UUID,
    ):
        return await self.service.get_day(
            attendance_day_id=attendance_day_id
        )

    async def update_day(
        self,
        attendance_day_id: uuid.UUID,
        request: AttendanceDayUpdateRequest,
    ):
        return await self.service.update_day(
            request,
            attendance_day_id=attendance_day_id,
        )

    async def list_days(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: AttendanceStatus | None = None,
    ):
        return await self.service.list_days(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

    async def employee_summary(
        self,
        *,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ):
        return await self.service.employee_summary(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )


__all__ = [
    "AttendanceApi",
]