from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discipline.models import (
    DisciplinaryIncident,
)
from app.modules.discipline.repository import (
    DisciplineRepository,
)
from app.modules.discipline.schemas import (
    IncidentCreate,
    IncidentUpdate,
)


class DisciplineService:
    def __init__(
        self,
        session: AsyncSession,
        reported_by_user_id: uuid.UUID,
    ) -> None:
        self.session = session
        self.reported_by_user_id = (
            reported_by_user_id
        )
        self.repository = DisciplineRepository(
            session
        )

    async def create(
        self,
        request: IncidentCreate,
    ) -> DisciplinaryIncident:
        incident = DisciplinaryIncident(
            employee_id=request.employee_id,
            reported_by_user_id=(
                self.reported_by_user_id
            ),
            category=request.category,
            summary=request.summary,
            details=request.details,
            action=request.action,
        )

        await self.repository.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def list(
        self,
        employee_id: uuid.UUID | None = None,
    ) -> dict[str, object]:
        incidents = await self.repository.list(
            employee_id
        )

        return {
            "items": incidents,
            "total": len(incidents),
        }

    async def update(
        self,
        incident_id: uuid.UUID,
        request: IncidentUpdate,
    ) -> DisciplinaryIncident:
        incident = await self.repository.get(
            incident_id
        )

        if incident is None:
            raise LookupError(
                "Disciplinary incident not found."
            )

        values = request.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(
                incident,
                field,
                value,
            )

        if incident.status in {
            "resolved",
            "dismissed",
        }:
            incident.resolved_at = (
                datetime.now(timezone.utc)
            )

        await self.session.commit()
        await self.session.refresh(incident)

        return incident


__all__ = [
    "DisciplineService",
]