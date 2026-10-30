from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
)
from app.modules.devices.activation_models import (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXHAUSTED,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_REVOKED,
)
from app.modules.devices.activation_schemas import (
    DeviceActivationCodeCreateRequest,
)
from app.modules.devices.activation_service import (
    DeviceActivationService,
)


# =========================================================
# CONSTANTS
# =========================================================

VALID_ACTIVATION_CODE = (
    "wfdev_test_activation_code_123456789"
)

SECOND_ACTIVATION_CODE = (
    "wfdev_another_activation_code_987654321"
)


# =========================================================
# HELPERS
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def hash_code(
    value: str,
) -> str:
    return hashlib.sha256(
        value.encode(
            "utf-8"
        )
    ).hexdigest()


def build_activation(
    *,
    activation_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    created_by_user_id: uuid.UUID | None = None,
    code_hash: str | None = None,
    status: str = ACTIVATION_STATUS_ACTIVE,
    is_active: bool = True,
    expires_at: datetime | None = None,
    revoked_at: datetime | None = None,
    last_used_at: datetime | None = None,
    max_uses: int = 1,
    used_count: int = 0,
    label: str | None = "Test activation",
):
    now = utc_now()

    return SimpleNamespace(
        id=activation_id or uuid.uuid4(),
        workspace_id=workspace_id or uuid.uuid4(),
        created_by_user_id=(
            created_by_user_id
            or uuid.uuid4()
        ),
        code_hash=(
            code_hash
            or hash_code(
                VALID_ACTIVATION_CODE
            )
        ),
        code_prefix="wfdev_test",
        status=status,
        is_active=is_active,
        expires_at=expires_at,
        revoked_at=revoked_at,
        last_used_at=last_used_at,
        max_uses=max_uses,
        used_count=used_count,
        label=label,
        created_at=now,
        updated_at=now,
    )


# =========================================================
# MOCK MUTATION HELPERS
# =========================================================


async def increment_usage_side_effect(
    activation,
    *,
    used_at: datetime,
):
    activation.used_count += 1
    activation.last_used_at = used_at

    return activation


async def mark_exhausted_side_effect(
    activation,
    *,
    exhausted_status: str,
):
    activation.status = exhausted_status
    activation.is_active = False

    return activation


async def mark_expired_side_effect(
    activation,
    *,
    expired_status: str,
):
    activation.status = expired_status
    activation.is_active = False

    return activation


# =========================================================
# HASH CONTRACT
# =========================================================


def test_activation_code_hash_is_deterministic() -> None:
    digest_one = (
        DeviceActivationService.hash_activation_code(
            VALID_ACTIVATION_CODE
        )
    )

    digest_two = (
        DeviceActivationService.hash_activation_code(
            VALID_ACTIVATION_CODE
        )
    )

    assert digest_one == digest_two

    assert digest_one == hash_code(
        VALID_ACTIVATION_CODE
    )

    assert (
        digest_one
        != VALID_ACTIVATION_CODE
    )


def test_different_activation_codes_produce_different_hashes() -> None:
    first = (
        DeviceActivationService.hash_activation_code(
            VALID_ACTIVATION_CODE
        )
    )

    second = (
        DeviceActivationService.hash_activation_code(
            SECOND_ACTIVATION_CODE
        )
    )

    assert first != second


# =========================================================
# CREATE REQUEST CONTRACT
# =========================================================


def test_activation_create_request_accepts_valid_values() -> None:
    expires_at = (
        utc_now()
        + timedelta(
            days=7
        )
    )

    payload = DeviceActivationCodeCreateRequest(
        label="Windows deployment",
        expires_at=expires_at,
        max_uses=10,
    )

    assert payload.label == "Windows deployment"
    assert payload.expires_at == expires_at
    assert payload.max_uses == 10


def test_activation_create_request_rejects_invalid_max_uses() -> None:
    with pytest.raises(
        Exception
    ):
        DeviceActivationCodeCreateRequest(
            label="Invalid",
            max_uses=0,
        )


