from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.credential_models import (
    DEVICE_CREDENTIAL_STATUS_ACTIVE,
    DEVICE_CREDENTIAL_STATUS_REVOKED,
)
from app.modules.devices.credential_schemas import (
    DeviceAuthenticationRequest,
    DeviceRegistrationCredential,
)
from app.modules.devices.credential_service import (
    DeviceCredentialService,
)
from app.modules.devices.models import (
    DEVICE_STATUS_ACTIVE,
    DEVICE_STATUS_REVOKED,
)


# =========================================================
# CONSTANTS
# =========================================================

VALID_SECRET = (
    "wfds_test_device_secret_1234567890"
)

NEW_SECRET = (
    "wfds_rotated_device_secret_1234567890"
)


# =========================================================
# HELPERS
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def secret_hash(
    value: str,
) -> str:
    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()


def build_device(
    *,
    device_id: uuid.UUID | None = None,
    device_uuid: uuid.UUID | None = None,
    status: str = DEVICE_STATUS_ACTIVE,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=device_id or uuid.uuid4(),
        device_uuid=device_uuid or uuid.uuid4(),
        status=status,
        is_active=is_active,
    )


def build_credential(
    *,
    credential_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    version: int = 1,
    status: str = DEVICE_CREDENTIAL_STATUS_ACTIVE,
    is_active: bool = True,
    expires_at: datetime | None = None,
):
    now = utc_now()

    return SimpleNamespace(
        id=credential_id or uuid.uuid4(),
        device_id=device_id or uuid.uuid4(),
        secret_hash=secret_hash(
            VALID_SECRET
        ),
        secret_prefix="wfds_test",
        version=version,
        status=status,
        is_active=is_active,
        issued_at=now,
        expires_at=expires_at,
        revoked_at=None,
        last_used_at=None,
        created_at=now,
        updated_at=now,
    )


# =========================================================
# SECRET HASH CONTRACT
# =========================================================


def test_device_secret_hash_is_deterministic() -> None:
    digest_one = (
        DeviceCredentialService.hash_device_secret(
            VALID_SECRET
        )
    )

    digest_two = (
        DeviceCredentialService.hash_device_secret(
            VALID_SECRET
        )
    )

    assert digest_one == digest_two

    assert digest_one == secret_hash(
        VALID_SECRET
    )

    assert digest_one != VALID_SECRET


def test_different_device_secrets_produce_different_hashes() -> None:
    assert (
        DeviceCredentialService.hash_device_secret(
            VALID_SECRET
        )
        != DeviceCredentialService.hash_device_secret(
            NEW_SECRET
        )
    )


# =========================================================
# AUTH PAYLOAD CONTRACT
# =========================================================


def test_authentication_request_accepts_valid_secret() -> None:
    device_uuid = uuid.uuid4()

    payload = DeviceAuthenticationRequest(
        device_uuid=device_uuid,
        device_secret=VALID_SECRET,
    )

    assert (
        payload.device_uuid
        == device_uuid
    )

    assert (
        payload.device_secret
        == VALID_SECRET
    )


def test_authentication_request_rejects_short_secret() -> None:
    with pytest.raises(
        PydanticValidationError
    ):
        DeviceAuthenticationRequest(
            device_uuid=uuid.uuid4(),
            device_secret="short",
        )


# =========================================================
# INITIAL CREDENTIAL
# =========================================================


@pytest.mark.asyncio
async def test_initial_credential_requires_existing_device() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=None
        )
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.issue_initial_credential(
            device_id=uuid.uuid4()
        )


@pytest.mark.asyncio
async def test_initial_credential_rejects_existing_credentials() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device()

    existing_credential = (
        build_credential(
            device_id=device.id
        )
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    service.repository.list_device_credentials = (
        AsyncMock(
            return_value=[
                existing_credential,
            ]
        )
    )

    with pytest.raises(
        ValidationError
    ):
        await service.issue_initial_credential(
            device_id=device.id
        )

    service.repository.list_device_credentials.assert_awaited_once_with(
        device.id,
        include_inactive=True,
    )


# =========================================================
# AUTHENTICATION FAILURE CONTRACTS
# =========================================================


@pytest.mark.asyncio
async def test_authentication_rejects_unknown_secret() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=None
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=uuid.uuid4(),
        device_secret=VALID_SECRET,
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.authenticate_device(
            payload
        )

    expected_hash = (
        DeviceCredentialService.hash_device_secret(
            VALID_SECRET
        )
    )

    service.repository.get_active_by_hash.assert_awaited_once_with(
        expected_hash
    )


@pytest.mark.asyncio
async def test_authentication_rejects_missing_device() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    credential = build_credential()

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=credential
        )
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=None
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=uuid.uuid4(),
        device_secret=VALID_SECRET,
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.authenticate_device(
            payload
        )

    service.device_repository.get_device_by_id.assert_awaited_once_with(
        credential.device_id
    )


