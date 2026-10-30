from __future__ import annotations

import uuid

from app.modules.tenant_api.context import (
    AuthorizedTenantContext,
)


def test_context_has_workspace_identity(
) -> None:
    annotations = (
        AuthorizedTenantContext.__annotations__
    )

    assert "workspace_id" in annotations
    assert "actor_user_id" in annotations


def test_context_separates_control_and_tenant_sessions(
) -> None:
    annotations = (
        AuthorizedTenantContext.__annotations__
    )

    assert "control_session" in annotations
    assert "tenant_session" in annotations


def test_context_does_not_expose_database_credentials(
) -> None:
    annotations = (
        AuthorizedTenantContext.__annotations__
    )

    forbidden = {
        "database_url",
        "database_name",
        "password",
        "connection_string",
    }

    assert not (
        forbidden
        & set(annotations.keys())
    )