# =========================================================
# RESOLVE UNKNOWN CODE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_activation_code_rejects_unknown_code() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    service.repository.get_by_hash = AsyncMock(
        return_value=None
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.resolve_activation_code(
            VALID_ACTIVATION_CODE
        )

    expected_hash = (
        DeviceActivationService.hash_activation_code(
            VALID_ACTIVATION_CODE
        )
    )

    service.repository.get_by_hash.assert_awaited_once_with(
        expected_hash
    )


# =========================================================
# RESOLVE REVOKED CODE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_activation_code_rejects_revoked_code() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    activation = build_activation(
        status=ACTIVATION_STATUS_REVOKED,
        is_active=False,
        revoked_at=utc_now(),
    )

    service.repository.get_by_hash = AsyncMock(
        return_value=activation
    )

    with pytest.raises(
        ValidationError
    ):
        await service.resolve_activation_code(
            VALID_ACTIVATION_CODE
        )


# =========================================================
# RESOLVE EXPIRED CODE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_activation_code_rejects_expired_code() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    activation = build_activation(
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        expires_at=(
            utc_now()
            - timedelta(
                minutes=1
            )
        ),
    )

    service.repository.get_by_hash = AsyncMock(
        return_value=activation
    )

    service.repository.mark_expired = AsyncMock(
        side_effect=mark_expired_side_effect
    )

    with pytest.raises(
        ValidationError
    ):
        await service.resolve_activation_code(
            VALID_ACTIVATION_CODE
        )

    service.repository.mark_expired.assert_awaited_once()

    assert (
        activation.status
        == ACTIVATION_STATUS_EXPIRED
    )

    assert activation.is_active is False

    session.commit.assert_awaited_once()


# =========================================================
# RESOLVE EXHAUSTED CODE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_activation_code_rejects_exhausted_code() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    activation = build_activation(
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        max_uses=1,
        used_count=1,
    )

    service.repository.get_by_hash = AsyncMock(
        return_value=activation
    )

    service.repository.mark_exhausted = AsyncMock(
        side_effect=mark_exhausted_side_effect
    )

    with pytest.raises(
        ValidationError
    ):
        await service.resolve_activation_code(
            VALID_ACTIVATION_CODE
        )

    service.repository.mark_exhausted.assert_awaited_once()

    assert (
        activation.status
        == ACTIVATION_STATUS_EXHAUSTED
    )

    assert activation.is_active is False

    session.commit.assert_awaited_once()


# =========================================================
# RESOLVE VALID CODE
# =========================================================


@pytest.mark.asyncio
async def test_resolve_activation_code_returns_trusted_workspace() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        max_uses=5,
        used_count=1,
        expires_at=(
            utc_now()
            + timedelta(
                hours=1
            )
        ),
    )

    service.repository.get_by_hash = AsyncMock(
        return_value=activation
    )

    result = await service.resolve_activation_code(
        VALID_ACTIVATION_CODE
    )

    assert (
        result.workspace_id
        == workspace_id
    )

    assert (
        result.activation_id
        == activation.id
    )

    assert (
        result.status
        == ACTIVATION_STATUS_ACTIVE
    )

    assert result.used_count == 1
    assert result.max_uses == 5

    session.commit.assert_not_awaited()


# =========================================================
# CONSUME NORMAL USE
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_increments_usage() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        max_uses=5,
        used_count=1,
    )

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=activation
        )
    )

    service.repository.increment_usage = AsyncMock(
        side_effect=increment_usage_side_effect
    )

    service.repository.mark_exhausted = AsyncMock(
        side_effect=mark_exhausted_side_effect
    )

    result = await service.consume_activation_code(
        activation_id=activation.id,
        workspace_id=workspace_id,
    )

    service.repository.get_workspace_activation_for_update.assert_awaited_once_with(
        workspace_id=workspace_id,
        activation_id=activation.id,
    )

    service.repository.increment_usage.assert_awaited_once()

    service.repository.mark_exhausted.assert_not_awaited()

    assert activation.used_count == 2

    assert (
        result.used_count
        == 2
    )

    assert (
        result.status
        == ACTIVATION_STATUS_ACTIVE
    )

    session.commit.assert_awaited_once()

    session.refresh.assert_awaited_once_with(
        activation
    )


