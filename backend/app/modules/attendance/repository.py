from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.orm import selectinload

from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)


class AttendanceRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_record(
        self,
        *,
        employee_id: uuid.UUID,
        attendance_date: date,
        status: str,
        source: str,
        actor_user_id: uuid.UUID | None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            employee_id=employee_id,
            attendance_date=attendance_date,
            status=status,
            source=source,
            worked_minutes=0,
            break_minutes=0,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )

        self.session.add(
            record
        )

        await self.session.flush()
        await self.session.refresh(
            record
        )

        return record

    async def get_record_by_id(
        self,
        attendance_record_id: uuid.UUID,
    ) -> AttendanceRecord | None:
        result = await self.session.execute(
            select(
                AttendanceRecord
            )
            .options(
                selectinload(
                    AttendanceRecord.events
                )
            )
            .where(
                AttendanceRecord.id
                == attendance_record_id
            )
        )

        return result.scalar_one_or_none()

    async def get_record(
        self,
        *,
        employee_id: uuid.UUID,
        attendance_date: date,
    ) -> AttendanceRecord | None:
        result = await self.session.execute(
            select(
                AttendanceRecord
            )
            .options(
                selectinload(
                    AttendanceRecord.events
                )
            )
            .where(
                AttendanceRecord.employee_id
                == employee_id,
                AttendanceRecord.attendance_date
                == attendance_date,
            )
        )

        return result.scalar_one_or_none()

    async def list_records(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str | None = None,
    ) -> Sequence[
        AttendanceRecord
    ]:
        statement = select(
            AttendanceRecord
        )

        if employee_id is not None:
            statement = statement.where(
                AttendanceRecord.employee_id
                == employee_id
            )

        if start_date is not None:
            statement = statement.where(
                AttendanceRecord.attendance_date
                >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                AttendanceRecord.attendance_date
                <= end_date
            )

        if status is not None:
            statement = statement.where(
                AttendanceRecord.status
                == status
            )

        statement = statement.order_by(
            AttendanceRecord.attendance_date.desc(),
            AttendanceRecord.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def create_event(
        self,
        *,
        attendance_record_id: uuid.UUID,
        employee_id: uuid.UUID,
        event_type: str,
        source: str,
        occurred_at,
        actor_user_id: uuid.UUID | None,
        notes: str | None,
    ) -> AttendanceEvent:
        event = AttendanceEvent(
            attendance_record_id=(
                attendance_record_id
            ),
            employee_id=employee_id,
            event_type=event_type,
            source=source,
            occurred_at=occurred_at,
            actor_user_id=actor_user_id,
            notes=notes,
        )

        self.session.add(
            event
        )

        await self.session.flush()
        await self.session.refresh(
            event
        )

        return event

    async def list_events(
        self,
        *,
        attendance_record_id: uuid.UUID,
    ) -> Sequence[
        AttendanceEvent
    ]:
        result = await self.session.execute(
            select(
                AttendanceEvent
            )
            .where(
                AttendanceEvent.attendance_record_id
                == attendance_record_id
            )
            .order_by(
                AttendanceEvent.occurred_at.asc(),
                AttendanceEvent.created_at.asc(),
            )
        )

        return result.scalars().all()

    async def update_record(
        self,
        record: AttendanceRecord,
        *,
        values: dict[str, object],
    ) -> AttendanceRecord:
        for field_name, value in values.items():
            setattr(
                record,
                field_name,
                value,
            )

        self.session.add(
            record
        )

        await self.session.flush()
        await self.session.refresh(
            record
        )

        return record

    # Compatibility methods.
    async def create_day(
        self,
        *,
        employee_id: uuid.UUID,
        work_date: date,
        status: str,
    ) -> AttendanceRecord:
        return await self.create_record(
            employee_id=employee_id,
            attendance_date=work_date,
            status=status,
            source="system",
            actor_user_id=None,
        )

    async def get_day_by_id(
        self,
        attendance_day_id: uuid.UUID,
    ) -> AttendanceRecord | None:
        return await self.get_record_by_id(
            attendance_day_id
        )

    async def get_day(
        self,
        *,
        employee_id: uuid.UUID,
        work_date: date,
    ) -> AttendanceRecord | None:
        return await self.get_record(
            employee_id=employee_id,
            attendance_date=work_date,
        )

    async def list_days(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str | None = None,
    ):
        return await self.list_records(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )


def get_attendance_repository(
    session: AsyncSession,
) -> AttendanceRepository:
    return AttendanceRepository(
        session
    )


__all__ = [
    "AttendanceRepository",
    "get_attendance_repository",
]