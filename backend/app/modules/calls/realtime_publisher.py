from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calls.enums import (
    CallScope,
)
from app.modules.calls.models import (
    RealtimeCall,
)
from app.modules.realtime_bridge.envelope import (
    build_realtime_envelope,
)
from app.modules.realtime_bridge.recipient_resolver import (
    RealtimeRecipientResolver,
)
from app.modules.realtime_bridge.redis_transport import (
    get_realtime_transport,
)


class CallRealtimePublisher:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.recipients = (
            RealtimeRecipientResolver(
                session
            )
        )

    async def _recipients(
        self,
        call: RealtimeCall,
    ) -> list[uuid.UUID]:
        if (
            call.scope
            == CallScope.CONVERSATION
        ):
            assert (
                call.conversation_id
                is not None
            )

            return (
                await self.recipients
                .conversation_users(
                    conversation_id=(
                        call.conversation_id
                    )
                )
            )

        assert (
            call.channel_id
            is not None
        )

        return (
            await self.recipients
            .channel_users(
                channel_id=(
                    call.channel_id
                )
            )
        )

    async def publish(
        self,
        *,
        actor_user_id: uuid.UUID,
        event_type: str,
        call: RealtimeCall,
        data: dict[str, object],
    ) -> None:
        recipient_ids = await self._recipients(
            call
        )

        envelope = build_realtime_envelope(
            event_type=event_type,
            actor_user_id=actor_user_id,
            recipient_user_ids=recipient_ids,
            data={
                "call_id": str(
                    call.id
                ),
                **data,
            },
        )

        try:
            await (
                get_realtime_transport()
                .publish(envelope)
            )
        except Exception:
            return