@pytest.mark.asyncio
async def test_authentication_rejects_device_uuid_mismatch() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device()

    credential = build_credential(
        device_id=device.id
    )

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=credential
        )
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=uuid.uuid4(),
        device_secret=VALID_SECRET,
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.authenticate_device(
            payload
        )


@pytest.mark.asyncio
async def test_authentication_rejects_revoked_device() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device(
        status=DEVICE_STATUS_REVOKED,
        is_active=False,
    )

    credential = build_credential(
        device_id=device.id
    )

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=credential
        )
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=device.device_uuid,
        device_secret=VALID_SECRET,
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.authenticate_device(
            payload
        )


# =========================================================
# EXPIRED CREDENTIAL
# =========================================================


@pytest.mark.asyncio
async def test_authentication_rejects_expired_credential() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    credential = build_credential(
        expires_at=(
            utc_now()
            - timedelta(
                minutes=1
            )
        ),
    )

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=credential
        )
    )

    service.repository.expire_credential = (
        AsyncMock(
            return_value=credential
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=uuid.uuid4(),
        device_secret=VALID_SECRET,
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.authenticate_device(
            payload
        )

    service.repository.expire_credential.assert_awaited_once_with(
        credential,
        expired_status="expired",
    )

    session.commit.assert_awaited_once()


# =========================================================
# SUCCESSFUL AUTHENTICATION
# =========================================================


@pytest.mark.asyncio
async def test_authentication_returns_trusted_identity() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device()

    credential = build_credential(
        device_id=device.id,
        version=3,
    )

    service.repository.get_active_by_hash = (
        AsyncMock(
            return_value=credential
        )
    )

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    service.repository.mark_used = (
        AsyncMock(
            return_value=credential
        )
    )

    payload = DeviceAuthenticationRequest(
        device_uuid=device.device_uuid,
        device_secret=VALID_SECRET,
    )

    result = await service.authenticate_device(
        payload
    )

    assert (
        result.device_id
        == device.id
    )

    assert (
        result.device_uuid
        == device.device_uuid
    )

    assert (
        result.credential_id
        == credential.id
    )

    assert (
        result.credential_version
        == 3
    )

    service.repository.mark_used.assert_awaited_once()

    mark_used_call = (
        service.repository
        .mark_used
        .await_args
    )

    assert (
        mark_used_call.args[0]
        is credential
    )

    assert isinstance(
        mark_used_call.kwargs["used_at"],
        datetime,
    )

    session.commit.assert_awaited_once()


# =========================================================
# REVOKE ALL
# =========================================================


@pytest.mark.asyncio
async def test_revoke_all_device_credentials_is_idempotent() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device()

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    service.repository.get_active_device_credentials_for_update = (
        AsyncMock(
            return_value=[]
        )
    )

    result = (
        await service.revoke_all_device_credentials(
            device_id=device.id
        )
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_revoke_all_device_credentials_revokes_active_rows() -> None:
    session = AsyncMock()

    service = DeviceCredentialService(
        session
    )

    device = build_device()

    credentials = [
        build_credential(
            device_id=device.id,
            version=1,
        ),
        build_credential(
            device_id=device.id,
            version=2,
        ),
    ]

    service.device_repository.get_device_by_id = (
        AsyncMock(
            return_value=device
        )
    )

    service.repository.get_active_device_credentials_for_update = (
        AsyncMock(
            return_value=credentials
        )
    )

    service.repository.revoke_credentials = (
        AsyncMock()
    )

    result = (
        await service.revoke_all_device_credentials(
            device_id=device.id
        )
    )

    assert result.success is True

    service.repository.revoke_credentials.assert_awaited_once()

    revoke_call = (
        service.repository
        .revoke_credentials
        .await_args
    )

    assert (
        revoke_call.args[0]
        == credentials
    )

    assert isinstance(
        revoke_call.kwargs["revoked_at"],
        datetime,
    )

    assert (
        revoke_call.kwargs["revoked_status"]
        == DEVICE_CREDENTIAL_STATUS_REVOKED
    )

    session.commit.assert_awaited_once()


# =========================================================
# SECURITY CONTRACT
# =========================================================


def test_registration_credential_does_not_expose_secret_hash() -> None:
    credential = DeviceRegistrationCredential(
        device_uuid=uuid.uuid4(),
        device_secret=VALID_SECRET,
    )

    serialized = (
        credential.model_dump()
    )

    assert (
        "secret_hash"
        not in serialized
    )

    assert (
        "credential_id"
        not in serialized
    )

    assert (
        serialized["device_secret"]
        == VALID_SECRET
    )


# =========================================================
# MODEL STATUS CONTRACT
# =========================================================


def test_credential_status_constants_are_distinct() -> None:
    assert (
        DEVICE_CREDENTIAL_STATUS_ACTIVE
        != DEVICE_CREDENTIAL_STATUS_REVOKED
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "VALID_SECRET",
    "NEW_SECRET",
    "utc_now",
    "secret_hash",
    "build_device",
    "build_credential",
]