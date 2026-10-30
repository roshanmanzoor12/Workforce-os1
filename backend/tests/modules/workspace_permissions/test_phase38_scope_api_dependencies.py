from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


dependencies = importlib.import_module(
    "app.modules.workspace_rbac.scope_dependencies",
)


def scope(workspace_id):
    return SimpleNamespace(
        workspace_id=workspace_id,
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        session=object(),
    )


def test_factory_uses_server_resolved_scope_and_control_session(
    monkeypatch,
):
    workspace_id = uuid.uuid4()
    tenant_scope = scope(workspace_id)
    control_session = object()
    expected = object()
    calls = []

    def build(control, tenant):
        calls.append((control, tenant))
        return expected

    monkeypatch.setattr(
        dependencies,
        "MembershipScopeGrantService",
        build,
    )

    result = dependencies.get_membership_scope_service(
        workspace_id,
        tenant_scope,
        control_session,
    )

    assert result is expected
    assert calls == [(control_session, tenant_scope)]


def test_wrong_workspace_stops_service_creation(monkeypatch):
    calls = []

    def build(*args):
        calls.append(args)
        raise AssertionError("Service must not be constructed.")

    monkeypatch.setattr(
        dependencies,
        "MembershipScopeGrantService",
        build,
    )

    with pytest.raises(HTTPException) as error:
        dependencies.get_membership_scope_service(
            uuid.uuid4(),
            scope(uuid.uuid4()),
            object(),
        )

    assert error.value.status_code == 403
    assert calls == []


@pytest.mark.parametrize(
    "missing_field",
    ["user_id", "membership_id"],
)
def test_missing_actor_identity_is_rejected(missing_field):
    workspace_id = uuid.uuid4()
    tenant_scope = scope(workspace_id)
    setattr(tenant_scope, missing_field, None)

    with pytest.raises(HTTPException) as error:
        dependencies.get_membership_scope_service(
            workspace_id,
            tenant_scope,
            object(),
        )

    assert error.value.status_code == 403