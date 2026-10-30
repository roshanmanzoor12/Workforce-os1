from __future__ import annotations

import importlib
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest


dependencies = importlib.import_module(
    "app.db.tenant_dependency"
)


def make_context():
    return SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset({"employees.read"}),
        schema_version=None,
    )


def test_scope_preserves_existing_two_argument_construction():
    context = make_context()
    tenant = object()

    scope = dependencies.TenantRequestScope(context, tenant)

    assert scope.session is tenant
    assert scope.control_session is None
    assert scope.workspace_id == context.workspace_id
    assert scope.user_id == context.user_id
    assert scope.membership_id == context.membership_id
    assert scope.effective_permissions == context.effective_permissions


@pytest.mark.asyncio
async def test_http_dependency_supplies_control_session_and_closes_tenant(
    monkeypatch,
):
    context = make_context()
    control = object()
    tenant = object()
    calls = []
    closed = []

    @asynccontextmanager
    async def authorized_session(
        actual_control,
        *,
        workspace_id,
        user_id,
    ):
        calls.append((actual_control, workspace_id, user_id))

        try:
            yield context, tenant
        finally:
            closed.append(True)

    monkeypatch.setattr(
        dependencies,
        "authorized_tenant_session",
        authorized_session,
    )

    generator = dependencies.get_tenant_scope(
        context.workspace_id,
        control,
        SimpleNamespace(id=context.user_id),
    )

    scope = await anext(generator)

    assert scope.context is context
    assert scope.session is tenant
    assert scope.control_session is control
    assert calls == [
        (control, context.workspace_id, context.user_id),
    ]
    assert closed == []

    await generator.aclose()

    assert closed == [True]