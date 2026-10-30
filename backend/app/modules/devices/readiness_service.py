from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.devices.readiness_access import (
    DeviceReadinessAccess,
)
from app.modules.devices.readiness_policy import (
    evaluate_device_readiness,
)
from app.modules.devices.readiness_repository import (
    DeviceReadinessRepository,
)
from app.modules.devices.readiness_schemas import (
    DeviceReadinessItem,
    DeviceReadinessResponse,
    DeviceReadinessSummary,
)
from app.modules.devices.readiness_types import (
    DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS,
)


# =========================================================
# SERVICE
# =========================================================


class DeviceReadinessService:
    """
    Backend-authoritative device readiness projection.

    This service does not mutate:

    - device status
    - heartbeat timestamps
    - capabilities
    - employee assignments

    It derives browser-facing readiness from current persisted
    evidence.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            DeviceReadinessRepository(
                session
            )
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    async def get_readiness(
        self,
        *,
        access: DeviceReadinessAccess,
    ) -> DeviceReadinessResponse:
        devices = await (
            self.repository
            .list_devices(
                employee_ids=(
                    access
                    .visible_employee_ids
                ),
            )
        )

        now = self._now()

        items: list[
            DeviceReadinessItem
        ] = []

        online = 0
        offline = 0
        disabled = 0
        monitoring_ready = 0
        live_ready = 0
        needs_setup = 0

        for device in devices:
            decision = (
                evaluate_device_readiness(
                    employee_id=(
                        device.employee_id
                    ),

                    agent_version=(
                        device.agent_version
                    ),

                    last_seen_at=(
                        device.last_seen_at
                    ),

                    is_disabled=(
                        device.is_disabled
                    ),

                    consent_at=(
                        device.consent_at
                    ),

                    capabilities=(
                        device.capabilities
                    ),

                    now=now,
                )
            )

            capabilities = dict(
                device.capabilities
                or {}
            )

            activity_capability = any(
                capabilities.get(
                    key
                )
                is True
                for key in (
                    "activity_state",
                    "activity_reporting",
                    "activity_capture",
                )
            )

            screen_capability = any(
                capabilities.get(
                    key
                )
                is True
                for key in (
                    "live_screen",
                    "screen_capture",
                    "screenshot_capture",
                )
            )

            if decision.status == "online":
                online += 1

            elif decision.status == "offline":
                offline += 1

            else:
                disabled += 1

            if decision.monitoring_ready:
                monitoring_ready += 1

            if decision.live_ready:
                live_ready += 1

            if decision.needs_setup:
                needs_setup += 1

            items.append(
                DeviceReadinessItem(
                    device_id=device.id,

                    employee_id=(
                        device.employee_id
                    ),

                    device_name=(
                        device.device_name
                    ),

                    platform=(
                        device.platform
                    ),

                    os_version=(
                        device.os_version
                    ),

                    agent_version=(
                        device.agent_version
                    ),

                    status=(
                        decision.status
                    ),

                    last_seen_at=(
                        device.last_seen_at
                    ),

                    heartbeat_age_seconds=(
                        decision
                        .heartbeat_age_seconds
                    ),

                    is_online=(
                        decision.is_online
                    ),

                    consent_granted=(
                        device.consent_at
                        is not None
                    ),

                    activity_capability=(
                        activity_capability
                    ),

                    screen_capability=(
                        screen_capability
                    ),

                    monitoring_ready=(
                        decision
                        .monitoring_ready
                    ),

                    live_ready=(
                        decision.live_ready
                    ),

                    needs_setup=(
                        decision.needs_setup
                    ),

                    setup_reasons=list(
                        decision
                        .setup_reasons
                    ),
                )
            )

        return DeviceReadinessResponse(
            summary=(
                DeviceReadinessSummary(
                    total=len(
                        items
                    ),

                    online=online,

                    offline=offline,

                    disabled=disabled,

                    monitoring_ready=(
                        monitoring_ready
                    ),

                    live_ready=(
                        live_ready
                    ),

                    needs_setup=(
                        needs_setup
                    ),

                    online_timeout_seconds=(
                        DEVICE_READINESS_ONLINE_TIMEOUT_SECONDS
                    ),
                )
            ),

            devices=items,
        )


__all__ = [
    "DeviceReadinessService",
]