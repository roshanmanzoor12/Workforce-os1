from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.db.tenant import (
    tenant_session,
    validate_tenant_cluster_key,
    validate_tenant_database_name,
)
from app.db.tenant_initialization import (
    CURRENT_TENANT_SCHEMA_VERSION,
)
from app.db.tenant_models import TenantMetadata
from app.modules.devices.routing_service import (
    DeviceRoutingService,
)
from app.modules.devices.schemas import (
    DeviceDeleteResponse,
)
from app.modules.devices.service import (
    DeviceService,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
)


# =========================================================
# DEVICE MANAGEMENT SERVICE
# =========================================================


class DeviceManagementService:
    """
    Cross-plane administrative device lifecycle orchestrator.

    Responsibilities:

        workspace-scoped admin request
            ↓
        trusted control TenantDatabaseRegistry
            ↓
        correct tenant DB
            ↓
        revoke tenant Device + credentials
            ↓
        revoke control DeviceRoute

    DeviceService remains tenant-only.
    DeviceRoutingService remains control-only.
    This service coordinates both.
    """

    def __init__(
        self,
        control_session: AsyncSession,
    ) -> None:
        self.control_session = (
            control_session
        )

        self.routing_service = (
            DeviceRoutingService(
                control_session
            )
        )

    # =====================================================
    # TENANT REGISTRY
    # =====================================================

    async def _require_ready_registry(
        self,
        *,
        workspace_id: uuid.UUID,
    ) -> TenantDatabaseRegistry:
        result = (
            await self.control_session.execute(
                select(
                    TenantDatabaseRegistry
                ).where(
                    TenantDatabaseRegistry.workspace_id
                    == workspace_id
                )
            )
        )

        registry = (
            result.scalar_one_or_none()
        )

        if registry is None:
            raise ResourceNotFound(
                "Workspace tenant is unavailable."
            )

        if (
            registry.status
            != TENANT_STATUS_READY
        ):
            raise ValidationError(
                "Workspace tenant is not ready."
            )

        validate_tenant_database_name(
            registry.database_name
        )

        validate_tenant_cluster_key(
            registry.cluster_key
        )

        return registry

    # =====================================================
    # TENANT IDENTITY
    # =====================================================

    @staticmethod
    async def _verify_tenant_identity(
        tenant_db_session: AsyncSession,
        *,
        workspace_id: uuid.UUID,
    ) -> None:
        """
        Verify the physical tenant DB before any mutation.
        """

        result = await tenant_db_session.execute(
            select(
                TenantMetadata
            )
        )

        metadata_rows = list(
            result.scalars().all()
        )

        if len(metadata_rows) != 1:
            raise ValidationError(
                "Tenant database identity "
                "verification failed."
            )

        metadata = metadata_rows[0]

        if (
            metadata.workspace_id
            != workspace_id
        ):
            raise ValidationError(
                "Tenant database identity "
                "verification failed."
            )

        if not metadata.is_active:
            raise ValidationError(
                "Tenant database is inactive."
            )

        if (
            metadata.schema_version
            != CURRENT_TENANT_SCHEMA_VERSION
        ):
            raise ValidationError(
                "Tenant database schema is not current."
            )

    # =====================================================
    # REVOKE DEVICE
    # =====================================================

    async def revoke_device(
        self,
        *,
        workspace_id: uuid.UUID,
        device_id: uuid.UUID,
        device_uuid: uuid.UUID,
    ) -> DeviceDeleteResponse:
        """
        Revoke a device across tenant and control planes.

        Required caller inputs:

            workspace_id
            tenant-local device_id
            global device_uuid

        All three identities are cross-checked before completing
        the lifecycle transition.
        """

        registry = (
            await self._require_ready_registry(
                workspace_id=workspace_id
            )
        )

        trusted_database_name = (
            validate_tenant_database_name(
                registry.database_name
            )
        )

        trusted_cluster_key = (
            validate_tenant_cluster_key(
                registry.cluster_key
            )
        )

        # -------------------------------------------------
        # RESOLVE CONTROL ROUTE
        # -------------------------------------------------

        route = (
            await self.routing_service.resolve_device_route(
                device_uuid=device_uuid
            )
        )

        if (
            route.workspace_id
            != workspace_id
        ):
            raise ResourceNotFound(
                "Device not found."
            )

        if (
            route.tenant_device_id
            != device_id
        ):
            raise ResourceNotFound(
                "Device not found."
            )

        # -------------------------------------------------
        # REVOKE TENANT DEVICE + CREDENTIALS
        # -------------------------------------------------

        async with tenant_session(
            trusted_database_name,
            cluster_key=trusted_cluster_key,
        ) as tenant_db_session:

            await self._verify_tenant_identity(
                tenant_db_session,
                workspace_id=workspace_id,
            )

            device_service = DeviceService(
                tenant_db_session
            )

            device = (
                await device_service.get_device(
                    device_id=device_id
                )
            )

            if (
                device.device.device_uuid
                != device_uuid
            ):
                raise ResourceNotFound(
                    "Device not found."
                )

            tenant_result = (
                await device_service.revoke_device(
                    device_id=device_id
                )
            )

        # -------------------------------------------------
        # REVOKE CONTROL ROUTE
        # -------------------------------------------------

        try:
            await self.routing_service.revoke_route(
                device_uuid=device_uuid
            )

        except Exception:
            """
            Tenant revocation has already succeeded.

            Do not reactivate the tenant device automatically.

            A later reconciliation pass can detect active control
            routes whose tenant devices are already revoked.
            """

            raise

        return tenant_result


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceManagementService",
]