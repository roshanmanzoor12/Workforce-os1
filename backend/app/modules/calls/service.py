from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calls.enums import (
    CallParticipantState,
    CallScope,
    CallStatus,
    ScreenShareState,
)
from app.modules.calls.models import (
    RealtimeCall,
    RealtimeCallParticipant,
)
from app.modules.calls.repository import (
    CallRepository,
)
from app.modules.calls.schemas import (
    CreateCallRequest,
)


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


class CallService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            CallRepository(
                session
            )
        )

    async def assert_target_access(
        self,
        *,
        user_id: uuid.UUID,
        scope: CallScope,
        conversation_id: (
            uuid.UUID | None
        ),
        channel_id: (
            uuid.UUID | None
        ),
    ) -> None:
        if (
            scope
            == CallScope.CONVERSATION
        ):
            from app.modules.chat.models import (
                ConversationMember,
            )

            result = await self.session.execute(
                select(
                    ConversationMember.id
                ).where(
                    ConversationMember.conversation_id
                    == conversation_id,
                    ConversationMember.user_id
                    == user_id,
                    ConversationMember.left_at
                    .is_(None),
                )
            )

            if (
                result.scalar_one_or_none()
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_403_FORBIDDEN
                    ),
                    detail=(
                        "Conversation call "
                        "access denied."
                    ),
                )

            return

        if scope == CallScope.CHANNEL:
            from app.modules.channels.models import (
                WorkspaceChannelMember,
            )

            result = await self.session.execute(
                select(
                    WorkspaceChannelMember.id
                ).where(
                    WorkspaceChannelMember.channel_id
                    == channel_id,
                    WorkspaceChannelMember.user_id
                    == user_id,
                    WorkspaceChannelMember.is_active
                    .is_(True),
                )
            )

            if (
                result.scalar_one_or_none()
                is None
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_403_FORBIDDEN
                    ),
                    detail=(
                        "Channel call "
                        "access denied."
                    ),
                )

            return

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail="Unsupported call scope.",
        )

    async def create_call(
        self,
        *,
        user_id: uuid.UUID,
        payload: CreateCallRequest,
    ) -> RealtimeCall:
        await self.assert_target_access(
            user_id=user_id,
            scope=payload.scope,
            conversation_id=(
                payload.conversation_id
            ),
            channel_id=payload.channel_id,
        )

        if payload.scope == CallScope.CONVERSATION:
            from datetime import timedelta
            from sqlalchemy import or_
            from app.modules.chat.models import Conversation

            await self.session.scalar(
                select(Conversation.id)
                .where(Conversation.id == payload.conversation_id)
                .with_for_update()
            )

            cutoff = utcnow() - timedelta(seconds=90)

            mine = select(RealtimeCallParticipant.call_id).where(
                RealtimeCallParticipant.user_id == user_id,
                RealtimeCallParticipant.state.in_([
                    CallParticipantState.INVITED,
                    CallParticipantState.JOINED,
                ]),
            )

            live = select(RealtimeCallParticipant.call_id).where(
                RealtimeCallParticipant.state ==
                CallParticipantState.JOINED,
                or_(
                    RealtimeCallParticipant.last_heartbeat_at >= cutoff,
                    RealtimeCallParticipant.joined_at >= cutoff,
                ),
            )

            existing = await self.session.scalar(
                select(RealtimeCall)
                .where(
                    RealtimeCall.conversation_id ==
                    payload.conversation_id,
                    RealtimeCall.scope == CallScope.CONVERSATION,
                    RealtimeCall.status.in_([
                        CallStatus.RINGING,
                        CallStatus.ACTIVE,
                    ]),
                    RealtimeCall.id.in_(mine),
                    RealtimeCall.id.in_(live),
                )
                .order_by(RealtimeCall.created_at.desc())
                .limit(1)
            )

            if existing is not None:
                return existing

        call = RealtimeCall(
            id=uuid.uuid4(),
            scope=payload.scope,
            conversation_id=(
                payload.conversation_id
            ),
            channel_id=payload.channel_id,
            started_by_user_id=user_id,
            kind=payload.kind,
            status=CallStatus.RINGING,
        )

        await self.repository.add_call(
            call
        )

        starter = (
            RealtimeCallParticipant(
                id=uuid.uuid4(),
                call_id=call.id,
                user_id=user_id,
                state=(
                    CallParticipantState.JOINED
                ),
                microphone_enabled=True,
                camera_enabled=(
                    payload.kind.value
                    == "VIDEO"
                ),
                screen_share_state=(
                    ScreenShareState.STOPPED
                ),
                joined_at=utcnow(),
            )
        )

        await self.repository.add_participant(
            starter
        )

        unique_invites = set(payload.invited_user_ids)

        if not unique_invites and payload.scope == CallScope.CONVERSATION:
            from app.modules.chat.models import ConversationMember

            unique_invites = set(
                await self.session.scalars(
                    select(ConversationMember.user_id).where(
                        ConversationMember.conversation_id ==
                        payload.conversation_id,
                        ConversationMember.left_at.is_(None),
                    )
                )
            )

        unique_invites.discard(user_id)

        if len(unique_invites) > 99:
            raise HTTPException(
                400,
                "A call can contain at most 100 participants.",
            )

        for invited_user_id in unique_invites:
            await self.assert_target_access(
                user_id=invited_user_id,
                scope=payload.scope,
                conversation_id=(
                    payload.conversation_id
                ),
                channel_id=(
                    payload.channel_id
                ),
            )

            participant = (
                RealtimeCallParticipant(
                    id=uuid.uuid4(),
                    call_id=call.id,
                    user_id=invited_user_id,
                    state=(
                        CallParticipantState
                        .INVITED
                    ),
                    microphone_enabled=True,
                    camera_enabled=False,
                    screen_share_state=(
                        ScreenShareState
                        .STOPPED
                    ),
                )
            )

            await (
                self.repository
                .add_participant(
                    participant
                )
            )

        await self.session.commit()
        await self.session.refresh(
            call
        )

        return call
    async def update_media_state(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
        microphone_enabled: bool | None = None,
        camera_enabled: bool | None = None,
    ) -> RealtimeCallParticipant:
        call = await self.get_call_or_404(call_id)

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        if call.status not in (
            CallStatus.RINGING,
            CallStatus.ACTIVE,
        ):
            raise HTTPException(
                status_code=409,
                detail="Call is already closed.",
            )

        participant = await self.repository.get_participant(
            call_id=call_id,
            user_id=user_id,
        )

        if (
            participant is None
            or participant.state != CallParticipantState.JOINED
        ):
            raise HTTPException(
                status_code=403,
                detail="Join the call before updating media.",
            )

        if microphone_enabled is not None:
            participant.microphone_enabled = microphone_enabled

        if camera_enabled is not None:
            participant.camera_enabled = camera_enabled

        await self.session.commit()
        await self.session.refresh(participant)

        return participant

    async def heartbeat(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
        connection_id: str,
    ) -> datetime:
        call = await self.get_call_or_404(call_id)

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        if call.status not in (
            CallStatus.RINGING,
            CallStatus.ACTIVE,
        ):
            raise HTTPException(
                status_code=409,
                detail="Call is already closed.",
            )

        participant = await self.repository.get_participant(
            call_id=call_id,
            user_id=user_id,
        )

        if (
            participant is None
            or participant.state != CallParticipantState.JOINED
        ):
            raise HTTPException(
                status_code=403,
                detail="Only joined participants can send a heartbeat.",
            )

        timestamp = utcnow()

        await self.repository.update_connection(
            call_id=call_id,
            user_id=user_id,
            connection_id=connection_id,
            last_heartbeat_at=timestamp,
        )

        await self.session.commit()

        return timestamp

    async def get_call_or_404(
        self,
        call_id: uuid.UUID,
    ) -> RealtimeCall:
        call = (
            await self.repository.get_call(
                call_id
            )
        )

        if call is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Call not found.",
            )

        return call


    async def assert_call_access(
        self,
        *,
        user_id: uuid.UUID,
        call: RealtimeCall,
    ) -> None:
        if call.scope == CallScope.CONVERSATION:
            from app.modules.chat.models import Conversation

            conversation = await self.session.get(
                Conversation,
                call.conversation_id,
            )

            kind = (
                str(
                    getattr(
                        conversation.conversation_type,
                        "value",
                        conversation.conversation_type,
                    )
                ).lower()
                if conversation
                else ""
            )

            if (
                conversation
                and conversation.is_active
                and kind == "direct"
            ):
                person = await self.repository.get_participant(
                    call_id=call.id,
                    user_id=user_id,
                )

                if person is not None:
                    return

        await self.assert_target_access(
            user_id=user_id,
            scope=call.scope,
            conversation_id=call.conversation_id,
            channel_id=call.channel_id,
        )

    async def join(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RealtimeCallParticipant:
        from .call_runtime import expire_call

        call = await self.session.scalar(
            select(RealtimeCall)
            .where(RealtimeCall.id == call_id)
            .with_for_update()
        )

        if call is None:
            raise HTTPException(404, "Call not found.")

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        await expire_call(self.session, call)

        if call.status in (
            CallStatus.ENDED,
            CallStatus.CANCELLED,
        ):
            await self.session.commit()

            raise HTTPException(
                409,
                "Call has ended or its invitation expired.",
            )

        participant = await self.repository.get_participant(
            call_id=call_id,
            user_id=user_id,
        )

        if (
            participant is not None
            and participant.joined_at is None
            and participant.state in (
                CallParticipantState.LEFT,
                CallParticipantState.DECLINED,
            )
        ):
            try:
                await self.assert_target_access(
                    user_id=user_id,
                    scope=call.scope,
                    conversation_id=call.conversation_id,
                    channel_id=call.channel_id,
                )
            except HTTPException:
                await self.session.commit()

                raise HTTPException(
                    409,
                    "This invitation is no longer active. "
                    "Ask for a new invitation.",
                ) from None

        if participant is None:
            participant = RealtimeCallParticipant(
                id=uuid.uuid4(),
                call_id=call_id,
                user_id=user_id,
            )

            await self.repository.add_participant(
                participant,
            )

        participant.state = CallParticipantState.JOINED
        participant.joined_at = (
            participant.joined_at or utcnow()
        )
        participant.left_at = None

        if (
            user_id != call.started_by_user_id
            and call.status == CallStatus.RINGING
        ):
            call.status = CallStatus.ACTIVE
            call.started_at = utcnow()

        await self.session.commit()
        await self.session.refresh(participant)

        return participant

    async def leave(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RealtimeCallParticipant:
        call = await self.get_call_or_404(
            call_id
        )

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        participant = (
            await self.repository
            .get_participant(
                call_id=call_id,
                user_id=user_id,
            )
        )

        if participant is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Call participant "
                    "not found."
                ),
            )

        participant.state = (
            CallParticipantState.LEFT
        )

        participant.left_at = utcnow()

        participant.screen_share_state = (
            ScreenShareState.STOPPED
        )

        await self.session.commit()
        await self.session.refresh(
            participant
        )

        return participant

    async def decline(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RealtimeCallParticipant:
        call = await self.get_call_or_404(
            call_id
        )

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        participant = (
            await self.repository
            .get_participant(
                call_id=call_id,
                user_id=user_id,
            )
        )

        if participant is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Call invitation "
                    "not found."
                ),
            )

        participant.state = (
            CallParticipantState.DECLINED
        )

        participant.left_at = utcnow()

        await self.session.commit()
        await self.session.refresh(
            participant
        )

        return participant

    async def end_call(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RealtimeCall:
        call = await self.get_call_or_404(
            call_id
        )

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        if (
            call.started_by_user_id
            != user_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only the call starter "
                    "can end the call."
                ),
            )

        if call.status in {
            CallStatus.ENDED,
            CallStatus.CANCELLED,
        }:
            return call

        call.status = CallStatus.ENDED
        call.ended_at = utcnow()
        call.ended_by_user_id = user_id

        participants = (
            await self.repository
            .list_participants(
                call_id=call_id
            )
        )

        for participant in participants:
            if (
                participant.state
                == CallParticipantState.JOINED
            ):
                participant.state = (
                    CallParticipantState.LEFT
                )

                participant.left_at = (
                    call.ended_at
                )

            participant.screen_share_state = (
                ScreenShareState.STOPPED
            )

        await self.session.commit()
        await self.session.refresh(
            call
        )

        return call

    async def set_screen_share(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
        active: bool,
    ) -> RealtimeCallParticipant:
        call = await self.get_call_or_404(
            call_id
        )

        await self.assert_call_access(
            user_id=user_id,
            call=call,
        )

        if call.status not in {
            CallStatus.RINGING,
            CallStatus.ACTIVE,
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Screen sharing requires "
                    "an active call."
                ),
            )

        participant = (
            await self.repository
            .get_participant(
                call_id=call_id,
                user_id=user_id,
            )
        )

        if (
            participant is None
            or participant.state
            != CallParticipantState.JOINED
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only joined participants "
                    "can share their screen."
                ),
            )

        participant.screen_share_state = (
            ScreenShareState.ACTIVE
            if active
            else ScreenShareState.STOPPED
        )

        await self.session.commit()
        await self.session.refresh(
            participant
        )

        return participant

    async def assert_signal_access(
        self,
        *,
        call_id: uuid.UUID,
        sender_user_id: uuid.UUID,
        target_user_id: (
            uuid.UUID | None
        ),
    ) -> RealtimeCall:
        call = await self.get_call_or_404(
            call_id
        )

        await self.assert_call_access(
            user_id=sender_user_id,
            call=call,
        )

        sender = (
            await self.repository
            .get_participant(
                call_id=call_id,
                user_id=sender_user_id,
            )
        )

        if (
            sender is None
            or sender.state
            != CallParticipantState.JOINED
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only joined participants "
                    "can send call signaling."
                ),
            )

        if target_user_id is not None:
            target = (
                await self.repository
                .get_participant(
                    call_id=call_id,
                    user_id=target_user_id,
                )
            )

            if target is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail=(
                        "Target participant "
                        "not found."
                    ),
                )

        return call