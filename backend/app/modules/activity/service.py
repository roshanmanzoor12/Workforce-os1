from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFound
from app.modules.activity.models import (
    ACTIVITY_STATE_ACTIVE,
    ACTIVITY_STATE_IDLE,
    ActivityStateEvent,
)
from app.modules.activity.repository import (
    ActivityRepository,
)
from app.modules.activity.schemas import (
    ActivityStateRequest,
    ActivityStateResponse,
    ActivityStatusResponse,
)
from app.modules.devices.models import Device


__all__ = [
    "ActivityService",
]


class ActivityService:
    """
    Tenant-local active/idle activity service.

    Device identity and tenant routing must already be resolved
    through authenticated device context before this service is used.

    The agent cannot choose:
    - workspace
    - tenant database
    - device database identity
    - employee assignment
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = ActivityRepository(
            session
        )

    # =========================================================
    # TIME
    # =========================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    # =========================================================
    # DEVICE LOOKUP
    # =========================================================

    async def _get_device(
        self,
        *,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
    ) -> Device:
        statement = (
            select(
                Device
            )
            .where(
                Device.id == device_id,
                Device.device_uuid == device_uuid,
            )
            .limit(
                1
            )
        )

        result = await self.session.execute(
            statement
        )

        device = result.scalar_one_or_none()

        if device is None:
            raise ResourceNotFound(
                "Device not found."
            )

        return device

    # =========================================================
    # RECORD STATE
    # =========================================================

    async def record_state(
        self,
        *,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
        payload: ActivityStateRequest,
    ) -> ActivityStateResponse:
        """
        Record one active/idle observation from an authenticated agent.

        Employee assignment is always resolved from the current
        tenant-side device record.

        Server received_at is authoritative.
        """

        device = await self._get_device(
            device_id=device_id,
            device_uuid=device_uuid,
        )

        received_at = self._now()

        observed_at = payload.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(
                tzinfo=timezone.utc
            )

        last_input_at = payload.last_input_at

        if (
            last_input_at is not None
            and last_input_at.tzinfo is None
        ):
            last_input_at = last_input_at.replace(
                tzinfo=timezone.utc
            )

        state = (
            payload.state
            .strip()
            .lower()
        )

        if state not in {
            ACTIVITY_STATE_ACTIVE,
            ACTIVITY_STATE_IDLE,
        }:
            raise ValueError(
                "Unsupported activity state."
            )

        event: ActivityStateEvent | None = None

        try:
            event = await self.repository.create_event(
                device_id=device.id,
                employee_id=device.employee_id,
                state=state,
                idle_seconds=payload.idle_seconds,
                last_input_at=last_input_at,
                observed_at=observed_at,
                received_at=received_at,
            )

            await self.repository.commit()

            event = await self.repository.refresh(
                event
            )

        except Exception:
            await self.repository.rollback()
            raise

        return ActivityStateResponse(
            event_id=event.id,
            device_uuid=device.device_uuid,
            employee_id=event.employee_id,
            state=event.state,
            idle_seconds=event.idle_seconds,
            last_input_at=event.last_input_at,
            observed_at=event.observed_at,
            received_at=event.received_at,
        )

    # =========================================================
    # CURRENT DEVICE STATUS
    # =========================================================

    async def get_device_status(
        self,
        *,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
    ) -> ActivityStatusResponse:
        device = await self._get_device(
            device_id=device_id,
            device_uuid=device_uuid,
        )

        latest_event = (
            await self.repository
                .get_latest_for_device(
                    device_id=device.id
                )
        )

        if latest_event is None:
            return ActivityStatusResponse(
                device_uuid=device.device_uuid,
                employee_id=device.employee_id,
                state=ACTIVITY_STATE_IDLE,
                idle_seconds=0,
                last_input_at=None,
                observed_at=None,
                received_at=None,
            )

        return ActivityStatusResponse(
            device_uuid=device.device_uuid,
            employee_id=latest_event.employee_id,
            state=latest_event.state,
            idle_seconds=latest_event.idle_seconds,
            last_input_at=latest_event.last_input_at,
            observed_at=latest_event.observed_at,
            received_at=latest_event.received_at,
        )

    # =========================================================
    # CURRENT EMPLOYEE STATUS
    # =========================================================

    async def get_employee_status(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> ActivityStatusResponse | None:
        latest_event = (
            await self.repository
                .get_latest_for_employee(
                    employee_id=employee_id
                )
        )

        if latest_event is None:
            return None

        device = await self._get_device(
            device_id=latest_event.device_id,
            device_uuid=(
                await self._get_device_uuid(
                    device_id=latest_event.device_id
                )
            ),
        )

        return ActivityStatusResponse(
            device_uuid=device.device_uuid,
            employee_id=latest_event.employee_id,
            state=latest_event.state,
            idle_seconds=latest_event.idle_seconds,
            last_input_at=latest_event.last_input_at,
            observed_at=latest_event.observed_at,
            received_at=latest_event.received_at,
        )

    # =========================================================
    # DEVICE UUID LOOKUP
    # =========================================================

    async def _get_device_uuid(
        self,
        *,
        device_id: uuid.UUID,
    ) -> uuid.UUID:
        statement = (
            select(
                Device.device_uuid
            )
            .where(
                Device.id == device_id
            )
            .limit(
                1
            )
        )

        result = await self.session.execute(
            statement
        )

        device_uuid = result.scalar_one_or_none()

        if device_uuid is None:
            raise ResourceNotFound(
                "Device not found."
            )

        return device_uuid