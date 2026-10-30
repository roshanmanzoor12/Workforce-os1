from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.redis import redis_client
from app.modules.voice_channels.access import (
    VoiceChannelAccess,
    require_voice_moderator,
)
from app.modules.voice_channels.models import (
    VOICE_PARTICIPANT_JOINED,
)
from app.modules.voice_channels.repository import (
    VoiceChannelRepository,
)
from app.modules.voice_channels.schemas import (
    VoiceBanResponse,
    VoiceCallPublic,
    VoiceCapabilitiesResponse,
    VoiceJoinResponse,
    VoiceModeratorStateRequest,
    VoiceParticipantListResponse,
    VoiceParticipantPublic,
    VoicePresenceHeartbeatRequest,
    VoicePresenceState,
    VoiceRealtimeStateResponse,
    VoiceScreenShareResponse,
    VoiceSelfStateRequest,
    VoiceSignalEnvelope,
    VoiceSignalPollResponse,
    VoiceSignalRequest,
    VoiceSignalResponse,
)


class VoiceChannelNotFoundError(LookupError):
    pass


class VoiceChannelPermissionError(PermissionError):
    pass


class VoiceChannelService:
    PRESENCE_TTL_SECONDS = 45
    SIGNAL_TTL_SECONDS = 120
    SIGNAL_QUEUE_LIMIT = 200

    def __init__(
        self,
        *,
        tenant_session: AsyncSession,
        control_session: AsyncSession,
        workspace_id: uuid.UUID,
    ) -> None:
        self.tenant_session = tenant_session
        self.control_session = control_session
        self.workspace_id = workspace_id

        self.repository = VoiceChannelRepository(
            tenant_session
        )

    @staticmethod
    def now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    # =====================================================
    # CHANNEL
    # =====================================================

    async def require_voice_channel(
        self,
        *,
        channel_id: uuid.UUID,
    ) -> Any:
        from app.modules.channels.models import (
            WorkspaceChannel,
        )

        result = await self.control_session.execute(
            select(
                WorkspaceChannel
            ).where(
                WorkspaceChannel.id
                == channel_id,
                WorkspaceChannel.workspace_id
                == self.workspace_id,
            )
        )

        channel = result.scalar_one_or_none()

        if channel is None:
            raise VoiceChannelNotFoundError(
                "Workspace channel not found."
            )

        if not channel.is_active:
            raise ValidationError(
                "Workspace channel is archived."
            )

        raw_type = getattr(
            channel.channel_type,
            "value",
            channel.channel_type,
        )

        if str(raw_type).lower() != "voice":
            raise ValidationError(
                "This operation requires a voice channel."
            )

        return channel

    # =====================================================
    # REDIS KEYS
    # =====================================================

    def _event_channel(
        self,
        *,
        call_id: uuid.UUID,
    ) -> str:
        return (
            f"workforce:voice:"
            f"{self.workspace_id}:"
            f"{call_id}:events"
        )

    def _presence_key(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        return (
            f"workforce:voice:"
            f"{self.workspace_id}:"
            f"{call_id}:presence:"
            f"{user_id}"
        )

    def _signal_queue_key(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        return (
            f"workforce:voice:"
            f"{self.workspace_id}:"
            f"{call_id}:signals:"
            f"{user_id}"
        )

    async def publish(
        self,
        *,
        call_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        message = json.dumps(
            {
                "event": event_type,
                "call_id": str(
                    call_id
                ),
                "payload": payload,
                "created_at": (
                    self.now().isoformat()
                ),
            },
            separators=(",", ":"),
            default=str,
        )

        await redis_client.publish(
            self._event_channel(
                call_id=call_id
            ),
            message,
        )

    # =====================================================
    # REALTIME STATE
    # =====================================================

    async def realtime_state(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[
        VoicePresenceState,
        bool,
    ]:
        data = await redis_client.hgetall(
            self._presence_key(
                call_id=call_id,
                user_id=user_id,
            )
        )

        if not data:
            return (
                VoicePresenceState.DISCONNECTED,
                False,
            )

        presence_raw = data.get(
            "presence",
            VoicePresenceState
            .DISCONNECTED
            .value,
        )

        speaking = (
            data.get(
                "speaking",
                "0",
            )
            == "1"
        )

        return (
            VoicePresenceState(
                presence_raw
            ),
            speaking,
        )

    async def _set_presence(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
        presence: VoicePresenceState,
        speaking: bool,
        connection_id: str,
    ) -> None:
        key = self._presence_key(
            call_id=call_id,
            user_id=user_id,
        )

        await redis_client.hset(
            key,
            mapping={
                "presence": presence.value,
                "speaking": (
                    "1"
                    if speaking
                    else "0"
                ),
                "connection_id": (
                    connection_id
                ),
                "last_seen_at": (
                    self.now().isoformat()
                ),
            },
        )

        await redis_client.expire(
            key,
            self.PRESENCE_TTL_SECONDS,
        )

    async def participant_public(
        self,
        participant: Any,
    ) -> VoiceParticipantPublic:
        presence, speaking = await (
            self.realtime_state(
                call_id=(
                    participant.call_id
                ),
                user_id=(
                    participant.user_id
                ),
            )
        )

        return VoiceParticipantPublic(
            id=participant.id,
            call_id=participant.call_id,
            user_id=participant.user_id,
            state=participant.state,
            self_muted=(
                participant.self_muted
            ),
            self_deafened=(
                participant.self_deafened
            ),
            server_muted=(
                participant.server_muted
            ),
            server_deafened=(
                participant.server_deafened
            ),
            effective_muted=(
                participant.self_muted
                or participant.server_muted
            ),
            effective_deafened=(
                participant.self_deafened
                or participant.server_deafened
            ),
            screen_sharing=(
                participant.screen_sharing
            ),
            presence=presence,
            speaking=speaking,
            joined_at=(
                participant.joined_at
            ),
            left_at=(
                participant.left_at
            ),
        )

    # =====================================================
    # CALL
    # =====================================================

    async def get_or_create_active_call(
        self,
        *,
        channel_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> Any:
        await self.require_voice_channel(
            channel_id=channel_id
        )

        existing = await (
            self.repository.active_call(
                channel_id=channel_id
            )
        )

        if existing is not None:
            return existing

        try:
            async with (
                self.tenant_session
                .begin_nested()
            ):
                return await (
                    self.repository.create_call(
                        channel_id=(
                            channel_id
                        ),
                        created_by_user_id=(
                            actor_user_id
                        ),
                    )
                )

        except Exception:
            existing = await (
                self.repository.active_call(
                    channel_id=channel_id
                )
            )

            if existing is not None:
                return existing

            raise

    async def call_public(
        self,
        call: Any,
    ) -> VoiceCallPublic:
        participants = await (
            self.repository
            .joined_participants(
                call_id=call.id
            )
        )

        public_participants = []

        for participant in participants:
            public_participants.append(
                await self.participant_public(
                    participant
                )
            )

        return VoiceCallPublic(
            id=call.id,
            channel_id=call.channel_id,
            created_by_user_id=(
                call.created_by_user_id
            ),
            status=call.status,
            created_at=call.created_at,
            ended_at=call.ended_at,
            participants=(
                public_participants
            ),
        )

    async def active_call(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
    ) -> VoiceCallPublic:
        await self.require_voice_channel(
            channel_id=channel_id
        )

        call = await (
            self.repository.active_call(
                channel_id=channel_id
            )
        )

        if call is None:
            call = await (
                self.get_or_create_active_call(
                    channel_id=channel_id,
                    actor_user_id=(
                        access.actor_user_id
                    ),
                )
            )

        return await self.call_public(
            call
        )

    # =====================================================
    # JOIN
    # =====================================================

    async def join(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
    ) -> VoiceJoinResponse:
        await self.require_voice_channel(
            channel_id=channel_id
        )

        ban = await (
            self.repository.active_ban(
                channel_id=channel_id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        if ban is not None:
            raise VoiceChannelPermissionError(
                "You are banned from this "
                "voice channel."
            )

        call = await (
            self.get_or_create_active_call(
                channel_id=channel_id,
                actor_user_id=(
                    access.actor_user_id
                ),
            )
        )

        participant = await (
            self.repository.join(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        await self._set_presence(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
            presence=(
                VoicePresenceState.CONNECTED
            ),
            speaking=False,
            connection_id="join",
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.participant.joined"
            ),
            payload={
                "user_id": str(
                    access.actor_user_id
                )
            },
        )

        return VoiceJoinResponse(
            call=await self.call_public(
                call
            ),
            participant=(
                await self.participant_public(
                    participant
                )
            ),
        )

    # =====================================================
    # LEAVE
    # =====================================================

    async def leave(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
    ) -> VoiceParticipantPublic:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        participant = await (
            self._require_joined_participant(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        participant = await (
            self.repository.leave(
                participant=participant
            )
        )

        await redis_client.delete(
            self._presence_key(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.participant.left"
            ),
            payload={
                "user_id": str(
                    access.actor_user_id
                )
            },
        )

        remaining = await (
            self.repository
            .joined_participants(
                call_id=call.id
            )
        )

        if not remaining:
            await self.repository.end_call(
                call=call
            )

            await self.publish(
                call_id=call.id,
                event_type=(
                    "voice.call.ended"
                ),
                payload={},
            )

        return await (
            self.participant_public(
                participant
            )
        )

    # =====================================================
    # PARTICIPANTS
    # =====================================================

    async def participants(
        self,
        *,
        channel_id: uuid.UUID,
    ) -> VoiceParticipantListResponse:
        await self.require_voice_channel(
            channel_id=channel_id
        )

        call = await (
            self.repository.active_call(
                channel_id=channel_id
            )
        )

        if call is None:
            return VoiceParticipantListResponse(
                call_id=uuid.UUID(
                    int=0
                ),
                participants=[],
            )

        rows = await (
            self.repository
            .joined_participants(
                call_id=call.id
            )
        )

        items = []

        for row in rows:
            items.append(
                await self.participant_public(
                    row
                )
            )

        return VoiceParticipantListResponse(
            call_id=call.id,
            participants=items,
        )

    # =====================================================
    # SELF MUTE / DEAFEN
    # =====================================================

    async def self_state(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        payload: VoiceSelfStateRequest,
    ) -> VoiceParticipantPublic:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        participant = await (
            self._require_joined_participant(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        if payload.self_muted is not None:
            participant.self_muted = (
                payload.self_muted
            )

        if payload.self_deafened is not None:
            participant.self_deafened = (
                payload.self_deafened
            )

            if payload.self_deafened:
                participant.self_muted = True

        participant = await (
            self.repository
            .refresh_participant(
                participant
            )
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.participant.self_state"
            ),
            payload={
                "user_id": str(
                    participant.user_id
                ),
                "self_muted": (
                    participant.self_muted
                ),
                "self_deafened": (
                    participant.self_deafened
                ),
            },
        )

        return await (
            self.participant_public(
                participant
            )
        )

    # =====================================================
    # MODERATOR MUTE / DEAFEN
    # =====================================================

    async def moderator_state(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: VoiceModeratorStateRequest,
    ) -> VoiceParticipantPublic:
        try:
            require_voice_moderator(
                access
            )
        except ValidationError as exc:
            raise (
                VoiceChannelPermissionError(
                    str(exc)
                )
            ) from exc

        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        participant = await (
            self._require_joined_participant(
                call_id=call.id,
                user_id=user_id,
            )
        )

        if payload.server_muted is not None:
            participant.server_muted = (
                payload.server_muted
            )

        if (
            payload.server_deafened
            is not None
        ):
            participant.server_deafened = (
                payload.server_deafened
            )

            if payload.server_deafened:
                participant.server_muted = True

        participant = await (
            self.repository
            .refresh_participant(
                participant
            )
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.participant."
                "moderation_state"
            ),
            payload={
                "user_id": str(
                    user_id
                ),
                "server_muted": (
                    participant.server_muted
                ),
                "server_deafened": (
                    participant.server_deafened
                ),
            },
        )

        return await (
            self.participant_public(
                participant
            )
        )

    # =====================================================
    # KICK
    # =====================================================

    async def kick(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> VoiceParticipantPublic:
        try:
            require_voice_moderator(
                access
            )
        except ValidationError as exc:
            raise (
                VoiceChannelPermissionError(
                    str(exc)
                )
            ) from exc

        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        participant = await (
            self._require_joined_participant(
                call_id=call.id,
                user_id=user_id,
            )
        )

        participant = await (
            self.repository.leave(
                participant=participant
            )
        )

        await redis_client.delete(
            self._presence_key(
                call_id=call.id,
                user_id=user_id,
            )
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.participant.kicked"
            ),
            payload={
                "user_id": str(
                    user_id
                ),
                "moderator_user_id": str(
                    access.actor_user_id
                ),
            },
        )

        remaining = await (
            self.repository
            .joined_participants(
                call_id=call.id
            )
        )

        if not remaining:
            await self.repository.end_call(
                call=call
            )

        return await (
            self.participant_public(
                participant
            )
        )

    # =====================================================
    # BAN
    # =====================================================

    async def ban(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str | None,
    ) -> VoiceBanResponse:
        try:
            require_voice_moderator(
                access
            )
        except ValidationError as exc:
            raise (
                VoiceChannelPermissionError(
                    str(exc)
                )
            ) from exc

        await self.require_voice_channel(
            channel_id=channel_id
        )

        item = await self.repository.ban(
            channel_id=channel_id,
            user_id=user_id,
            banned_by_user_id=(
                access.actor_user_id
            ),
            reason=reason,
        )

        call = await (
            self.repository.active_call(
                channel_id=channel_id
            )
        )

        if call is not None:
            participant = await (
                self.repository.participant(
                    call_id=call.id,
                    user_id=user_id,
                )
            )

            if (
                participant is not None
                and participant.state
                == VOICE_PARTICIPANT_JOINED
            ):
                await self.repository.leave(
                    participant=participant
                )

                await redis_client.delete(
                    self._presence_key(
                        call_id=call.id,
                        user_id=user_id,
                    )
                )

                await self.publish(
                    call_id=call.id,
                    event_type=(
                        "voice.participant.banned"
                    ),
                    payload={
                        "user_id": str(
                            user_id
                        )
                    },
                )

        return VoiceBanResponse(
            channel_id=channel_id,
            user_id=user_id,
            is_active=item.is_active,
            reason=item.reason,
        )

    async def unban(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> VoiceBanResponse:
        try:
            require_voice_moderator(
                access
            )
        except ValidationError as exc:
            raise (
                VoiceChannelPermissionError(
                    str(exc)
                )
            ) from exc

        await self.require_voice_channel(
            channel_id=channel_id
        )

        item = await (
            self.repository.active_ban(
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        if item is None:
            return VoiceBanResponse(
                channel_id=channel_id,
                user_id=user_id,
                is_active=False,
                reason=None,
            )

        item = await (
            self.repository.unban(
                item=item
            )
        )

        return VoiceBanResponse(
            channel_id=channel_id,
            user_id=user_id,
            is_active=False,
            reason=item.reason,
        )

    # =====================================================
    # SCREEN SHARE
    # =====================================================

    async def screen_share(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        enabled: bool,
    ) -> VoiceScreenShareResponse:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        participant = await (
            self._require_joined_participant(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        participant.screen_sharing = (
            enabled
        )

        participant = await (
            self.repository
            .refresh_participant(
                participant
            )
        )

        await self.publish(
            call_id=call.id,
            event_type=(
                "voice.screen_share.started"
                if enabled
                else
                "voice.screen_share.stopped"
            ),
            payload={
                "user_id": str(
                    access.actor_user_id
                )
            },
        )

        return VoiceScreenShareResponse(
            participant=(
                await self.participant_public(
                    participant
                )
            )
        )

    # =====================================================
    # WEBRTC SIGNALING
    # =====================================================

    async def signal(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        payload: VoiceSignalRequest,
    ) -> VoiceSignalResponse:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        await self._require_joined_participant(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        if (
            payload.target_user_id
            == access.actor_user_id
        ):
            raise ValidationError(
                "WebRTC signal target cannot "
                "be the sender."
            )

        if payload.target_user_id is not None:
            await self._require_joined_participant(
                call_id=call.id,
                user_id=(
                    payload.target_user_id
                ),
            )

        event = VoiceSignalEnvelope(
            event_id=uuid.uuid4(),
            call_id=call.id,
            channel_id=channel_id,
            sender_user_id=(
                access.actor_user_id
            ),
            target_user_id=(
                payload.target_user_id
            ),
            signal_type=(
                payload.signal_type
            ),
            payload=payload.payload,
            created_at=self.now(),
        )

        if payload.target_user_id:
            recipients = [
                payload.target_user_id
            ]
        else:
            participants = await (
                self.repository
                .joined_participants(
                    call_id=call.id
                )
            )

            recipients = [
                participant.user_id
                for participant
                in participants
                if (
                    participant.user_id
                    != access.actor_user_id
                )
            ]

        encoded = (
            event.model_dump_json()
        )

        for recipient in recipients:
            key = (
                self._signal_queue_key(
                    call_id=call.id,
                    user_id=recipient,
                )
            )

            await redis_client.rpush(
                key,
                encoded,
            )

            await redis_client.ltrim(
                key,
                -self.SIGNAL_QUEUE_LIMIT,
                -1,
            )

            await redis_client.expire(
                key,
                self.SIGNAL_TTL_SECONDS,
            )

        await self.publish(
            call_id=call.id,
            event_type="voice.signal",
            payload={
                "event_id": str(
                    event.event_id
                ),
                "sender_user_id": str(
                    event.sender_user_id
                ),
                "target_user_id": (
                    str(
                        event.target_user_id
                    )
                    if event.target_user_id
                    else None
                ),
                "signal_type": (
                    event.signal_type.value
                ),
            },
        )

        return VoiceSignalResponse(
            event=event
        )

    async def poll_signals(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
    ) -> VoiceSignalPollResponse:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        await self._require_joined_participant(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        key = self._signal_queue_key(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        raw_items = await (
            redis_client.lrange(
                key,
                0,
                -1,
            )
        )

        if raw_items:
            await redis_client.delete(
                key
            )

        events = [
            VoiceSignalEnvelope
            .model_validate_json(
                raw
            )
            for raw in raw_items
        ]

        return VoiceSignalPollResponse(
            events=events
        )

    # =====================================================
    # HEARTBEAT
    # =====================================================

    async def heartbeat(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        payload: VoicePresenceHeartbeatRequest,
    ) -> VoiceRealtimeStateResponse:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        await self._require_joined_participant(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        _, current_speaking = await (
            self.realtime_state(
                call_id=call.id,
                user_id=(
                    access.actor_user_id
                ),
            )
        )

        await self._set_presence(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
            presence=(
                VoicePresenceState.CONNECTED
            ),
            speaking=current_speaking,
            connection_id=(
                payload.connection_id
            ),
        )

        return VoiceRealtimeStateResponse(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
            presence=(
                VoicePresenceState.CONNECTED
            ),
            speaking=current_speaking,
        )

    # =====================================================
    # SPEAKING
    # =====================================================

    async def speaking(
        self,
        *,
        access: VoiceChannelAccess,
        channel_id: uuid.UUID,
        speaking: bool,
    ) -> VoiceRealtimeStateResponse:
        call = await (
            self._require_active_call(
                channel_id=channel_id
            )
        )

        await self._require_joined_participant(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        key = self._presence_key(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
        )

        current = await (
            redis_client.hgetall(
                key
            )
        )

        connection_id = (
            current.get(
                "connection_id",
                "voice",
            )
            if current
            else "voice"
        )

        await self._set_presence(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
            presence=(
                VoicePresenceState.CONNECTED
            ),
            speaking=speaking,
            connection_id=(
                connection_id
            ),
        )

        await self.publish(
            call_id=call.id,
            event_type="voice.speaking",
            payload={
                "user_id": str(
                    access.actor_user_id
                ),
                "speaking": speaking,
            },
        )

        return VoiceRealtimeStateResponse(
            call_id=call.id,
            user_id=(
                access.actor_user_id
            ),
            presence=(
                VoicePresenceState.CONNECTED
            ),
            speaking=speaking,
        )

    # =====================================================
    # INTERNAL
    # =====================================================

    async def _require_active_call(
        self,
        *,
        channel_id: uuid.UUID,
    ) -> Any:
        await self.require_voice_channel(
            channel_id=channel_id
        )

        call = await (
            self.repository.active_call(
                channel_id=channel_id
            )
        )

        if call is None:
            raise VoiceChannelNotFoundError(
                "No active voice call."
            )

        return call

    async def _require_joined_participant(
        self,
        *,
        call_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Any:
        participant = await (
            self.repository.participant(
                call_id=call_id,
                user_id=user_id,
            )
        )

        if (
            participant is None
            or participant.state
            != VOICE_PARTICIPANT_JOINED
        ):
            raise VoiceChannelPermissionError(
                "You must join the voice "
                "channel first."
            )

        return participant

    @staticmethod
    def capabilities(
    ) -> VoiceCapabilitiesResponse:
        return (
            VoiceCapabilitiesResponse()
        )


__all__ = [
    "VoiceChannelNotFoundError",
    "VoiceChannelPermissionError",
    "VoiceChannelService",
]