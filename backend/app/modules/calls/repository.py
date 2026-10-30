from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calls.models import (
    RealtimeCall,
    RealtimeCallParticipant,
)


class CallRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_call(
        self,
        call_id: uuid.UUID,
    ) -> RealtimeCall | None:
        result = await self.session.execute(
            select(
                RealtimeCall
            ).where(
                RealtimeCall.id == call_id
            )
        )

        return result.scalar_one_or_none()

    async def get_participant(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> (
        RealtimeCallParticipant | None
    ):
        result = await self.session.execute(
            select(
                RealtimeCallParticipant
            ).where(
                RealtimeCallParticipant.call_id
                == call_id,
                RealtimeCallParticipant.user_id
                == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_participants(
        self,
        *,
        call_id: uuid.UUID,
    ) -> list[
        RealtimeCallParticipant
    ]:
        result = await self.session.execute(
            select(
                RealtimeCallParticipant
            )
            .where(
                RealtimeCallParticipant.call_id
                == call_id
            )
            .order_by(
                RealtimeCallParticipant.created_at
                .asc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def add_call(
        self,
        call: RealtimeCall,
    ) -> None:
        self.session.add(
            call
        )

    async def add_participant(
        self,
        participant: (
            RealtimeCallParticipant
        ),
    ) -> None:
        self.session.add(
            participant
        )

    async def update_connection(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
        connection_id: str,
        last_heartbeat_at: datetime,
    ) -> (
        RealtimeCallParticipant | None
    ):
        participant = await self.get_participant(
            call_id=call_id,
            user_id=user_id,
        )

        if participant is None:
            return None

        participant.connection_id = (
            connection_id
        )

        participant.last_heartbeat_at = (
            last_heartbeat_at
        )

        self.session.add(
            participant
        )

        return participant