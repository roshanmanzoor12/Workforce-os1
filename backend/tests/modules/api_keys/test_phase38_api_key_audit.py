from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from app.modules.api_keys.audit_models import APIKeyAuditOutbox
from app.modules.api_keys.audit_repository import APIKeyAuditRepository
from app.modules.api_keys.schemas import APIKeyCreate
from app.modules.api_keys.service import APIKeyService
from app.modules.workspace_permissions.roles import OWNER_ROLE


class MemoryKeyRepository:
    def __init__(self):
        self.rows = {}

    async def add(self, row):
        self.rows[row.id] = row

    async def get(self, key_id, *, for_update=False):
        return self.rows.get(key_id)


def make_service():
    scope = SimpleNamespace(
        workspace_id=uuid4(),
        user_id=uuid4(),
        role_key=OWNER_ROLE,
        session=SimpleNamespace(
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            rollback=AsyncMock(),
        ),
    )
    service = APIKeyService(scope)
    service.repository = MemoryKeyRepository()
    return service, scope


def create_payload():
    return APIKeyCreate(
        name="Audit test",
        scopes=["reports.self.read"],
    )


def queued_events(scope):
    return [
        call.args[0]
        for call in scope.session.add.call_args_list
    ]


def test_creation_queues_secret_free_event_before_commit():
    async def scenario():
        service, scope = make_service()
        scope.session.commit.side_effect = lambda: (
            assert_event_already_queued(scope)
        )

        issued = await service.create_key(create_payload())
        events = queued_events(scope)

        assert len(events) == 1
        event = events[0]
        assert event.workspace_id == scope.workspace_id
        assert event.actor_user_id == scope.user_id
        assert event.key_id == issued.key.id
        assert event.action == "created"
        assert event.replacement_key_id is None
        assert event.delivered_at is None

        fields = set(inspect(APIKeyAuditOutbox).columns.keys())
        assert not fields.intersection(
            {"secret", "secret_hash", "name", "event_data"}
        )
        scope.session.rollback.assert_not_awaited()

    asyncio.run(scenario())


def assert_event_already_queued(scope):
    assert len(queued_events(scope)) == 1


def test_repeated_revocation_queues_only_one_revocation():
    async def scenario():
        service, scope = make_service()
        issued = await service.create_key(create_payload())

        first = await service.revoke_key(issued.key.id)
        second = await service.revoke_key(issued.key.id)

        revoked = [
            event for event in queued_events(scope)
            if event.action == "revoked"
        ]
        assert len(revoked) == 1
        assert first.revoked_at == second.revoked_at
        assert revoked[0].occurred_at == first.revoked_at

    asyncio.run(scenario())


def test_rotation_links_original_and_replacement():
    async def scenario():
        service, scope = make_service()
        original = await service.create_key(create_payload())
        replacement = await service.rotate_key(original.key.id)

        events = queued_events(scope)
        assert [event.action for event in events] == [
            "created",
            "rotated",
        ]
        event = events[-1]
        assert event.key_id == original.key.id
        assert event.replacement_key_id == replacement.key.id
        assert service.repository.rows[
            original.key.id
        ].revoked_at is not None

    asyncio.run(scenario())


def test_outbox_enqueue_failure_prevents_commit():
    async def scenario():
        service, scope = make_service()
        scope.session.add.side_effect = RuntimeError(
            "Outbox write failed"
        )

        with pytest.raises(RuntimeError, match="Outbox write failed"):
            await service.create_key(create_payload())

        scope.session.commit.assert_not_awaited()
        scope.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_commit_failure_rolls_back_combined_transaction():
    async def scenario():
        service, scope = make_service()
        scope.session.commit.side_effect = RuntimeError(
            "Commit failed"
        )

        with pytest.raises(RuntimeError, match="Commit failed"):
            await service.create_key(create_payload())

        assert len(queued_events(scope)) == 1
        scope.session.rollback.assert_awaited_once()

    asyncio.run(scenario())


def test_pending_query_is_workspace_scoped_and_locks_rows():
    async def scenario():
        result = Mock()
        result.scalars.return_value.all.return_value = []
        session = SimpleNamespace(
            execute=AsyncMock(return_value=result),
        )
        repository = APIKeyAuditRepository(session, uuid4())

        assert await repository.pending(limit=25) == []

        statement = session.execute.call_args.args[0]
        sql = str(statement.compile(dialect=postgresql.dialect()))

        assert "workspace_id =" in sql
        assert "delivered_at IS NULL" in sql
        assert "FOR UPDATE SKIP LOCKED" in sql
        assert "LIMIT" in sql

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("action", "replacement"),
    [
        ("unsupported", None),
        ("rotated", None),
        ("created", uuid4()),
        ("revoked", uuid4()),
    ],
)
def test_invalid_audit_actions_cannot_be_enqueued(action, replacement):
    session = SimpleNamespace(add=Mock())
    repository = APIKeyAuditRepository(session, uuid4())

    with pytest.raises(ValueError):
        repository.enqueue(
            actor_user_id=uuid4(),
            key_id=uuid4(),
            action=action,
            occurred_at=datetime.now(timezone.utc),
            replacement_key_id=replacement,
        )

    session.add.assert_not_called()