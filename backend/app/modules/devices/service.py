from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.credential_models import (
    DEVICE_CREDENTIAL_STATUS_REVOKED,
)
from app.modules.devices.credential_repository import (
    DeviceCredentialRepository,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
    DEVICE_STATUS_DISABLED,
    DEVICE_STATUS_OFFLINE,
    DEVICE_STATUS_PENDING,
    DEVICE_STATUS_REVOKED,
    DEVICE_STATUSES,
    Device,
)
from app.modules.devices.repository import (
    DeviceRepository,
)
from app.modules.devices.schemas import (
    DeviceAgentMetadataRequest,
    DeviceAssignmentRequest,
    DeviceDeleteResponse,
    DeviceDetailResponse,
    DeviceListResponse,
    DevicePublic,
    DeviceRegistrationRequest,
    DeviceResponse,
    DeviceStatusResponse,
    DeviceUpdateRequest,
)


class DeviceService:
    """
    Tenant-local business service for registered devices.

    Responsibilities:

    - tenant device creation
    - device inventory
    - employee assignment
    - administrative metadata/lifecycle updates
    - agent metadata updates
    - tenant-side device revocation
    - tenant credential revocation when a device is revoked

    Important:

    Final public enrollment orchestration does NOT live here.

    DeviceRegistrationService coordinates:

        activation
        tenant Device
        tenant DeviceCredential
        control DeviceRoute
        activation consumption
        final one-time registration response
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = DeviceRepository(
            session
        )

        self.credential_repository = (
            DeviceCredentialRepository(
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
    # MAPPERS
    # =====================================================

    @staticmethod
    def _to_public(
        device: Device,
    ) -> DevicePublic:
        return DevicePublic.model_validate(
            device
        )

    # =====================================================
    # INTERNAL LOOKUPS
    # =====================================================

    async def _require_device(
        self,
        device_id: uuid.UUID,
    ) -> Device:
        device = (
            await self.repository.get_device_by_id(
                device_id
            )
        )

        if device is None:
            raise ResourceNotFound(
                "Device not found."
            )

        return device

    async def _require_device_by_uuid(
        self,
        device_uuid: uuid.UUID,
    ) -> Device:
        device = (
            await self.repository.get_device_by_uuid(
                device_uuid
            )
        )

        if device is None:
            raise ResourceNotFound(
                "Device not found."
            )

        return device

    # =====================================================
    # EMPLOYEE VALIDATION
    # =====================================================

    async def _validate_employee_assignment(
        self,
        employee_id: uuid.UUID | None,
    ) -> None:
        if employee_id is None:
            return

        employee = (
            await self.repository.get_active_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise ValidationError(
                "Assigned employee must exist and be active."
            )

    # =====================================================
    # AGENT IDENTIFIER
    # =====================================================

    async def _validate_agent_identifier_unique(
        self,
        agent_identifier: str | None,
        *,
        exclude_device_id: uuid.UUID | None = None,
    ) -> None:
        if agent_identifier is None:
            return

        exists = (
            await self.repository.agent_identifier_exists(
                agent_identifier,
                exclude_device_id=exclude_device_id,
            )
        )

        if exists:
            raise ConflictError(
                "A device with this agent identifier "
                "is already registered."
            )

    # =====================================================
    # STATUS VALIDATION
    # =====================================================

    @staticmethod
    def _validate_status(
        status: str,
    ) -> None:
        if status not in DEVICE_STATUSES:
            raise ValidationError(
                "Invalid device status."
            )

    # =====================================================
    # TENANT-LOCAL DEVICE CREATION
    # =====================================================

    async def register_device(
        self,
        payload: DeviceRegistrationRequest,
    ) -> DeviceResponse:
        """
        Create only the tenant-local Device row.

        This method does NOT:

        - resolve activation codes
        - create DeviceRoute
        - issue the final registration response
        - consume activation usage

        Public endpoint enrollment must use
        DeviceRegistrationService instead.
        """

        await self._validate_agent_identifier_unique(
            payload.agent_identifier
        )

        now = self._now()

        device = (
            await self.repository.create_device(
                device_uuid=uuid.uuid4(),
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

        await self.session.commit()

        await self.session.refresh(
            device
        )

        return DeviceResponse(
            message="Device registered.",
            device=self._to_public(
                device
            ),
        )

    # =====================================================
    # GET DEVICE
    # =====================================================

    async def get_device(
        self,
        *,
        device_id: uuid.UUID,
    ) -> DeviceDetailResponse:
        device = await self._require_device(
            device_id
        )

        return DeviceDetailResponse(
            device=self._to_public(
                device
            )
        )

    async def get_device_by_uuid(
        self,
        *,
        device_uuid: uuid.UUID,
    ) -> DeviceDetailResponse:
        device = await self._require_device_by_uuid(
            device_uuid
        )

        return DeviceDetailResponse(
            device=self._to_public(
                device
            )
        )

    # =====================================================
    # LIST DEVICES
    # =====================================================

    async def list_devices(
        self,
        *,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ) -> DeviceListResponse:
        if status is not None:
            self._validate_status(
                status
            )

        normalized_search = (
            search.strip()
            if search is not None
            else None
        )

        if normalized_search == "":
            normalized_search = None

        devices = (
            await self.repository.list_devices(
                employee_id=employee_id,
                status=status,
                include_inactive=include_inactive,
                search=normalized_search,
            )
        )

        total = (
            await self.repository.count_devices(
                employee_id=employee_id,
                status=status,
                include_inactive=include_inactive,
                search=normalized_search,
            )
        )

        return DeviceListResponse(
            devices=[
                self._to_public(
                    device
                )
                for device in devices
            ],
            total=total,
        )

    # =====================================================
    # ASSIGN / UNASSIGN EMPLOYEE
    # =====================================================

    async def assign_device(
        self,
        payload: DeviceAssignmentRequest,
        *,
        device_id: uuid.UUID,
    ) -> DeviceResponse:
        device = await self._require_device(
            device_id
        )

        if (
            device.status
            == DEVICE_STATUS_REVOKED
        ):
            raise ValidationError(
                "A revoked device cannot be assigned."
            )

        await self._validate_employee_assignment(
            payload.employee_id
        )

        await self.repository.assign_employee(
            device,
            employee_id=payload.employee_id,
        )

        await self.session.commit()

        await self.session.refresh(
            device
        )

        message = (
            "Device unassigned."
            if payload.employee_id is None
            else "Device assigned."
        )

        return DeviceResponse(
            message=message,
            device=self._to_public(
                device
            ),
        )

    # =====================================================
    # ADMIN UPDATE
    # =====================================================

    async def update_device(
        self,
        payload: DeviceUpdateRequest,
        *,
        device_id: uuid.UUID,
    ) -> DeviceResponse:
        device = await self._require_device(
            device_id
        )

        fields_set = (
            payload.model_fields_set
        )

        values: dict[
            str,
            object,
        ] = {}

        # -------------------------------------------------
        # HOSTNAME
        # -------------------------------------------------

        if "hostname" in fields_set:
            if payload.hostname is None:
                raise ValidationError(
                    "Hostname cannot be cleared."
                )

            values[
                "hostname"
            ] = payload.hostname

        # -------------------------------------------------
        # EMPLOYEE
        # -------------------------------------------------

        if "employee_id" in fields_set:
            if (
                device.status
                == DEVICE_STATUS_REVOKED
                and payload.employee_id is not None
            ):
                raise ValidationError(
                    "A revoked device cannot be assigned."
                )

            await self._validate_employee_assignment(
                payload.employee_id
            )

            values[
                "employee_id"
            ] = payload.employee_id

        # -------------------------------------------------
        # MONITORING PROFILE
        # -------------------------------------------------

        if "monitoring_profile_id" in fields_set:
            values[
                "monitoring_profile_id"
            ] = payload.monitoring_profile_id

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        if "status" in fields_set:
            if payload.status is None:
                raise ValidationError(
                    "Device status cannot be cleared."
                )

            self._validate_status(
                payload.status
            )

            if (
                device.status
                == DEVICE_STATUS_REVOKED
                and payload.status
                != DEVICE_STATUS_REVOKED
            ):
                raise ValidationError(
                    "A revoked device cannot be restored."
                )

            values[
                "status"
            ] = payload.status

            if (
                payload.status
                == DEVICE_STATUS_REVOKED
            ):
                values[
                    "is_active"
                ] = False

                values[
                    "revoked_at"
                ] = (
                    device.revoked_at
                    or self._now()
                )

            elif (
                payload.status
                == DEVICE_STATUS_DISABLED
            ):
                values[
                    "is_active"
                ] = False

            elif payload.status in {
                DEVICE_STATUS_PENDING,
                DEVICE_STATUS_ACTIVE,
                DEVICE_STATUS_OFFLINE,
            }:
                if (
                    "is_active"
                    not in fields_set
                ):
                    values[
                        "is_active"
                    ] = True

        # -------------------------------------------------
        # ACTIVE FLAG
        # -------------------------------------------------

        if "is_active" in fields_set:
            if payload.is_active is None:
                raise ValidationError(
                    "Device active state cannot be cleared."
                )

            if (
                device.status
                == DEVICE_STATUS_REVOKED
                and payload.is_active
            ):
                raise ValidationError(
                    "A revoked device cannot be activated."
                )

            if (
                payload.status
                == DEVICE_STATUS_REVOKED
                and payload.is_active
            ):
                raise ValidationError(
                    "A revoked device cannot be active."
                )

            values[
                "is_active"
            ] = payload.is_active

        # -------------------------------------------------
        # NO-OP
        # -------------------------------------------------

        if not fields_set:
            return DeviceResponse(
                message="Device updated.",
                device=self._to_public(
                    device
                ),
            )

        # -------------------------------------------------
        # REVOKE CREDENTIALS IF STATUS BECOMES REVOKED
        # -------------------------------------------------

        if (
            values.get("status")
            == DEVICE_STATUS_REVOKED
        ):
            active_credentials = (
                await self.credential_repository
                .get_active_device_credentials_for_update(
                    device.id
                )
            )

            if active_credentials:
                await self.credential_repository.revoke_credentials(
                    active_credentials,
                    revoked_at=self._now(),
                    revoked_status=(
                        DEVICE_CREDENTIAL_STATUS_REVOKED
                    ),
                )

        await self.repository.update_device(
            device,
            values=values,
        )

        await self.session.commit()

        await self.session.refresh(
            device
        )

        return DeviceResponse(
            message="Device updated.",
            device=self._to_public(
                device
            ),
        )

    # =====================================================
    # AGENT METADATA
    # =====================================================

    async def update_agent_metadata(
        self,
        payload: DeviceAgentMetadataRequest,
        *,
        device_uuid: uuid.UUID,
    ) -> DeviceResponse:
        device = (
            await self._require_device_by_uuid(
                device_uuid
            )
        )

        if (
            device.status
            == DEVICE_STATUS_REVOKED
        ):
            raise ValidationError(
                "Revoked device cannot update agent metadata."
            )

        if not device.is_active:
            raise ValidationError(
                "Inactive device cannot update agent metadata."
            )

        fields_set = (
            payload.model_fields_set
        )

        values: dict[
            str,
            object,
        ] = {}

        allowed_fields = (
            "hostname",
            "os_name",
            "os_version",
            "architecture",
            "agent_version",
            "agent_identifier",
        )

        if (
            "agent_identifier"
            in fields_set
        ):
            await self._validate_agent_identifier_unique(
                payload.agent_identifier,
                exclude_device_id=device.id,
            )

        for field_name in allowed_fields:
            if field_name not in fields_set:
                continue

            value = getattr(
                payload,
                field_name,
            )

            if (
                field_name
                in {
                    "hostname",
                    "os_name",
                }
                and value is None
            ):
                raise ValidationError(
                    f"{field_name} cannot be cleared."
                )

            values[
                field_name
            ] = value

        if values:
            await self.repository.update_device(
                device,
                values=values,
            )

            await self.session.commit()

            await self.session.refresh(
                device
            )

        return DeviceResponse(
            message="Device metadata updated.",
            device=self._to_public(
                device
            ),
        )

    # =====================================================
    # REVOKE DEVICE
    # =====================================================

    async def revoke_device(
        self,
        *,
        device_id: uuid.UUID,
    ) -> DeviceDeleteResponse:
        """
        Revoke tenant device and all currently active credentials.

        Both changes occur before one tenant DB commit.

        Control-plane DeviceRoute revocation is intentionally NOT
        handled here because this service has no control DB session.
        """

        device = await self._require_device(
            device_id
        )

        if (
            device.status
            == DEVICE_STATUS_REVOKED
        ):
            # Ensure no active credential survives even if an older
            # inconsistent state exists.

            active_credentials = (
                await self.credential_repository
                .get_active_device_credentials_for_update(
                    device.id
                )
            )

            if active_credentials:
                await self.credential_repository.revoke_credentials(
                    active_credentials,
                    revoked_at=(
                        device.revoked_at
                        or self._now()
                    ),
                    revoked_status=(
                        DEVICE_CREDENTIAL_STATUS_REVOKED
                    ),
                )

                await self.session.commit()

            return DeviceDeleteResponse(
                message="Device revoked.",
                success=True,
            )

        revoked_at = self._now()

        active_credentials = (
            await self.credential_repository
            .get_active_device_credentials_for_update(
                device.id
            )
        )

        if active_credentials:
            await self.credential_repository.revoke_credentials(
                active_credentials,
                revoked_at=revoked_at,
                revoked_status=(
                    DEVICE_CREDENTIAL_STATUS_REVOKED
                ),
            )

        await self.repository.revoke_device(
            device,
            revoked_at=revoked_at,
            revoked_status=(
                DEVICE_STATUS_REVOKED
            ),
        )

        await self.session.commit()

        return DeviceDeleteResponse(
            message="Device revoked.",
            success=True,
        )

    # =====================================================
    # DEVICE STATUS
    # =====================================================

    async def get_device_status(
        self,
        *,
        device_uuid: uuid.UUID,
    ) -> DeviceStatusResponse:
        device = (
            await self._require_device_by_uuid(
                device_uuid
            )
        )

        return DeviceStatusResponse(
            device_id=device.id,
            device_uuid=device.device_uuid,
            status=device.status,
            is_active=device.is_active,
            last_seen_at=device.last_seen_at,
        )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceService",
]