from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.voice_channels.models import (
    VOICE_CALL_ACTIVE,
    VOICE_CALL_ENDED,
    VOICE_PARTICIPANT_JOINED,
    VOICE_PARTICIPANT_LEFT,
    VoiceChannelBan,
    VoiceChannelCall,
    VoiceChannelParticipant,
)


class VoiceChannelRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    async def active_call(
        self,
        *,
        channel_id: uuid.UUID,
    ) -> VoiceChannelCall | None:
        result = await self.session.execute(
            select(
                VoiceChannelCall
            ).where(
                VoiceChannelCall.channel_id
                == channel_id,

                VoiceChannelCall.status
                == VOICE_CALL_ACTIVE,
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def create_call(
        self,
        *,
        channel_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
    ) -> VoiceChannelCall:
        call = VoiceChannelCall(
            channel_id=channel_id,

            created_by_user_id=(
                created_by_user_id
            ),

            status=VOICE_CALL_ACTIVE,
        )

        self.session.add(
            call
        )

        await self.session.flush()

        await self.session.refresh(
            call
        )

        return call

    async def get_call(
        self,
        *,
        call_id: uuid.UUID,
    ) -> VoiceChannelCall | None:
        result = await self.session.execute(
            select(
                VoiceChannelCall
            ).where(
                VoiceChannelCall.id
                == call_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def end_call(
        self,
        *,
        call: VoiceChannelCall,
    ) -> VoiceChannelCall:
        call.status = (
            VOICE_CALL_ENDED
        )

        call.ended_at = self.now()

        await self.session.flush()

        await self.session.refresh(
            call
        )

        return call

    async def participant(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> VoiceChannelParticipant | None:
        result = await self.session.execute(
            select(
                VoiceChannelParticipant
            ).where(
                VoiceChannelParticipant.call_id
                == call_id,

                VoiceChannelParticipant.user_id
                == user_id,
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def joined_participants(
        self,
        *,
        call_id: uuid.UUID,
    ) -> list[
        VoiceChannelParticipant
    ]:
        result = await self.session.execute(
            select(
                VoiceChannelParticipant
            ).where(
                VoiceChannelParticipant.call_id
                == call_id,

                VoiceChannelParticipant.state
                == VOICE_PARTICIPANT_JOINED,
            ).order_by(
                VoiceChannelParticipant.joined_at
                .asc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def join(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> VoiceChannelParticipant:
        participant = await self.participant(
            call_id=call_id,
            user_id=user_id,
        )

        now = self.now()

        if participant is None:
            participant = VoiceChannelParticipant(
                call_id=call_id,

                user_id=user_id,

                state=(
                    VOICE_PARTICIPANT_JOINED
                ),

                self_muted=False,

                self_deafened=False,

                server_muted=False,

                server_deafened=False,

                screen_sharing=False,

                joined_at=now,

                left_at=None,
            )

            self.session.add(
                participant
            )

        else:
            participant.state = (
                VOICE_PARTICIPANT_JOINED
            )

            participant.left_at = None

            participant.joined_at = now

            participant.screen_sharing = (
                False
            )

        await self.session.flush()

        await self.session.refresh(
            participant
        )

        return participant

    async def leave(
        self,
        *,
        participant: VoiceChannelParticipant,
    ) -> VoiceChannelParticipant:
        participant.state = (
            VOICE_PARTICIPANT_LEFT
        )

        participant.left_at = self.now()

        participant.screen_sharing = False

        await self.session.flush()

        await self.session.refresh(
            participant
        )

        return participant

    async def refresh_participant(
        self,
        participant: VoiceChannelParticipant,
    ) -> VoiceChannelParticipant:
        await self.session.flush()

        await self.session.refresh(
            participant
        )

        return participant

    async def active_ban(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> VoiceChannelBan | None:
        result = await self.session.execute(
            select(
                VoiceChannelBan
            ).where(
                VoiceChannelBan.channel_id
                == channel_id,

                VoiceChannelBan.user_id
                == user_id,

                VoiceChannelBan.is_active
                .is_(
                    True
                ),
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def ban(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        banned_by_user_id: uuid.UUID,
        reason: str | None,
    ) -> VoiceChannelBan:
        result = await self.session.execute(
            select(
                VoiceChannelBan
            ).where(
                VoiceChannelBan.channel_id
                == channel_id,

                VoiceChannelBan.user_id
                == user_id,
            )
        )

        item = (
            result
            .scalar_one_or_none()
        )

        if item is None:
            item = VoiceChannelBan(
                channel_id=channel_id,

                user_id=user_id,

                banned_by_user_id=(
                    banned_by_user_id
                ),

                reason=reason,

                is_active=True,

                lifted_at=None,
            )

            self.session.add(
                item
            )

        else:
            item.banned_by_user_id = (
                banned_by_user_id
            )

            item.reason = reason

            item.is_active = True

            item.lifted_at = None

        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item

    async def unban(
        self,
        *,
        item: VoiceChannelBan,
    ) -> VoiceChannelBan:
        item.is_active = False

        item.lifted_at = self.now()

        await self.session.flush()

        await self.session.refresh(
            item
        )

        return item


__all__ = [
    "VoiceChannelRepository",
]