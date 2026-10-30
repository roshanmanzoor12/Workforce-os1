from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from alembic.script import ScriptDirectory
from sqlalchemy import text

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
from app.db.tenant_models import (
    TenantMetadata,
)
from app.modules.devices.credential_schemas import (
    DeviceAuthenticationRequest,
)
from app.modules.devices.credential_service import (
    DeviceCredentialService,
)
from app.modules.devices.routing_service import (
    DeviceRoutingService,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
)


# =========================================================
# AUTHENTICATED DEVICE CONTEXT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class AuthenticatedDeviceContext:
    """
    Trusted server-side device authentication result.

    This object is internal and must not be serialized directly
    to the endpoint agent.
    """

    workspace_id: uuid.UUID

    device_id: uuid.UUID

    device_uuid: uuid.UUID

    credential_id: uuid.UUID

    credential_version: int

    database_name: str

    cluster_key: str


# =========================================================
# DEVICE AUTH SERVICE
# =========================================================


class DeviceAuthService:
    """
    Cross-plane authentication service for registered agents.

    Authentication flow:

        device_uuid
            ↓
        control DeviceRoute
            ↓
        trusted workspace_id
            ↓
        control TenantDatabaseRegistry
            ↓
        trusted tenant DB
            ↓
        TenantMetadata identity verification
            ↓
        DeviceCredential authentication
            ↓
        tenant Device validation
            ↓
        AuthenticatedDeviceContext

    The agent never selects the tenant database.
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
        result = await self.control_session.execute(
            select(
                TenantDatabaseRegistry
            ).where(
                TenantDatabaseRegistry.workspace_id
                == workspace_id
            )
        )

        registry = (
            result.scalar_one_or_none()
        )

        if registry is None:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if (
            registry.status
            != TENANT_STATUS_READY
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        database_name = (
            validate_tenant_database_name(
                registry.database_name
            )
        )

        cluster_key = (
            validate_tenant_cluster_key(
                registry.cluster_key
            )
        )

        if not database_name:
            raise ValidationError(
                "Tenant database name is invalid."
            )

        if not cluster_key:
            raise ValidationError(
                "Tenant cluster key is invalid."
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
        result = await tenant_db_session.execute(
            select(
                TenantMetadata
            )
        )

        metadata_rows = list(
            result.scalars().all()
        )

        if len(metadata_rows) != 1:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        metadata = metadata_rows[0]

        if (
            metadata.workspace_id
            != workspace_id
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )

        if not metadata.is_active:
            raise ResourceNotFound(
                "Device authentication failed."
            )

        # Require a REAL applied Alembic revision at or beyond the
        # minimum supported revision; do not trust stale metadata alone.
        # A separate check confirms that metadata is an ancestor of the
        # database's recorded migration revision (no fabricated version).
        try:
            version_result = await tenant_db_session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            applied = list(version_result.scalars().all())
            if len(applied) != 1:
                raise ValueError("Unexpected Alembic revision count")

            backend_dir = Path(__file__).resolve().parents[3]
            migrations_dir = backend_dir / "migrations" / "tenant"
            graph = ScriptDirectory(str(migrations_dir))
            database_revision = applied[0]
            if graph.get_revision(database_revision) is None:
                raise ValueError("Unknown applied Alembic revision")
            if graph.get_revision(CURRENT_TENANT_SCHEMA_VERSION) is None:
                raise ValueError("Unknown required Alembic revision")

            ancestors = {
                node.revision
                for node in graph.iterate_revisions(
                    database_revision, "base"
                )
            }
            if CURRENT_TENANT_SCHEMA_VERSION not in ancestors:
                raise ValueError("Required migration not applied")
            if metadata.schema_version not in ancestors:
                raise ValueError("Tenant metadata revision is not an ancestor")
        except Exception as exc:
            # Preserve generic error at the public authentication boundary.
            raise ResourceNotFound(
                "Device authentication failed."
            ) from exc

    # =====================================================
    # AUTHENTICATE
    # =====================================================

    async def authenticate_device(
        self,
        payload: DeviceAuthenticationRequest,
    ) -> AuthenticatedDeviceContext:
        """
        Authenticate one registered endpoint agent.
        """

        # -------------------------------------------------
        # 1. Resolve global control-plane route
        # -------------------------------------------------

        route = (
            await self.routing_service.resolve_device_route(
                device_uuid=payload.device_uuid
            )
        )

        # -------------------------------------------------
        # 2. Resolve trusted tenant registry
        # -------------------------------------------------

        registry = (
            await self._require_ready_registry(
                workspace_id=route.workspace_id
            )
        )

        database_name = (
            validate_tenant_database_name(
                registry.database_name
            )
        )

        cluster_key = (
            validate_tenant_cluster_key(
                registry.cluster_key
            )
        )

        # -------------------------------------------------
        # 3. Open trusted tenant database
        # -------------------------------------------------

        async with tenant_session(
            database_name,
            cluster_key=cluster_key,
        ) as tenant_db_session:

            # ---------------------------------------------
            # 4. Verify physical tenant identity
            # ---------------------------------------------

            await self._verify_tenant_identity(
                tenant_db_session,
                workspace_id=route.workspace_id,
            )

            # ---------------------------------------------
            # 5. Authenticate secret
            # ---------------------------------------------

            credential_service = (
                DeviceCredentialService(
                    tenant_db_session
                )
            )

            authenticated = (
                await credential_service.authenticate_device(
                    payload
                )
            )

            # ---------------------------------------------
            # 6. Cross-check route -> tenant identity
            # ---------------------------------------------

            if (
                authenticated.device_id
                != route.tenant_device_id
            ):
                raise ResourceNotFound(
                    "Device authentication failed."
                )

            if (
                authenticated.device_uuid
                != route.device_uuid
            ):
                raise ResourceNotFound(
                    "Device authentication failed."
                )

            # ---------------------------------------------
            # 7. Return trusted internal context
            # ---------------------------------------------

            return AuthenticatedDeviceContext(
                workspace_id=route.workspace_id,
                device_id=authenticated.device_id,
                device_uuid=authenticated.device_uuid,
                credential_id=authenticated.credential_id,
                credential_version=(
                    authenticated.credential_version
                ),
                database_name=database_name,
                cluster_key=cluster_key,
            )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "AuthenticatedDeviceContext",
    "DeviceAuthService",
]