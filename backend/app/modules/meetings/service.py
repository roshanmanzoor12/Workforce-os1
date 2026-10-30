from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.meetings.enums import (
    MeetingParticipantRole,
    MeetingParticipantStatus,
    MeetingStatus,
)
from app.modules.meetings.repository import (
    MeetingRepository,
)
from app.modules.meetings.schemas import (
    MeetingCreateRequest,
    MeetingDetailResponse,
    MeetingListResponse,
    MeetingParticipantAddRequest,
    MeetingParticipantPublic,
    MeetingParticipantResponse,
    MeetingParticipantStatusRequest,
    MeetingPublic,
    MeetingResponse,
    MeetingUpdateRequest,
)


class MeetingService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.repository = MeetingRepository(
            session
        )
        self.employees = EmployeeRepository(
            session
        )

    async def create_meeting(
        self,
        *,
        actor_user_id: uuid.UUID,
        request: MeetingCreateRequest,
    ) -> MeetingResponse:
        try:
            meeting = await self.repository.create_meeting(
                title=request.title,
                description=request.description,
                meeting_type=request.meeting_type.value,
                scheduled_start_at=(
                    request.scheduled_start_at
                ),
                scheduled_end_at=(
                    request.scheduled_end_at
                ),
                location=request.location,
                created_by_user_id=actor_user_id,
            )

            seen: set[uuid.UUID] = set()

            for employee_id in (
                request.participant_employee_ids
            ):
                if employee_id in seen:
                    continue

                seen.add(
                    employee_id
                )

                employee = (
                    await self.employees
                    .get_employee_by_id(
                        employee_id
                    )
                )

                if employee is None:
                    raise ResourceNotFound(
                        "Meeting participant employee "
                        "was not found."
                    )

                if not employee.is_active:
                    raise ValidationError(
                        "Inactive employee cannot be "
                        "invited to a meeting."
                    )

                await self.repository.add_participant(
                    meeting_id=meeting.id,
                    employee_id=employee_id,
                    participant_role=(
                        MeetingParticipantRole
                        .PARTICIPANT
                        .value
                    ),
                    status=(
                        MeetingParticipantStatus
                        .INVITED
                        .value
                    ),
                )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingResponse(
            message="Meeting created.",
            meeting=self._meeting_public(
                meeting
            ),
        )

    async def list_meetings(
        self,
        *,
        status: MeetingStatus | None = None,
    ) -> MeetingListResponse:
        meetings = (
            await self.repository
            .list_meetings(
                status=(
                    status.value
                    if status is not None
                    else None
                )
            )
        )

        items = [
            self._meeting_public(
                meeting
            )
            for meeting in meetings
        ]

        return MeetingListResponse(
            meetings=items,
            total=len(
                items
            ),
        )

    async def get_meeting(
        self,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingDetailResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        return MeetingDetailResponse(
            meeting=self._meeting_public(
                meeting
            ),
            participants=[
                MeetingParticipantPublic
                .model_validate(
                    participant
                )
                for participant
                in meeting.participants
            ],
        )

    async def update_meeting(
        self,
        request: MeetingUpdateRequest,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        if meeting.status in {
            MeetingStatus.CANCELLED.value,
            MeetingStatus.COMPLETED.value,
        }:
            raise ValidationError(
                "Completed or cancelled meeting "
                "cannot be modified."
            )

        fields = request.model_fields_set

        values: dict[
            str,
            object,
        ] = {}

        if "title" in fields:
            if request.title is None:
                raise ValidationError(
                    "Meeting title cannot be cleared."
                )

            values["title"] = (
                request.title
            )

        if "description" in fields:
            values["description"] = (
                request.description
            )

        if "meeting_type" in fields:
            if request.meeting_type is None:
                raise ValidationError(
                    "Meeting type cannot be cleared."
                )

            values["meeting_type"] = (
                request.meeting_type.value
            )

        start_at = (
            request.scheduled_start_at
            if "scheduled_start_at" in fields
            else meeting.scheduled_start_at
        )

        end_at = (
            request.scheduled_end_at
            if "scheduled_end_at" in fields
            else meeting.scheduled_end_at
        )

        if (
            end_at is not None
            and start_at is not None
            and end_at <= start_at
        ):
            raise ValidationError(
                "Meeting end must be after "
                "meeting start."
            )

        if "scheduled_start_at" in fields:
            if request.scheduled_start_at is None:
                raise ValidationError(
                    "Meeting start cannot be cleared."
                )

            values["scheduled_start_at"] = (
                request.scheduled_start_at
            )

        if "scheduled_end_at" in fields:
            values["scheduled_end_at"] = (
                request.scheduled_end_at
            )

        if "location" in fields:
            values["location"] = (
                request.location
            )

        if not values:
            return MeetingResponse(
                message="Meeting unchanged.",
                meeting=self._meeting_public(
                    meeting
                ),
            )

        try:
            meeting = (
                await self.repository
                .update_meeting(
                    meeting,
                    values=values,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingResponse(
            message="Meeting updated.",
            meeting=self._meeting_public(
                meeting
            ),
        )

    async def start_meeting(
        self,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        if (
            meeting.status
            == MeetingStatus.ACTIVE.value
        ):
            return MeetingResponse(
                message="Meeting already active.",
                meeting=self._meeting_public(
                    meeting
                ),
            )

        if meeting.status in {
            MeetingStatus.COMPLETED.value,
            MeetingStatus.CANCELLED.value,
        }:
            raise ConflictError(
                "Completed or cancelled meeting "
                "cannot be started."
            )

        now = datetime.now(
            timezone.utc
        )

        try:
            meeting = (
                await self.repository
                .update_meeting(
                    meeting,
                    values={
                        "status": (
                            MeetingStatus
                            .ACTIVE
                            .value
                        ),
                        "started_at": now,
                        "ended_at": None,
                    },
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingResponse(
            message="Meeting started.",
            meeting=self._meeting_public(
                meeting
            ),
        )

    async def end_meeting(
        self,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        if (
            meeting.status
            == MeetingStatus.COMPLETED.value
        ):
            return MeetingResponse(
                message="Meeting already completed.",
                meeting=self._meeting_public(
                    meeting
                ),
            )

        if (
            meeting.status
            != MeetingStatus.ACTIVE.value
        ):
            raise ConflictError(
                "Only an active meeting can "
                "be completed."
            )

        now = datetime.now(
            timezone.utc
        )

        try:
            meeting = (
                await self.repository
                .update_meeting(
                    meeting,
                    values={
                        "status": (
                            MeetingStatus
                            .COMPLETED
                            .value
                        ),
                        "ended_at": now,
                    },
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingResponse(
            message="Meeting completed.",
            meeting=self._meeting_public(
                meeting
            ),
        )

    async def cancel_meeting(
        self,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        if (
            meeting.status
            == MeetingStatus.CANCELLED.value
        ):
            return MeetingResponse(
                message="Meeting already cancelled.",
                meeting=self._meeting_public(
                    meeting
                ),
            )

        if (
            meeting.status
            == MeetingStatus.COMPLETED.value
        ):
            raise ConflictError(
                "Completed meeting cannot "
                "be cancelled."
            )

        try:
            meeting = (
                await self.repository
                .update_meeting(
                    meeting,
                    values={
                        "status": (
                            MeetingStatus
                            .CANCELLED
                            .value
                        ),
                        "ended_at": (
                            datetime.now(
                                timezone.utc
                            )
                        ),
                    },
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingResponse(
            message="Meeting cancelled.",
            meeting=self._meeting_public(
                meeting
            ),
        )

    async def add_participant(
        self,
        request: MeetingParticipantAddRequest,
        *,
        meeting_id: uuid.UUID,
    ) -> MeetingParticipantResponse:
        meeting = await self._require_meeting(
            meeting_id
        )

        if meeting.status in {
            MeetingStatus.CANCELLED.value,
            MeetingStatus.COMPLETED.value,
        }:
            raise ConflictError(
                "Participants cannot be added "
                "to completed or cancelled meetings."
            )

        employee = (
            await self.employees
            .get_employee_by_id(
                request.employee_id
            )
        )

        if employee is None:
            raise ResourceNotFound(
                "Employee was not found."
            )

        if not employee.is_active:
            raise ValidationError(
                "Inactive employee cannot "
                "join a meeting."
            )

        existing = (
            await self.repository
            .get_participant(
                meeting_id=meeting_id,
                employee_id=request.employee_id,
            )
        )

        if existing is not None:
            raise ConflictError(
                "Employee is already a "
                "meeting participant."
            )

        try:
            participant = (
                await self.repository
                .add_participant(
                    meeting_id=meeting_id,
                    employee_id=(
                        request.employee_id
                    ),
                    participant_role=(
                        request
                        .participant_role
                        .value
                    ),
                    status=(
                        MeetingParticipantStatus
                        .INVITED
                        .value
                    ),
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return MeetingParticipantResponse(
            message="Participant added.",
            participant=(
                MeetingParticipantPublic
                .model_validate(
                    participant
                )
            ),
        )

    async def update_participant_status(
        self,
        request: MeetingParticipantStatusRequest,
        *,
        meeting_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> MeetingParticipantResponse:
        participant = (
            await self.repository
            .get_participant(
                meeting_id=meeting_id,
                employee_id=employee_id,
            )
        )

        if participant is None:
            raise ResourceNotFound(
                "Meeting participant "
                "was not found."
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

        return MeetingParticipantResponse(
            message=(
                "Participant status updated."
            ),
            participant=(
                MeetingParticipantPublic
                .model_validate(
                    participant
                )
            ),
        )

    async def remove_participant(
        self,
        *,
        meeting_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> None:
        participant = (
            await self.repository
            .get_participant(
                meeting_id=meeting_id,
                employee_id=employee_id,
            )
        )

        if participant is None:
            raise ResourceNotFound(
                "Meeting participant "
                "was not found."
            )

        try:
            await self.repository.remove_participant(
                participant
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

    async def _require_meeting(
        self,
        meeting_id: uuid.UUID,
    ):
        meeting = (
            await self.repository
            .get_meeting(
                meeting_id
            )
        )

        if meeting is None:
            raise ResourceNotFound(
                "Meeting was not found."
            )

        return meeting

    @staticmethod
    def _meeting_public(
        meeting,
    ) -> MeetingPublic:
        return MeetingPublic.model_validate(
            meeting
        )


__all__ = [
    "MeetingService",
]