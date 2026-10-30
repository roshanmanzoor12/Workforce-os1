from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from app.modules.channels.realtime_bus import (
    channel_realtime_bus,
)
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeEvent,
    WorkspaceChannelRealtimeEventType,
)


class WorkspaceChannelRealtimeEventPublisher:
    """
    Converts existing channel/message domain objects into
    stable realtime payloads.

    This module intentionally accepts generic domain objects
    instead of importing repository/service implementation
    details. That keeps it compatible with the existing
    channel module while still enforcing a stable realtime
    contract.

    It does not mutate database records.

    It only publishes after a calling service/router has
    successfully completed its persistence operation.
    """

    # =====================================================
    # NORMALIZATION HELPERS
    # =====================================================

    @staticmethod
    def _value(
        value: Any,
    ) -> Any:
        """
        Convert common domain values into JSON-safe values.
        """

        if value is None:
            return None

        if isinstance(
            value,
            uuid.UUID,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            datetime,
        ):
            return (
                value.isoformat()
            )

        if isinstance(
            value,
            Enum,
        ):
            return value.value

        return value

    @classmethod
    def _required(
        cls,
        obj: Any,
        name: str,
    ) -> Any:
        if not hasattr(
            obj,
            name,
        ):
            raise ValueError(
                "Realtime event object "
                f"is missing required field: "
                f"{name}"
            )

        return getattr(
            obj,
            name,
        )

    @classmethod
    def _optional(
        cls,
        obj: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        return getattr(
            obj,
            name,
            default,
        )

    @classmethod
    def _uuid(
        cls,
        value: Any,
        *,
        field_name: str,
    ) -> uuid.UUID:
        if isinstance(
            value,
            uuid.UUID,
        ):
            return value

        try:
            return uuid.UUID(
                str(
                    value
                )
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
        ) as exc:
            raise ValueError(
                "Invalid UUID for "
                f"{field_name}: "
                f"{value!r}"
            ) from exc

    # =====================================================
    # CHANNEL PAYLOAD
    # =====================================================

    @classmethod
    def channel_payload(
        cls,
        channel: Any,
    ) -> dict[str, Any]:
        """
        Build the canonical public realtime channel payload.
        """

        return {
            "id": cls._value(
                cls._required(
                    channel,
                    "id",
                )
            ),
            "workspace_id": cls._value(
                cls._required(
                    channel,
                    "workspace_id",
                )
            ),
            "name": cls._value(
                cls._required(
                    channel,
                    "name",
                )
            ),
            "slug": cls._value(
                cls._required(
                    channel,
                    "slug",
                )
            ),
            "channel_type": cls._value(
                cls._required(
                    channel,
                    "channel_type",
                )
            ),
            "created_by_user_id": cls._value(
                cls._required(
                    channel,
                    "created_by_user_id",
                )
            ),
            "is_active": bool(
                cls._required(
                    channel,
                    "is_active",
                )
            ),
            "created_at": cls._value(
                cls._required(
                    channel,
                    "created_at",
                )
            ),
            "updated_at": cls._value(
                cls._required(
                    channel,
                    "updated_at",
                )
            ),
        }

    # =====================================================
    # MESSAGE PAYLOAD
    # =====================================================

    @classmethod
    def message_payload(
        cls,
        message: Any,
    ) -> dict[str, Any]:
        """
        Build the canonical public realtime message payload.
        """

        return {
            "id": cls._value(
                cls._required(
                    message,
                    "id",
                )
            ),
            "channel_id": cls._value(
                cls._required(
                    message,
                    "channel_id",
                )
            ),
            "sender_user_id": cls._value(
                cls._optional(
                    message,
                    "sender_user_id",
                )
            ),
            "message_type": cls._value(
                cls._required(
                    message,
                    "message_type",
                )
            ),
            "content": cls._value(
                cls._required(
                    message,
                    "content",
                )
            ),
            "edited_at": cls._value(
                cls._optional(
                    message,
                    "edited_at",
                )
            ),
            "deleted_at": cls._value(
                cls._optional(
                    message,
                    "deleted_at",
                )
            ),
            "created_at": cls._value(
                cls._required(
                    message,
                    "created_at",
                )
            ),
        }

    # =====================================================
    # CHANNEL CREATED
    # =====================================================

    async def channel_created(
        self,
        *,
        channel: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        workspace_id = self._uuid(
            self._required(
                channel,
                "workspace_id",
            ),
            field_name=(
                "channel.workspace_id"
            ),
        )

        channel_id = self._uuid(
            self._required(
                channel,
                "id",
            ),
            field_name=(
                "channel.id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .CHANNEL_CREATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.channel_payload(
                        channel
                    )
                ),
            )
        )

    # =====================================================
    # CHANNEL UPDATED
    # =====================================================

    async def channel_updated(
        self,
        *,
        channel: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        workspace_id = self._uuid(
            self._required(
                channel,
                "workspace_id",
            ),
            field_name=(
                "channel.workspace_id"
            ),
        )

        channel_id = self._uuid(
            self._required(
                channel,
                "id",
            ),
            field_name=(
                "channel.id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .CHANNEL_UPDATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.channel_payload(
                        channel
                    )
                ),
            )
        )

    # =====================================================
    # CHANNEL ARCHIVED
    # =====================================================

    async def channel_archived(
        self,
        *,
        channel: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        workspace_id = self._uuid(
            self._required(
                channel,
                "workspace_id",
            ),
            field_name=(
                "channel.workspace_id"
            ),
        )

        channel_id = self._uuid(
            self._required(
                channel,
                "id",
            ),
            field_name=(
                "channel.id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .CHANNEL_ARCHIVED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.channel_payload(
                        channel
                    )
                ),
            )
        )

    # =====================================================
    # MESSAGE CREATED
    # =====================================================

    async def message_created(
        self,
        *,
        workspace_id: uuid.UUID,
        message: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        channel_id = self._uuid(
            self._required(
                message,
                "channel_id",
            ),
            field_name=(
                "message.channel_id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_CREATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.message_payload(
                        message
                    )
                ),
            )
        )

    # =====================================================
    # MESSAGE UPDATED
    # =====================================================

    async def message_updated(
        self,
        *,
        workspace_id: uuid.UUID,
        message: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        channel_id = self._uuid(
            self._required(
                message,
                "channel_id",
            ),
            field_name=(
                "message.channel_id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_UPDATED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.message_payload(
                        message
                    )
                ),
            )
        )

    # =====================================================
    # MESSAGE DELETED
    # =====================================================

    async def message_deleted(
        self,
        *,
        workspace_id: uuid.UUID,
        message: Any,
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        channel_id = self._uuid(
            self._required(
                message,
                "channel_id",
            ),
            field_name=(
                "message.channel_id"
            ),
        )

        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .MESSAGE_DELETED
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload=(
                    self.message_payload(
                        message
                    )
                ),
            )
        )

    # =====================================================
    # ATTACHMENT BOUND
    # =====================================================

    async def attachment_bound(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        attachment_ids:
            list[uuid.UUID],
        actor_user_id:
            uuid.UUID | None = None,
    ) -> WorkspaceChannelRealtimeEvent:
        return await (
            channel_realtime_bus
            .publish(
                workspace_id=workspace_id,
                channel_id=channel_id,
                event_type=(
                    WorkspaceChannelRealtimeEventType
                    .ATTACHMENT_BOUND
                ),
                actor_user_id=(
                    actor_user_id
                ),
                payload={
                    "message_id": str(
                        message_id
                    ),
                    "channel_id": str(
                        channel_id
                    ),
                    "attachment_ids": [
                        str(
                            item
                        )
                        for item
                        in attachment_ids
                    ],
                },
            )
        )


channel_realtime_events = (
    WorkspaceChannelRealtimeEventPublisher()
)


__all__ = [
    "WorkspaceChannelRealtimeEventPublisher",
    "channel_realtime_events",
]