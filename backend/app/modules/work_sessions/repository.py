from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.work_sessions.models import (
    WORK_SESSION_STATUS_OPEN,
    WorkSession,
)


class WorkSessionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def create(
        self,
        work_session: WorkSession,
    ) -> WorkSession:
        self._session.add(
            work_session
        )

        await self._session.flush()

        return work_session

    async def get_by_id(
        self,
        session_id: UUID,
    ) -> WorkSession | None:
        statement = (
            select(
                WorkSession
            )
            .where(
                WorkSession.id == session_id
            )
            .limit(1)
        )

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_open_for_device(
        self,
        device_id: UUID,
    ) -> WorkSession | None:
        statement = (
            select(
                WorkSession
            )
            .where(
                WorkSession.device_id == device_id,
                WorkSession.status == WORK_SESSION_STATUS_OPEN,
            )
            .order_by(
                WorkSession.started_at.desc()
            )
            .limit(1)
        )

        result = await self._session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def list_for_device(
        self,
        device_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSession]:
        statement = (
            select(
                WorkSession
            )
            .where(
                WorkSession.device_id == device_id
            )
            .order_by(
                WorkSession.started_at.desc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_for_employee(
        self,
        employee_id: UUID,
        *,
        limit: int = 100,
    ) -> list[WorkSession]:
        statement = (
            select(
                WorkSession
            )
            .where(
                WorkSession.employee_id == employee_id
            )
            .order_by(
                WorkSession.started_at.desc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_between(
        self,
        *,
        started_from: datetime,
        started_to: datetime,
        employee_id: UUID | None = None,
        device_id: UUID | None = None,
        limit: int = 1000,
    ) -> list[WorkSession]:
        statement: Select[tuple[WorkSession]] = (
            select(
                WorkSession
            )
            .where(
                WorkSession.started_at >= started_from,
                WorkSession.started_at < started_to,
            )
        )

        if employee_id is not None:
            statement = statement.where(
                WorkSession.employee_id == employee_id
            )

        if device_id is not None:
            statement = statement.where(
                WorkSession.device_id == device_id
            )

        statement = (
            statement
            .order_by(
                WorkSession.started_at.asc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_open_stale_before(
        self,
        cutoff: datetime,
        *,
        limit: int = 500,
    ) -> list[WorkSession]:
        statement = (
            select(
                WorkSession
            )
            .where(
                WorkSession.status == WORK_SESSION_STATUS_OPEN,
                WorkSession.last_observed_at < cutoff,
            )
            .order_by(
                WorkSession.last_observed_at.asc()
            )
            .limit(limit)
        )

        result = await self._session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def commit(
        self,
    ) -> None:
        await self._session.commit()

    async def rollback(
        self,
    ) -> None:
        await self._session.rollback()

    async def refresh(
        self,
        work_session: WorkSession,
    ) -> None:
        await self._session.refresh(
            work_session
        )


__all__ = [
    "WorkSessionRepository",
]