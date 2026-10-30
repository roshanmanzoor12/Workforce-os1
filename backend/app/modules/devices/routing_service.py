from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.routing_models import (
    DEVICE_ROUTE_STATUS_ACTIVE,
    DEVICE_ROUTE_STATUS_REVOKED,
    DeviceRoute,
)
from app.modules.devices.routing_repository import (
    DeviceRoutingRepository,
)


# =========================================================
# RESOLVED ROUTE
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ResolvedDeviceRoute:
    """
    Trusted control-plane device routing result.

    Physical tenant DB details are intentionally not included here.
    Those are resolved from TenantDatabaseRegistry.
    """

    route_id: uuid.UUID
    workspace_id: uuid.UUID
    device_uuid: uuid.UUID
    tenant_device_id: uuid.UUID


# =========================================================
# DEVICE ROUTING SERVICE
# =========================================================


class DeviceRoutingService:
    """
    Control-plane service for global device routing.

    Flow:

        device_uuid
            ↓
        workforce_control.device_routes
            ↓
        workspace_id
            ↓
        TenantDatabaseRegistry
            ↓
        correct tenant database

    This service never opens tenant databases directly.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            DeviceRoutingRepository(
                session
            )
        )

    # =====================================================
    # TIME
    # =====================================================

    @staticmethod
    def _now() -> datetime:
        return datetime.now(
            timezone.utc
        )

    # =====================================================
    # CREATE ROUTE
    # =====================================================

    async def create_route(
        self,
        *,
        workspace_id: uuid.UUID,
        device_uuid: uuid.UUID,
        tenant_device_id: uuid.UUID,
    ) -> DeviceRoute:
        """
        Create the trusted global route for one tenant-local Device.
        """

        existing_device_route = (
            await self.repository.get_by_device_uuid(
                device_uuid
            )
        )

        if existing_device_route is not None:
            raise ConflictError(
                "Device routing identity already exists."
            )

        existing_tenant_route = (
            await self.repository.get_workspace_device_route(
                workspace_id=workspace_id,
                tenant_device_id=tenant_device_id,
            )
        )

        if existing_tenant_route is not None:
            raise ConflictError(
                "Tenant device routing identity already exists."
            )

        route = (
            await self.repository.create_route(
                workspace_id=workspace_id,
                device_uuid=device_uuid,
                tenant_device_id=tenant_device_id,
                status=DEVICE_ROUTE_STATUS_ACTIVE,
                is_active=True,
                registered_at=self._now(),
            )
        )

        await self.session.commit()

        await self.session.refresh(
            route
        )

        return route

    # =====================================================
    # RESOLVE ROUTE
    # =====================================================

    async def resolve_device_route(
        self,
        *,
        device_uuid: uuid.UUID,
    ) -> ResolvedDeviceRoute:
        """
        Resolve a globally unique device UUID to its trusted workspace.

        Revoked/inactive routes intentionally return the same
        not-found style error used by device authentication.
        """

        route = (
            await self.repository.get_active_by_device_uuid(
                device_uuid
            )
        )

        if route is None:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if (
            route.status
            != DEVICE_ROUTE_STATUS_ACTIVE
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if not route.is_active:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        return ResolvedDeviceRoute(
            route_id=route.id,
            workspace_id=route.workspace_id,
            device_uuid=route.device_uuid,
            tenant_device_id=route.tenant_device_id,
        )

    # =====================================================
    # REVOKE ROUTE
    # =====================================================

    async def revoke_route(
        self,
        *,
        device_uuid: uuid.UUID,
    ) -> None:
        """
        Revoke the control-plane route for a device.

        Idempotent:
        - missing route -> no-op
        - already revoked -> no-op
        """

        route = (
            await self.repository.get_by_device_uuid_for_update(
                device_uuid
            )
        )

        if route is None:
            return

        if (
            route.status
            == DEVICE_ROUTE_STATUS_REVOKED
        ):
            return

        await self.repository.revoke_route(
            route,
            revoked_at=self._now(),
            revoked_status=(
                DEVICE_ROUTE_STATUS_REVOKED
            ),
        )

        await self.session.commit()

    # =====================================================
    # IDENTITY VALIDATION
    # =====================================================

    @staticmethod
    def validate_route_identity(
        route: ResolvedDeviceRoute,
        *,
        expected_device_uuid: uuid.UUID,
        expected_workspace_id: uuid.UUID | None = None,
        expected_tenant_device_id: uuid.UUID | None = None,
    ) -> None:
        """
        Cross-check a previously resolved route against expected
        trusted identities.
        """

        if (
            route.device_uuid
            != expected_device_uuid
        ):
            raise ValidationError(
                "Device routing identity mismatch."
            )

        if (
            expected_workspace_id is not None
            and route.workspace_id
            != expected_workspace_id
        ):
            raise ValidationError(
                "Device routing workspace mismatch."
            )

        if (
            expected_tenant_device_id is not None
            and route.tenant_device_id
            != expected_tenant_device_id
        ):
            raise ValidationError(
                "Device routing tenant identity mismatch."
            )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ResolvedDeviceRoute",
    "DeviceRoutingService",
]