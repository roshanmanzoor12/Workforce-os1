from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.routing_models import (
    DeviceRoute,
)


class DeviceRoutingRepository:
    """
    Control-plane persistence layer for registered-device routing.

    This repository operates only against workforce_control.

    Responsibilities:

    - create DeviceRoute rows
    - resolve device_uuid -> trusted workspace
    - resolve tenant-local device identity
    - lock routes during lifecycle changes
    - revoke routes safely

    It never opens a tenant database.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CREATE
    # =====================================================

    async def create_route(
        self,
        *,
        workspace_id: uuid.UUID,
        device_uuid: uuid.UUID,
        tenant_device_id: uuid.UUID,
        status: str,
        is_active: bool,
        registered_at: datetime | None,
    ) -> DeviceRoute:
        route = DeviceRoute(
            workspace_id=workspace_id,
            device_uuid=device_uuid,
            tenant_device_id=tenant_device_id,
            status=status,
            is_active=is_active,
            registered_at=registered_at,
        )

        self.session.add(
            route
        )

        await self.session.flush()

        return route

    # =====================================================
    # GET BY ROUTE ID
    # =====================================================

    async def get_by_id(
        self,
        route_id: uuid.UUID,
    ) -> DeviceRoute | None:
        result = await self.session.execute(
            select(
                DeviceRoute
            ).where(
                DeviceRoute.id
                == route_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # GET BY DEVICE UUID
    # =====================================================

    async def get_by_device_uuid(
        self,
        device_uuid: uuid.UUID,
    ) -> DeviceRoute | None:
        result = await self.session.execute(
            select(
                DeviceRoute
            ).where(
                DeviceRoute.device_uuid
                == device_uuid
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # GET ACTIVE ROUTE
    # =====================================================

    async def get_active_by_device_uuid(
        self,
        device_uuid: uuid.UUID,
    ) -> DeviceRoute | None:
        result = await self.session.execute(
            select(
                DeviceRoute
            ).where(
                DeviceRoute.device_uuid
                == device_uuid,
                DeviceRoute.is_active.is_(
                    True
                ),
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # WORKSPACE + TENANT DEVICE LOOKUP
    # =====================================================

    async def get_workspace_device_route(
        self,
        *,
        workspace_id: uuid.UUID,
        tenant_device_id: uuid.UUID,
    ) -> DeviceRoute | None:
        result = await self.session.execute(
            select(
                DeviceRoute
            ).where(
                DeviceRoute.workspace_id
                == workspace_id,
                DeviceRoute.tenant_device_id
                == tenant_device_id,
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # LOCKED LOOKUP
    # =====================================================

    async def get_by_device_uuid_for_update(
        self,
        device_uuid: uuid.UUID,
    ) -> DeviceRoute | None:
        """
        Fetch and row-lock one DeviceRoute until transaction end.

        Used during route revocation or other concurrency-sensitive
        lifecycle transitions.
        """

        result = await self.session.execute(
            select(
                DeviceRoute
            )
            .where(
                DeviceRoute.device_uuid
                == device_uuid
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    # =====================================================
    # GENERIC UPDATE
    # =====================================================

    async def update_route(
        self,
        route: DeviceRoute,
        *,
        values: dict[str, object],
    ) -> DeviceRoute:
        for field_name, value in values.items():
            setattr(
                route,
                field_name,
                value,
            )

        await self.session.flush()

        return route

    # =====================================================
    # REVOKE
    # =====================================================

    async def revoke_route(
        self,
        route: DeviceRoute,
        *,
        revoked_at: datetime,
        revoked_status: str,
    ) -> DeviceRoute:
        route.status = (
            revoked_status
        )

        route.is_active = False

        route.revoked_at = (
            revoked_at
        )

        await self.session.flush()

        return route


__all__ = [
    "DeviceRoutingRepository",
]