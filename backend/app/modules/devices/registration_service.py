from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
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
from app.modules.devices.activation_service import (
    DeviceActivationService,
)
from app.modules.devices.credential_schemas import (
    DeviceRegistrationCredential,
)
from app.modules.devices.credential_service import (
    DeviceCredentialService,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
)
from app.modules.devices.repository import (
    DeviceRepository,
)
from app.modules.devices.routing_service import (
    DeviceRoutingService,
)
from app.modules.devices.schemas import (
    DevicePublic,
    DeviceRegistrationRequest,
    DeviceRegistrationResponse,
)
from app.modules.devices.service import (
    DeviceService,
)
from app.modules.workspaces.models import (
    TENANT_STATUS_READY,
    TenantDatabaseRegistry,
    Workspace,
)


# =========================================================
# CONSTANTS
# =========================================================

WORKSPACE_READY_STATUS = "ready"


# =========================================================
# REGISTRATION SERVICE
# =========================================================


class DeviceRegistrationService:
    """
    Complete cross-plane endpoint enrollment orchestrator.

    Enrollment flow:

        activation_code
            ↓
        control-plane activation lookup
            ↓
        trusted workspace_id
            ↓
        trusted TenantDatabaseRegistry
            ↓
        physical tenant identity verification
            ↓
        tenant Device
            ↓
        tenant DeviceCredential
            ↓
        control DeviceRoute
            ↓
        consume activation-code use
            ↓
        return device_uuid + device_secret once

    The endpoint agent never supplies:

        workspace_id
        tenant database name
        database URL
        cluster key
        trusted device_uuid
    """

    def __init__(
        self,
        control_session: AsyncSession,
    ) -> None:
        self.control_session = (
            control_session
        )

        self.activation_service = (
            DeviceActivationService(
                control_session
            )
        )

        self.routing_service = (
            DeviceRoutingService(
                control_session
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
    # WORKSPACE
    # =====================================================

    async def _require_ready_workspace(
        self,
        workspace_id: uuid.UUID,
    ) -> Workspace:
        result = (
            await self.control_session.execute(
                select(
                    Workspace
                ).where(
                    Workspace.id
                    == workspace_id
                )
            )
        )

        workspace = (
            result.scalar_one_or_none()
        )

        if workspace is None:
            raise ResourceNotFound(
                "Device registration target is unavailable."
            )

        if (
            workspace.status
            != WORKSPACE_READY_STATUS
        ):
            raise ValidationError(
                "Workspace is not ready "
                "for device registration."
            )

        if not workspace.is_active:
            raise ValidationError(
                "Workspace is not active."
            )

        return workspace

    # =====================================================
    # TENANT REGISTRY
    # =====================================================

    async def _require_ready_registry(
        self,
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
                "Device registration target is unavailable."
            )

        if (
            registry.status
            != TENANT_STATUS_READY
        ):
            raise ValidationError(
                "Workspace tenant is not ready "
                "for device registration."
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
    ) -> TenantMetadata:
        """
        Verify the physical tenant database actually belongs to
        the workspace resolved from the activation code.
        """

        result = (
            await tenant_db_session.execute(
                select(
                    TenantMetadata
                )
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
                "Tenant database workspace identity "
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

        return metadata

    # =====================================================
    # TENANT DEVICE CREATION
    # =====================================================

    async def _create_device(
        self,
        tenant_db_session: AsyncSession,
        payload: DeviceRegistrationRequest,
    ):
        repository = DeviceRepository(
            tenant_db_session
        )

        if payload.agent_identifier is not None:
            existing = (
                await repository.get_device_by_agent_identifier(
                    payload.agent_identifier
                )
            )

            if existing is not None:
                raise ConflictError(
                    "A device with this agent identifier "
                    "is already registered."
                )

        now = self._now()

        device_uuid = uuid.uuid4()

        try:
            device = (
                await repository.create_device(
                    device_uuid=device_uuid,
                    employee_id=None,
                    hostname=payload.hostname,
                    os_name=payload.os_name,
                    os_version=payload.os_version,
                    architecture=payload.architecture,
                    agent_version=payload.agent_version,
                    agent_identifier=payload.agent_identifier,
                    status=DEVICE_STATUS_ACTIVE,
                    is_active=True,
                    first_seen_at=now,
                    last_seen_at=now,
                    registered_at=now,
                    monitoring_profile_id=None,
                )
            )

            await tenant_db_session.commit()

            await tenant_db_session.refresh(
                device
            )

            return device

        except IntegrityError as exc:
            await tenant_db_session.rollback()

            raise ConflictError(
                "Device registration conflicts with "
                "an existing device."
            ) from exc

    # =====================================================
    # TENANT COMPENSATION
    # =====================================================

    @staticmethod
    async def _revoke_tenant_registration(
        tenant_db_session: AsyncSession,
        *,
        device_id: uuid.UUID,
    ) -> None:
        """
        Best-effort compensation when a later control-plane step
        fails after tenant-side registration has already committed.
        """

        credential_service = (
            DeviceCredentialService(
                tenant_db_session
            )
        )

        device_service = (
            DeviceService(
                tenant_db_session
            )
        )

        try:
            await credential_service.revoke_all_device_credentials(
                device_id=device_id
            )
        except Exception:
            pass

        try:
            await device_service.revoke_device(
                device_id=device_id
            )
        except Exception:
            pass

    # =====================================================
    # REGISTER DEVICE
    # =====================================================

    async def register_device(
        self,
        payload: DeviceRegistrationRequest,
    ) -> DeviceRegistrationResponse:
        from app.core.database import control_transaction
        from app.modules.auth.models import User
        from app.modules.billing.workspace_billing import (
            require_device_capacity,
            workspace_account,
        )

        activation = await self.activation_service.resolve_activation_code(
            payload.activation_code
        )

        # A separate control transaction holds the account lock while the
        # existing enrollment flow commits its tenant/control records.
        async with control_transaction() as billing_db:
            owner_id = await workspace_account(billing_db, activation.workspace_id)
            await billing_db.execute(
                select(User.id).where(User.id == owner_id).with_for_update()
            )
            await require_device_capacity(billing_db, activation.workspace_id)
            return await self._register_device_with_capacity(payload)

    async def _register_device_with_capacity(
        self,
        payload: DeviceRegistrationRequest,
    ) -> DeviceRegistrationResponse:
        """
        Complete first-time endpoint enrollment.
        """

        # -------------------------------------------------
        # 1. Resolve activation code
        # -------------------------------------------------

        resolved_activation = (
            await self.activation_service.resolve_activation_code(
                payload.activation_code
            )
        )

        workspace_id = (
            resolved_activation.workspace_id
        )

        # -------------------------------------------------
        # 2. Validate workspace
        # -------------------------------------------------

        await self._require_ready_workspace(
            workspace_id
        )

        # -------------------------------------------------
        # 3. Resolve trusted tenant
        # -------------------------------------------------

        registry = (
            await self._require_ready_registry(
                workspace_id
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
        # 4. Open trusted tenant DB
        # -------------------------------------------------

        async with tenant_session(
            trusted_database_name,
            cluster_key=trusted_cluster_key,
        ) as tenant_db_session:

            # ---------------------------------------------
            # 5. Verify physical tenant identity
            # ---------------------------------------------

            await self._verify_tenant_identity(
                tenant_db_session,
                workspace_id=workspace_id,
            )

            # ---------------------------------------------
            # 6. Create Device
            # ---------------------------------------------

            device = await self._create_device(
                tenant_db_session,
                payload,
            )

            # ---------------------------------------------
            # 7. Issue initial device credential
            # ---------------------------------------------

            credential_service = (
                DeviceCredentialService(
                    tenant_db_session
                )
            )

            try:
                issued_credential = (
                    await credential_service.issue_initial_credential(
                        device_id=device.id
                    )
                )

            except Exception:
                await self._revoke_tenant_registration(
                    tenant_db_session,
                    device_id=device.id,
                )

                raise

            # ---------------------------------------------
            # 8. Create global device route
            # ---------------------------------------------

            try:
                await self.routing_service.create_route(
                    workspace_id=workspace_id,
                    device_uuid=device.device_uuid,
                    tenant_device_id=device.id,
                )

            except Exception:
                await self._revoke_tenant_registration(
                    tenant_db_session,
                    device_id=device.id,
                )

                raise

            # ---------------------------------------------
            # 9. Consume activation code
            # ---------------------------------------------

            try:
                await self.activation_service.consume_activation_code(
                    activation_id=(
                        resolved_activation.activation_id
                    ),
                    workspace_id=workspace_id,
                )

            except Exception:
                # Revoke the control route first.

                try:
                    await self.routing_service.revoke_route(
                        device_uuid=device.device_uuid
                    )
                except Exception:
                    pass

                # Then revoke tenant credential/device.

                await self._revoke_tenant_registration(
                    tenant_db_session,
                    device_id=device.id,
                )

                raise

            # ---------------------------------------------
            # 10. Return one-time credential
            # ---------------------------------------------

            return DeviceRegistrationResponse(
                message="Device registered.",
                device=DevicePublic.model_validate(
                    device
                ),
                credential=DeviceRegistrationCredential(
                    device_uuid=device.device_uuid,
                    device_secret=(
                        issued_credential.device_secret
                    ),
                ),
            )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "WORKSPACE_READY_STATUS",
    "DeviceRegistrationService",
]
