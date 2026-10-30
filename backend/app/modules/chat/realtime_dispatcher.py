from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .connection_manager import (
    ChatConnectionManager,
    chat_connection_manager,
)
from .realtime_events import ChatRealtimeEvent
from .realtime_recipient_repository import (
    RealtimeRecipientRepository,
)


logger = logging.getLogger(__name__)


class ChatRealtimeDispatcher:
    def __init__(
        self,
        *,
        connection_manager: ChatConnectionManager | None = None,
        recipient_repository: RealtimeRecipientRepository | None = None,
    ) -> None:
        self.connection_manager = (
            connection_manager
            if connection_manager is not None
            else chat_connection_manager
        )

        self.recipient_repository = (
            recipient_repository
            if recipient_repository is not None
            else RealtimeRecipientRepository()
        )

    async def _send_to_user(
        self,
        *,
        user_id: uuid.UUID,
        event: ChatRealtimeEvent,
    ) -> int:
        try:
            return await self.connection_manager.send_to_user(
                user_id=user_id,
                event=event,
            )

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Realtime send failed for event %s, recipient %s",
                event.event_id,
                user_id,
            )

            return 0

    async def _dispatch_call(
        self,
        session: AsyncSession,
        *,
        event: ChatRealtimeEvent,
        event_type: str,
    ) -> int:
        from app.modules.calls.enums import (
            CallParticipantState,
            CallStatus,
        )
        from app.modules.calls.repository import CallRepository
        from app.modules.realtime_bridge.recipient_resolver import (
            RealtimeRecipientResolver,
        )

        target_user_id = event.target_user_id

        # The bridge subscriber converts each explicit recipient
        # into a separate targeted event. Never broadcast call
        # events implicitly to an entire conversation.
        if target_user_id is None:
            logger.warning(
                "Dropping untargeted call event %s",
                event.event_id,
            )

            return 0

        try:
            call_id = uuid.UUID(
                str(event.data["call_id"])
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            AttributeError,
        ):
            logger.warning(
                "Dropping call event with invalid call_id: %s",
                event.event_id,
            )

            return 0

        repository = CallRepository(session)

        call = await repository.get_call(call_id)

        if call is None:
            return 0

        if (
            event.conversation_id is not None
            and event.conversation_id != call.conversation_id
        ):
            return 0

        resolver = RealtimeRecipientResolver(session)

        if call.conversation_id is not None:
            allowed = await resolver.conversation_users(
                conversation_id=call.conversation_id,
            )

        elif call.channel_id is not None:
            allowed = await resolver.channel_users(
                channel_id=call.channel_id,
            )

        else:
            return 0

        if target_user_id not in allowed:
            return 0

        target = await repository.get_participant(
            call_id=call_id,
            user_id=target_user_id,
        )

        if target is None:
            return 0

        if event_type == "call.signal":
            actor_user_id = event.actor_user_id

            if (
                actor_user_id is None
                or actor_user_id == target_user_id
                or actor_user_id not in allowed
                or call.status not in {
                    CallStatus.RINGING,
                    CallStatus.ACTIVE,
                }
                or target.state != CallParticipantState.JOINED
            ):
                return 0

            payload_target = event.data.get(
                "target_user_id"
            )

            if payload_target is not None:
                try:
                    if (
                        uuid.UUID(str(payload_target))
                        != target_user_id
                    ):
                        return 0

                except (
                    TypeError,
                    ValueError,
                    AttributeError,
                ):
                    return 0

            sender = await repository.get_participant(
                call_id=call_id,
                user_id=actor_user_id,
            )

            if (
                sender is None
                or sender.state != CallParticipantState.JOINED
            ):
                return 0

        # Lifecycle events can still reach authorized participants
        # after the call has ended. Only signaling requires an
        # open call with joined sender and recipient.
        return await self._send_to_user(
            user_id=target_user_id,
            event=event,
        )

    async def dispatch(
        self,
        session: AsyncSession,
        *,
        event: ChatRealtimeEvent,
    ) -> int:
        event_type = str(
            getattr(
                event.event_type,
                "value",
                event.event_type,
            )
        )

        if event_type.startswith("call."):
            return await self._dispatch_call(
                session,
                event=event,
                event_type=event_type,
            )

        explicit_target = event.target_user_id
        conversation_id = event.conversation_id

        # Pin, mute and archive preferences belong to the actor.
        # Their updates must not be broadcast to other members.
        if event_type == "conversation.preferences.updated":
            actor_user_id = event.actor_user_id

            if actor_user_id is None:
                return 0

            if (
                explicit_target is not None
                and explicit_target != actor_user_id
            ):
                return 0

            explicit_target = actor_user_id

        if explicit_target is not None:
            if conversation_id is not None:
                active_users = (
                    await self.recipient_repository.list_active_user_ids(
                        session,
                        conversation_id=conversation_id,
                    )
                )

                if explicit_target not in active_users:
                    return 0

            return await self._send_to_user(
                user_id=explicit_target,
                event=event,
            )

        if conversation_id is None:
            if event.actor_user_id is None:
                return 0

            return await self._send_to_user(
                user_id=event.actor_user_id,
                event=event,
            )

        user_ids = (
            await self.recipient_repository.list_active_user_ids(
                session,
                conversation_id=conversation_id,
            )
        )

        delivered = 0
        seen: set[uuid.UUID] = set()

        for user_id in user_ids:
            if user_id in seen:
                continue

            seen.add(user_id)

            delivered += await self._send_to_user(
                user_id=user_id,
                event=event,
            )

        return delivered


__all__ = [
    "ChatRealtimeDispatcher",
]