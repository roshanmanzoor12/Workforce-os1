from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.modules.api_keys.audit_delivery import (
    APIKeyAuditDelivery,
    APIKeyAuditDeliveryError,
)
from app.modules.api_keys.audit_models import APIKeyAuditOutbox


def make_session():
    return SimpleNamespace(
        execute=AsyncMock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )


def make_event(workspace_id):
    return APIKeyAuditOutbox(
        id=uuid4(),
        workspace_id=workspace_id,
        actor_user_id=uuid4(),
        key_id=uuid4(),
        action="created",
        replacement_key_id=None,
        occurred_at=datetime.now(timezone.utc),
        delivered_at=None,
    )


def make_delivery():
    workspace_id = uuid4()
    tenant = make_session()
    control = make_session()

    delivery = APIKeyAuditDelivery(
        tenant_session=tenant,
        control_session=control,
        workspace_id=workspace_id,
    )

    event = make_event(workspace_id)

    delivery.repository.pending = AsyncMock(
        return_value=[event]
    )

    return delivery, tenant, control, event


@pytest.mark.asyncio
async def test_control_commits_before_tenant_delivery_marker():
    delivery, tenant, control, event = make_delivery()

    delivery._write_control_event = AsyncMock()

    order = []

    async def control_commit():
        assert event.delivered_at is None
        order.append("control")

    async def tenant_commit():
        assert event.delivered_at is not None
        order.append("tenant")

    control.commit.side_effect = control_commit
    tenant.commit.side_effect = tenant_commit

    assert await delivery.deliver() == 1
    assert order == ["control", "tenant"]

    delivery._write_control_event.assert_awaited_once_with(
        event
    )


@pytest.mark.asyncio
async def test_control_failure_does_not_mark_event_delivered():
    delivery, tenant, control, event = make_delivery()

    delivery._write_control_event = AsyncMock()
    control.commit.side_effect = RuntimeError(
        "Control commit failed"
    )

    with pytest.raises(RuntimeError, match="Control commit"):
        await delivery.deliver()

    assert event.delivered_at is None
    tenant.commit.assert_not_awaited()
    tenant.rollback.assert_awaited_once()
    control.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_tenant_failure_occurs_after_control_commit():
    delivery, tenant, control, event = make_delivery()

    delivery._write_control_event = AsyncMock()
    tenant.commit.side_effect = RuntimeError(
        "Tenant commit failed"
    )

    with pytest.raises(RuntimeError, match="Tenant commit"):
        await delivery.deliver()

    control.commit.assert_awaited_once()
    tenant.rollback.assert_awaited_once()
    control.rollback.assert_awaited_once()

    # Database rollback restores the persisted pending state.
    # This mock does not simulate ORM expiration or database rollback.


@pytest.mark.asyncio
async def test_empty_batch_does_not_commit():
    delivery, tenant, control, event = make_delivery()

    delivery.repository.pending.return_value = []

    assert await delivery.deliver() == 0

    tenant.commit.assert_not_awaited()
    control.commit.assert_not_awaited()
    tenant.rollback.assert_awaited_once()
    control.rollback.assert_awaited_once()


def test_payload_preserves_identity_and_excludes_secret_fields():
    delivery, tenant, control, event = make_delivery()

    payload = delivery._payload(event)

    assert payload["id"] == event.id
    assert payload["workspace_id"] == event.workspace_id
    assert payload["target_id"] == event.key_id
    assert payload["occurred_at"] == event.occurred_at
    assert payload["action"] == "api_keys.created"
    assert payload["event_data"] == {}

    assert "secret" not in payload
    assert "secret_hash" not in payload
    assert "key_prefix" not in payload
    assert "name" not in payload


def test_workspace_mismatch_is_rejected():
    delivery, tenant, control, event = make_delivery()

    event.workspace_id = uuid4()

    with pytest.raises(
        APIKeyAuditDeliveryError,
        match="workspace mismatch",
    ):
        delivery._payload(event)


@pytest.mark.asyncio
async def test_matching_existing_record_allows_retry():
    delivery, tenant, control, event = make_delivery()

    payload = delivery._payload(event)
    existing = SimpleNamespace(**payload)

    result = Mock()
    result.scalar_one.return_value = existing

    control.execute.side_effect = [
        Mock(),
        result,
    ]

    await delivery._write_control_event(event)

    assert control.execute.await_count == 2

    statement = control.execute.await_args_list[0].args[0]
    assert "ON CONFLICT" in str(statement)
    assert "DO NOTHING" in str(statement)


@pytest.mark.asyncio
async def test_conflicting_existing_record_is_rejected():
    delivery, tenant, control, event = make_delivery()

    payload = delivery._payload(event)
    existing = SimpleNamespace(**payload)
    existing.workspace_id = uuid4()

    result = Mock()
    result.scalar_one.return_value = existing

    control.execute.side_effect = [
        Mock(),
        result,
    ]

    with pytest.raises(
        APIKeyAuditDeliveryError,
        match="does not match",
    ):
        await delivery._write_control_event(event)

    control.commit.assert_not_awaited()