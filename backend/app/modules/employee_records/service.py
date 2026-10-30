from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee_records.models import (
    EmployeeRecord,
)
from app.modules.employee_records.schemas import (
    EmployeeRecordCreateRequest,
    EmployeeRecordDeleteResponse,
    EmployeeRecordListResponse,
    EmployeeRecordResponse,
    EmployeeRecordUpdateRequest,
)
from app.modules.employees.models import Employee


class EmployeeRecordService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def _require_employee(
        self,
        employee_id: uuid.UUID,
    ) -> None:
        result = await self.session.execute(
            select(Employee.id).where(
                Employee.id == employee_id,
            )
        )

        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee was not found.",
            )

    async def _require_record(
        self,
        record_id: uuid.UUID,
    ) -> EmployeeRecord:
        result = await self.session.execute(
            select(EmployeeRecord).where(
                EmployeeRecord.id == record_id,
            )
        )

        record = result.scalar_one_or_none()

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee record was not found.",
            )

        return record

    async def create(
        self,
        *,
        employee_id: uuid.UUID,
        request: EmployeeRecordCreateRequest,
    ) -> EmployeeRecordResponse:
        await self._require_employee(employee_id)

        record = EmployeeRecord(
            employee_id=employee_id,
            **request.model_dump(),
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return EmployeeRecordResponse.model_validate(record)

    async def list(
        self,
        *,
        employee_id: uuid.UUID,
        record_type: str | None = None,
    ) -> EmployeeRecordListResponse:
        await self._require_employee(employee_id)

        statement = select(EmployeeRecord).where(
            EmployeeRecord.employee_id == employee_id,
        )

        if record_type:
            statement = statement.where(
                EmployeeRecord.record_type == record_type,
            )

        statement = statement.order_by(
            EmployeeRecord.created_at.desc(),
        )

        result = await self.session.execute(statement)
        records = list(result.scalars().all())

        return EmployeeRecordListResponse(
            items=[
                EmployeeRecordResponse.model_validate(
                    record,
                )
                for record in records
            ],
            total=len(records),
        )

    async def get(
        self,
        *,
        record_id: uuid.UUID,
    ) -> EmployeeRecordResponse:
        record = await self._require_record(record_id)

        return EmployeeRecordResponse.model_validate(
            record,
        )

    async def update(
        self,
        *,
        record_id: uuid.UUID,
        request: EmployeeRecordUpdateRequest,
    ) -> EmployeeRecordResponse:
        record = await self._require_record(record_id)

        for field, value in request.model_dump(
            exclude_unset=True,
        ).items():
            setattr(record, field, value)

        await self.session.commit()
        await self.session.refresh(record)

        return EmployeeRecordResponse.model_validate(
            record,
        )

    async def delete(
        self,
        *,
        record_id: uuid.UUID,
    ) -> EmployeeRecordDeleteResponse:
        record = await self._require_record(record_id)

        await self.session.execute(
            delete(EmployeeRecord).where(
                EmployeeRecord.id == record.id,
            )
        )

        await self.session.commit()

        return EmployeeRecordDeleteResponse(
            success=True,
            message="Employee record deleted.",
        )


__all__ = ["EmployeeRecordService"]