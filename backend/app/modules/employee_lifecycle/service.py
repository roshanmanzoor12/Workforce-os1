from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employee_lifecycle.models import (
    OffboardingRecord,
    OnboardingRecord,
)
from app.modules.employee_lifecycle.schemas import (
    OffboardingCreateRequest,
    OffboardingResponse,
    OffboardingUpdateRequest,
    OnboardingCreateRequest,
    OnboardingResponse,
    OnboardingUpdateRequest,
)
from app.modules.employees.models import Employee


class EmployeeLifecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def require_employee(
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

    async def get_onboarding(
        self,
        record_id: uuid.UUID,
    ) -> OnboardingRecord:
        record = await self.session.get(
            OnboardingRecord,
            record_id,
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding record was not found.",
            )

        return record

    async def get_offboarding(
        self,
        record_id: uuid.UUID,
    ) -> OffboardingRecord:
        record = await self.session.get(
            OffboardingRecord,
            record_id,
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offboarding record was not found.",
            )

        return record

    async def create_onboarding(
        self,
        request: OnboardingCreateRequest,
    ) -> OnboardingResponse:
        await self.require_employee(request.employee_id)

        record = OnboardingRecord(
            **request.model_dump(),
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return OnboardingResponse.model_validate(record)

    async def update_onboarding(
        self,
        record_id: uuid.UUID,
        request: OnboardingUpdateRequest,
    ) -> OnboardingResponse:
        record = await self.get_onboarding(record_id)

        for key, value in request.model_dump(
            exclude_unset=True,
        ).items():
            setattr(record, key, value)

        await self.session.commit()
        await self.session.refresh(record)

        return OnboardingResponse.model_validate(record)

    async def create_offboarding(
        self,
        request: OffboardingCreateRequest,
    ) -> OffboardingResponse:
        await self.require_employee(request.employee_id)

        record = OffboardingRecord(
            **request.model_dump(),
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return OffboardingResponse.model_validate(record)

    async def update_offboarding(
        self,
        record_id: uuid.UUID,
        request: OffboardingUpdateRequest,
    ) -> OffboardingResponse:
        record = await self.get_offboarding(record_id)

        for key, value in request.model_dump(
            exclude_unset=True,
        ).items():
            setattr(record, key, value)

        await self.session.commit()
        await self.session.refresh(record)

        return OffboardingResponse.model_validate(record)


__all__ = ["EmployeeLifecycleService"]