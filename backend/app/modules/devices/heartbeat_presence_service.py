from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound
from app.modules.devices.heartbeat_presence import (
    DEVICE_ONLINE_TIMEOUT_SECONDS,
    get_device_presence,
)
from app.modules.devices.heartbeat_presence_schemas import (
    DevicePresenceResponse,
)
from app.modules.devices.models import Device


__all__ = [
    "DevicePresenceService",
]


class DevicePresenceService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    async def get_presence(
        self,
        *,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
    ) -> DevicePresenceResponse:
        statement = select(
            Device
        ).where(
            Device.id == device_id,
            Device.device_uuid == device_uuid,
        )

        result = await self.session.execute(
            statement
        )

        device = result.scalar_one_or_none()

        if device is None:
            raise ResourceNotFound(
                "Device not found."
            )

        presence = get_device_presence(
            device,
            now=self._now(),
        )

        return DevicePresenceResponse(
            device_uuid=device.device_uuid,
            is_online=presence.is_online,
            last_seen_at=presence.last_seen_at,
            offline_since=presence.offline_since,
            online_timeout_seconds=(
                DEVICE_ONLINE_TIMEOUT_SECONDS
            ),
        )