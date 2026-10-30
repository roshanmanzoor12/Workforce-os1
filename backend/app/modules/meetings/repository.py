from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from sqlalchemy.orm import (
    selectinload,
)

from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)


class MeetingRepository:
    """
    Tenant-scoped persistence for meetings.

    This repository receives an already-authorized tenant
    AsyncSession. It does not resolve workspaces, memberships,
    database URLs, or tenant credentials.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # MEETINGS
    # =====================================================

    async def create_meeting(
        self,
        *,
        title: str,
        description: str | None,
        meeting_type: str,
        scheduled_start_at: datetime,
        scheduled_end_at: datetime | None,
        location: str | None,
        created_by_user_id: uuid.UUID,
    ) -> Meeting:
        meeting = Meeting(
            title=title,
            description=description,
            meeting_type=meeting_type,
            scheduled_start_at=(
                scheduled_start_at
            ),
            scheduled_end_at=(
                scheduled_end_at
            ),
            location=location,
            created_by_user_id=(
                created_by_user_id
            ),
        )

        self.session.add(
            meeting
        )

        await self.session.flush()
        await self.session.refresh(
            meeting
        )

        return meeting

    async def get_meeting(
        self,
        meeting_id: uuid.UUID,
    ) -> Meeting | None:
        statement = (
            select(
                Meeting
            )
            .options(
                selectinload(
                    Meeting.participants
                )
            )
            .where(
                Meeting.id
                == meeting_id
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_meeting_for_update(
        self,
        meeting_id: uuid.UUID,
    ) -> Meeting | None:
        statement = (
            select(
                Meeting
            )
            .where(
                Meeting.id
                == meeting_id
            )
            .with_for_update()
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def list_meetings(
        self,
        *,
        status: str | None = None,
    ) -> Sequence[
        Meeting
    ]:
        statement = select(
            Meeting
        )

        if status is not None:
            statement = statement.where(
                Meeting.status
                == status
            )

        statement = statement.order_by(
            Meeting.scheduled_start_at.asc(),
            Meeting.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def update_meeting(
        self,
        meeting: Meeting,
        *,
        values: dict[
            str,
            object,
        ],
    ) -> Meeting:
        for field_name, value in (
            values.items()
        ):
            setattr(
                meeting,
                field_name,
                value,
            )

        self.session.add(
            meeting
        )

        await self.session.flush()
        await self.session.refresh(
            meeting
        )

        return meeting

    async def delete_meeting(
        self,
        meeting: Meeting,
    ) -> None:
        await self.session.delete(
            meeting
        )

        await self.session.flush()

    # =====================================================
    # PARTICIPANTS
    # =====================================================

    async def add_participant(
        self,
        *,
        meeting_id: uuid.UUID,
        employee_id: uuid.UUID,
        participant_role: str,
        status: str,
    ) -> MeetingParticipant:
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            employee_id=employee_id,
            participant_role=(
                participant_role
            ),
            status=status,
        )

        self.session.add(
            participant
        )

        await self.session.flush()
        await self.session.refresh(
            participant
        )

        return participant

    async def get_participant(
        self,
        *,
        meeting_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> MeetingParticipant | None:
        statement = select(
            MeetingParticipant
        ).where(
            MeetingParticipant.meeting_id
            == meeting_id,
            MeetingParticipant.employee_id
            == employee_id,
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_participant_by_id(
        self,
        participant_id: uuid.UUID,
    ) -> MeetingParticipant | None:
        statement = select(
            MeetingParticipant
        ).where(
            MeetingParticipant.id
            == participant_id
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def list_participants(
        self,
        meeting_id: uuid.UUID,
    ) -> Sequence[
        MeetingParticipant
    ]:
        statement = (
            select(
                MeetingParticipant
            )
            .where(
                MeetingParticipant.meeting_id
                == meeting_id
            )
            .order_by(
                MeetingParticipant.created_at.asc()
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def update_participant(
        self,
        participant: MeetingParticipant,
        *,
        values: dict[
            str,
            object,
        ],
    ) -> MeetingParticipant:
        for field_name, value in (
            values.items()
        ):
            setattr(
                participant,
                field_name,
                value,
            )

        self.session.add(
            participant
        )

        await self.session.flush()
        await self.session.refresh(
            participant
        )

        return participant

    async def remove_participant(
        self,
        participant: MeetingParticipant,
    ) -> None:
        await self.session.delete(
            participant
        )

        await self.session.flush()

    async def employee_is_participant(
        self,
        *,
        meeting_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> bool:
        participant = await self.get_participant(
            meeting_id=meeting_id,
            employee_id=employee_id,
        )

        return participant is not None


def get_meeting_repository(
    session: AsyncSession,
) -> MeetingRepository:
    return MeetingRepository(
        session
    )


__all__ = [
    "MeetingRepository",
    "get_meeting_repository",
]