# =========================================================
# FINAL USE -> EXHAUSTED
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_marks_final_use_exhausted() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        max_uses=2,
        used_count=1,
    )

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=activation
        )
    )

    service.repository.increment_usage = AsyncMock(
        side_effect=increment_usage_side_effect
    )

    service.repository.mark_exhausted = AsyncMock(
        side_effect=mark_exhausted_side_effect
    )

    result = await service.consume_activation_code(
        activation_id=activation.id,
        workspace_id=workspace_id,
    )

    service.repository.increment_usage.assert_awaited_once()

    service.repository.mark_exhausted.assert_awaited_once()

    assert activation.used_count == 2

    assert (
        activation.status
        == ACTIVATION_STATUS_EXHAUSTED
    )

    assert activation.is_active is False

    assert (
        result.status
        == ACTIVATION_STATUS_EXHAUSTED
    )

    assert (
        result.used_count
        == 2
    )

    session.commit.assert_awaited_once()

    session.refresh.assert_awaited_once_with(
        activation
    )


# =========================================================
# MISSING ACTIVATION
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_rejects_missing_activation() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    activation_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=None
        )
    )

    with pytest.raises(
        ResourceNotFound
    ):
        await service.consume_activation_code(
            activation_id=activation_id,
            workspace_id=workspace_id,
        )

    service.repository.get_workspace_activation_for_update.assert_awaited_once_with(
        workspace_id=workspace_id,
        activation_id=activation_id,
    )


# =========================================================
# CONSUME REVOKED
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_rejects_revoked_activation() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_REVOKED,
        is_active=False,
        revoked_at=utc_now(),
    )

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=activation
        )
    )

    with pytest.raises(
        ValidationError
    ):
        await service.consume_activation_code(
            activation_id=activation.id,
            workspace_id=workspace_id,
        )

    session.rollback.assert_awaited_once()

    session.commit.assert_not_awaited()


# =========================================================
# CONSUME ALREADY EXHAUSTED
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_rejects_exhausted_activation() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_EXHAUSTED,
        is_active=False,
        max_uses=1,
        used_count=1,
    )

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=activation
        )
    )

    with pytest.raises(
        ValidationError
    ):
        await service.consume_activation_code(
            activation_id=activation.id,
            workspace_id=workspace_id,
        )

    session.rollback.assert_awaited_once()

    session.commit.assert_not_awaited()


# =========================================================
# LIMIT REACHED WHILE STILL MARKED ACTIVE
# =========================================================


@pytest.mark.asyncio
async def test_consume_activation_code_synchronizes_usage_limit() -> None:
    session = AsyncMock()

    service = DeviceActivationService(
        session
    )

    workspace_id = uuid.uuid4()

    activation = build_activation(
        workspace_id=workspace_id,
        status=ACTIVATION_STATUS_ACTIVE,
        is_active=True,
        max_uses=1,
        used_count=1,
    )

    service.repository.get_workspace_activation_for_update = (
        AsyncMock(
            return_value=activation
        )
    )

    service.repository.mark_exhausted = AsyncMock(
        side_effect=mark_exhausted_side_effect
    )

    service.repository.increment_usage = AsyncMock(
        side_effect=increment_usage_side_effect
    )

    with pytest.raises(
        ValidationError
    ):
        await service.consume_activation_code(
            activation_id=activation.id,
            workspace_id=workspace_id,
        )

    service.repository.mark_exhausted.assert_awaited_once()

    service.repository.increment_usage.assert_not_awaited()

    assert (
        activation.status
        == ACTIVATION_STATUS_EXHAUSTED
    )

    assert activation.is_active is False

    session.commit.assert_awaited_once()


# =========================================================
# STATUS CONSTANTS
# =========================================================


def test_activation_status_constants_are_distinct() -> None:
    statuses = {
        ACTIVATION_STATUS_ACTIVE,
        ACTIVATION_STATUS_EXPIRED,
        ACTIVATION_STATUS_REVOKED,
        ACTIVATION_STATUS_EXHAUSTED,
    }

    assert len(
        statuses
    ) == 4


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "VALID_ACTIVATION_CODE",
    "SECOND_ACTIVATION_CODE",
    "utc_now",
    "hash_code",
    "build_activation",
    "increment_usage_side_effect",
    "mark_exhausted_side_effect",
    "mark_expired_side_effect",
]