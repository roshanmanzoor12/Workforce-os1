from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound
from app.modules.devices.heartbeat_schemas import (
    DeviceHeartbeatRequest,
    DeviceHeartbeatResponse,
)
from app.modules.devices.desktop_presence_bridge import synchronize_desktop_presence
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_OFFLINE,
    DEVICE_STATUS_REVOKED,
    Device,
)


__all__ = [
    "DEFAULT_HEARTBEAT_INTERVAL_SECONDS",
    "DeviceHeartbeatService",
]


DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 10


class DeviceHeartbeatService:
    """
    Tenant-local heartbeat mutation service.

    Device identity must already have been authenticated through
    the control-plane device-auth flow before this service is called.

    The agent cannot choose:
    - workspace
    - tenant database
    - device database ID
    - device UUID
    - online/offline state
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =========================================================
    # TIME
    # =========================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    # =========================================================
    # HEARTBEAT
    # =========================================================

    async def record_heartbeat(
        self,
        *,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
        payload: DeviceHeartbeatRequest,
    ) -> DeviceHeartbeatResponse:
        """
        Record one authenticated agent heartbeat.

        The server timestamp is authoritative.

        An offline device becomes active again when it sends a valid
        authenticated heartbeat.

        Disabled/revoked/inactive devices are rejected.
        """

        statement = (
            select(Device)
            .where(
                Device.id == device_id,
                Device.device_uuid == device_uuid,
            )
            .with_for_update()
        )

        result = await self.session.execute(
            statement
        )

        device = result.scalar_one_or_none()

        if device is None:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if (
            not device.is_active
            or device.status
            in {
                DEVICE_STATUS_DISABLED,
                DEVICE_STATUS_REVOKED,
            }
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        now = self._now()

        # -----------------------------------------------------
        # PRESENCE
        # -----------------------------------------------------

        if device.first_seen_at is None:
            device.first_seen_at = now

        device.last_seen_at = now

        # Offline is derived from heartbeat absence.
        # A valid heartbeat restores the device to active.
        if device.status == DEVICE_STATUS_OFFLINE:
            device.status = DEVICE_STATUS_ACTIVE

        # -----------------------------------------------------
        # SAFE MACHINE METADATA SYNC
        # -----------------------------------------------------

        if payload.agent_version is not None:
            device.agent_version = (
                payload.agent_version
            )

        if payload.hostname is not None:
            device.hostname = payload.hostname

        # WFOS_AUTHENTICATED_DESKTOP_PRESENCE_V1
        # Device is resolved by X-Device-UUID / X-Device-Secret above.
        # Sync does not grant screen-capture capability.
        # WFOS_BRIDGE_OUTCOME_LOG_V2
        bridge_outcome = await synchronize_desktop_presence(
            self.session,
            device=device,
            seen_at=now,
        )

        import logging
        logging.getLogger(__name__).warning(
            "WorkforceOS desktop bridge: outcome=%s",
            bridge_outcome,
        )

        try:
            await self.session.commit()

            await self.session.refresh(
                device
            )

        except Exception:
            await self.session.rollback()
            raise

        return DeviceHeartbeatResponse(
            device_uuid=device.device_uuid,
            status=device.status,
            heartbeat_at=now,
            next_heartbeat_seconds=(
                DEFAULT_HEARTBEAT_INTERVAL_SECONDS
            ),
        )