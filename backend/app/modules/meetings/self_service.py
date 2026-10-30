from __future__ import annotations

import uuid

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.employees.models import (
    Employee,
)
from app.modules.meetings.enums import (
    MeetingParticipantStatus,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)
from app.modules.meetings.repository import (
    MeetingRepository,
)
from app.modules.meetings.self_schemas import (
    MeetingInvitationListResponse,
    MeetingInvitationPublic,
    MeetingSelfResponse,
    MeetingSelfResponseRequest,
    MeetingSelfResponseResult,
)


class MeetingSelfService:
    """
    Meeting actions performed by the authenticated employee.

    Global User and tenant Employee remain separate identities.

    Employee.user_id is the logical tenant-to-control identity
    link and intentionally is not a cross-database foreign key.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = MeetingRepository(
            session
        )

    async def resolve_actor_employee(
        self,
        *,
        actor_user_id: uuid.UUID,
    ) -> Employee:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.user_id
                == actor_user_id,
                Employee.is_active.is_(
                    True
                ),
            )
        )

        employee = (
            result.scalar_one_or_none()
        )

        if employee is None:
            raise ResourceNotFound(
                "Authenticated workspace user "
                "is not linked to an active "
                "employee record."
            )

        return employee

    async def list_my_invitations(
        self,
        *,
        actor_user_id: uuid.UUID,
    ) -> MeetingInvitationListResponse:
        employee = (
            await self.resolve_actor_employee(
                actor_user_id=actor_user_id
            )
        )

        statement = (
            select(
                MeetingParticipant,
                Meeting,
            )
            .join(
                Meeting,
                Meeting.id
                == MeetingParticipant.meeting_id,
            )
            .where(
                MeetingParticipant.employee_id
                == employee.id
            )
            .order_by(
                Meeting.scheduled_start_at.asc()
            )
        )

        result = await self.session.execute(
            statement
        )

        rows = result.all()

        invitations = [
            MeetingInvitationPublic(
                meeting_id=meeting.id,
                title=meeting.title,
                meeting_type=(
                    meeting.meeting_type
                ),
                meeting_status=(
                    meeting.status
                ),
                scheduled_start_at=(
                    meeting.scheduled_start_at
                ),
                scheduled_end_at=(
                    meeting.scheduled_end_at
                ),
                participant_status=(
                    participant.status
                ),
            )
            for participant, meeting
            in rows
        ]

        return MeetingInvitationListResponse(
            invitations=invitations,
            total=len(
                invitations
            ),
        )

    async def respond_to_invitation(
        self,
        *,
        actor_user_id: uuid.UUID,
        meeting_id: uuid.UUID,
        request: MeetingSelfResponseRequest,
    ) -> MeetingSelfResponse:
        if request.status not in {
            MeetingParticipantStatus.ACCEPTED,
            MeetingParticipantStatus.DECLINED,
        }:
            raise ValidationError(
                "Participants may only accept "
                "or decline their own invitation."
            )

        employee = (
            await self.resolve_actor_employee(
                actor_user_id=actor_user_id
            )
        )

        participant = (
            await self.repository
            .get_participant(
                meeting_id=meeting_id,
                employee_id=employee.id,
            )
        )

        if participant is None:
            raise ResourceNotFound(
                "Meeting invitation was not found "
                "for the authenticated employee."
            )

        try:
            participant = (
                await self.repository
                .update_participant(
                    participant,
                    values={
                        "status": (
                            request.status.value
                        )
                    },
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingSelfResponse(
            message=(
                "Meeting invitation response "
                "updated."
            ),
            participant=(
                MeetingSelfResponseResult(
                    meeting_id=meeting_id,
                    employee_id=employee.id,
                    status=participant.status,
                )
            ),
        )


__all__ = [
    "MeetingSelfService",
]