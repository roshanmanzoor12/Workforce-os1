from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import (
    Attachment,
    AttachmentScope,
)
from app.modules.attachments.realtime_payloads import (
    serialize_message_attachments_realtime,
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


class AttachmentRealtimePublisher:
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

    async def attachments_bound(
        self,
        *,
        actor_user_id: uuid.UUID,
        message_id: uuid.UUID,
        attachments: list[Attachment],
    ) -> None:
        if not attachments:
            return

        first = attachments[0]

        if (
            first.scope
            == AttachmentScope.CONVERSATION
        ):
            assert (
                first.conversation_id
                is not None
            )

            recipient_ids = (
                await self.recipients
                .conversation_users(
                    conversation_id=(
                        first.conversation_id
                    )
                )
            )

        else:
            assert (
                first.channel_id
                is not None
            )

            recipient_ids = (
                await self.recipients
                .channel_users(
                    channel_id=(
                        first.channel_id
                    )
                )
            )

        envelope = build_realtime_envelope(
            event_type=(
                "message.attachments.updated"
            ),
            actor_user_id=actor_user_id,
            recipient_user_ids=recipient_ids,
            data={
                "message_id": str(
                    message_id
                ),
                "attachments": (
                    serialize_message_attachments_realtime(
                        attachments
                    )
                ),
            },
        )

        try:
            await (
                get_realtime_transport()
                .publish(envelope)
            )
        except Exception:
            # DB mutation already committed.
            # Realtime delivery is best effort.
            return