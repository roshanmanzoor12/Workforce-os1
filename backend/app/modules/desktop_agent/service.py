from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.monitoring.models import MonitoringConsent

from app.core.exceptions import ValidationError
from app.modules.desktop_agent.access import (
    DesktopAgentAccess,
    can_view_employee,
    require_actor_employee,
)
from app.modules.desktop_agent.models import (
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_ONLINE,
    DesktopAgentDevice,
)
from app.modules.desktop_agent.repository import (
    DesktopAgentRepository,
)
from app.modules.desktop_agent.schemas import (
    DesktopAgentCapabilitiesResponse,
    DesktopAgentDeviceListResponse,
    DesktopAgentDeviceResponse,
    DesktopAgentHeartbeatRequest,
    DesktopAgentHeartbeatResponse,
    DesktopAgentRegisterRequest,
)


class DesktopAgentNotFoundError(
    LookupError
):
    pass


class DesktopAgentPermissionError(
    PermissionError
):
    pass


class DesktopAgentService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            DesktopAgentRepository(
                session
            )
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    @staticmethod
    def _capabilities() -> dict:
        return {
            "device_registration": True,
            "heartbeat": True,
            "activity_state": True,
            "activity_reporting": True,
            "screenshot_capture": False,
            "screen_capture": True,
            "live_screen": True,
            "keystroke_capture": False,
            "clipboard_capture": False,
            "password_capture": False,
            "mouse_coordinate_capture": False,
        }

    @staticmethod
    def _response(
        device: DesktopAgentDevice,
    ) -> DesktopAgentDeviceResponse:
        return (
            DesktopAgentDeviceResponse
            .model_validate(
                device
            )
        )

    async def register(
        self,
        *,
        access: DesktopAgentAccess,
        payload: DesktopAgentRegisterRequest,
        ip_address: str | None,
    ) -> DesktopAgentDeviceResponse:
        if not access.can_register_self:
            raise DesktopAgentPermissionError(
                "Device registration permission "
                "required."
            )

        employee_id = require_actor_employee(
            access
        )

        if (
            payload.consent_acknowledged
            is not True
        ):
            raise ValidationError(
                "Desktop agent consent must be "
                "acknowledged before registration."
            )

        # WFOS_SAVED_CONSENT_GATE_V1
        # A request flag alone is not sufficient proof of consent.
        # Validate the authenticated employee's saved preference.
        consent_result = await self.session.execute(
            select(MonitoringConsent).where(
                MonitoringConsent.user_id == access.actor_user_id,
                MonitoringConsent.granted.is_(True),
                MonitoringConsent.revoked_at.is_(None),
            )
        )

        saved_consent = consent_result.scalar_one_or_none()

        if saved_consent is None:
            raise DesktopAgentPermissionError(
                "Monitoring consent is required. "
                "Sign in to the employee workspace and "
                "select Allow & remember before enrolling."
            )
        now = self._now()

        existing = await (
            self.repository
            .get_by_installation_id(
                installation_id=(
                    payload
                    .installation_id
                )
            )
        )

        if existing is not None:
            if (
                existing.user_id
                != access.actor_user_id
            ):
                raise DesktopAgentPermissionError(
                    "This installation is already "
                    "registered to another user."
                )

            if (
                existing.employee_id
                != employee_id
            ):
                raise DesktopAgentPermissionError(
                    "This installation is already "
                    "registered to another employee."
                )

            if existing.is_disabled:
                raise DesktopAgentPermissionError(
                    "This desktop agent device is "
                    "disabled by workspace policy."
                )

            existing.device_name = (
                payload.device_name
            )

            existing.platform = (
                payload.platform
            )

            existing.os_version = (
                payload.os_version
            )

            existing.agent_version = (
                payload.agent_version
            )

            existing.consent_version = (
                payload.consent_version
            )

            existing.consent_at = now

            existing.last_seen_at = now

            existing.last_ip_address = (
                ip_address
            )

            existing.status = (
                DEVICE_STATUS_ONLINE
            )

            existing.capabilities = (
                self._capabilities()
            )

            existing = await (
                self.repository.refresh(
                    device=existing
                )
            )

            return self._response(
                existing
            )

        device = DesktopAgentDevice(
            user_id=(
                access.actor_user_id
            ),

            employee_id=employee_id,

            installation_id=(
                payload.installation_id
            ),

            device_name=(
                payload.device_name
            ),

            platform=(
                payload.platform
            ),

            os_version=(
                payload.os_version
            ),

            agent_version=(
                payload.agent_version
            ),

            status=(
                DEVICE_STATUS_ONLINE
            ),

            is_disabled=False,

            consent_version=(
                payload.consent_version
            ),

            consent_at=now,

            capabilities=(
                self._capabilities()
            ),

            last_seen_at=now,

            last_ip_address=(
                ip_address
            ),

            registered_at=now,
        )

        device = await (
            self.repository.create(
                device=device
            )
        )

        return self._response(
            device
        )

    async def heartbeat(
        self,
        *,
        access: DesktopAgentAccess,
        device_id: uuid.UUID,
        payload: DesktopAgentHeartbeatRequest,
        ip_address: str | None,
    ) -> DesktopAgentHeartbeatResponse:
        device = await (
            self.repository.get(
                device_id=device_id
            )
        )

        if device is None:
            raise DesktopAgentNotFoundError(
                "Desktop agent device not found."
            )

        # Heartbeat is intentionally owner-only.
        #
        # Admin visibility does not allow an administrator
        # to impersonate the endpoint used by the employee's
        # desktop agent.
        if (
            device.user_id
            != access.actor_user_id
        ):
            raise DesktopAgentPermissionError(
                "Desktop agent heartbeat may only "
                "be sent by the registered user."
            )

        if device.is_disabled:
            raise DesktopAgentPermissionError(
                "Desktop agent device is disabled."
            )

        # WFOS_HEARTBEAT_SAVED_CONSENT_V2
        # An existing enrollment must respect consent revocation.
        consent_result = await self.session.execute(
            select(MonitoringConsent).where(
                MonitoringConsent.user_id == device.user_id,
                MonitoringConsent.granted.is_(True),
                MonitoringConsent.revoked_at.is_(None),
            )
        )

        saved_consent = consent_result.scalar_one_or_none()

        if saved_consent is None:
            raise DesktopAgentPermissionError(
                "Employee monitoring consent is disabled."
            )

        device = await (
            self.repository.mark_seen(
                device=device,

                seen_at=self._now(),

                agent_version=(
                    payload.agent_version
                ),

                os_version=(
                    payload.os_version
                ),

                ip_address=ip_address,
            )
        )

        # Refresh persisted capabilities for already-enrolled devices so
        # readiness and the owner request button see the native capability.
        device.capabilities = self._capabilities()
        await self.session.flush()

        return DesktopAgentHeartbeatResponse(
            device_id=device.id,
            accepted=True,
            status=device.status,
            last_seen_at=(
                device.last_seen_at
            ),
        )

    async def get(
        self,
        *,
        access: DesktopAgentAccess,
        device_id: uuid.UUID,
    ) -> DesktopAgentDeviceResponse:
        device = await (
            self.repository.get(
                device_id=device_id
            )
        )

        if device is None:
            raise DesktopAgentNotFoundError(
                "Desktop agent device not found."
            )

        if not can_view_employee(
            access=access,
            employee_id=(
                device.employee_id
            ),
        ):
            raise DesktopAgentPermissionError(
                "Device is outside your permitted "
                "employee scope."
            )

        return self._response(
            device
        )

    async def list(
        self,
        *,
        access: DesktopAgentAccess,
        status: str | None,
        limit: int,
        offset: int,
    ) -> DesktopAgentDeviceListResponse:
        allowed_statuses = {
            "online",
            "offline",
            "disabled",
        }

        if (
            status is not None
            and status
            not in allowed_statuses
        ):
            raise ValidationError(
                "status must be online, "
                "offline, or disabled."
            )

        devices, total = await (
            self.repository.list(
                employee_ids=(
                    access
                    .visible_employee_ids
                ),

                status=status,

                limit=limit,

                offset=offset,
            )
        )

        return DesktopAgentDeviceListResponse(
            items=[
                self._response(
                    device
                )
                for device
                in devices
            ],

            total=total,

            limit=limit,

            offset=offset,
        )

    async def disable(
        self,
        *,
        access: DesktopAgentAccess,
        device_id: uuid.UUID,
    ) -> DesktopAgentDeviceResponse:
        if not access.can_manage:
            raise DesktopAgentPermissionError(
                "Device management permission "
                "required."
            )

        device = await (
            self.repository.get(
                device_id=device_id
            )
        )

        if device is None:
            raise DesktopAgentNotFoundError(
                "Desktop agent device not found."
            )

        device = await (
            self.repository.disable(
                device=device
            )
        )

        if (
            device.status
            != DEVICE_STATUS_DISABLED
        ):
            raise RuntimeError(
                "Failed to disable desktop agent."
            )

        return self._response(
            device
        )

    @staticmethod
    def capabilities(
    ) -> DesktopAgentCapabilitiesResponse:
        return DesktopAgentCapabilitiesResponse(
            device_registration=True,
            authenticated_heartbeat=True,
            consent_required=True,
            self_device_access=True,
            team_device_access=True,
            workspace_device_access=True,
            admin_disable=True,
            screenshot_capture=False,
            live_screen=True,
            captures_keystrokes=False,
            captures_clipboard=False,
            captures_passwords=False,
            captures_mouse_coordinates=False,
        )


__all__ = [
    "DesktopAgentNotFoundError",
    "DesktopAgentPermissionError",
    "DesktopAgentService",
]

