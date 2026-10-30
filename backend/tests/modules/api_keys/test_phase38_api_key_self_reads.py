from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.api_keys.self_read_router import (
    SELF_REPORT_ACCESS,
    self_analytics_access,
    validate_self_report,
)
from app.modules.analytics.access import AnalyticsScope
from app.modules.reports.schemas import (
    ReportKey,
    ReportRunRequest,
    ReportScope,
)


@pytest.mark.parametrize(
    "report_scope",
    [ReportScope.TEAM, ReportScope.WORKSPACE],
)
def test_broader_report_scope_is_rejected(report_scope):
    request = ReportRunRequest(
        report=ReportKey.ATTENDANCE,
        scope=report_scope,
    )

    with pytest.raises(HTTPException) as error:
        validate_self_report(request)

    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "field",
    ["employee_id", "team_id", "department_id"],
)
def test_target_filters_are_rejected(field):
    request = ReportRunRequest(
        report=ReportKey.ATTENDANCE,
        scope=ReportScope.SELF,
        **{field: uuid4()},
    )

    with pytest.raises(HTTPException) as error:
        validate_self_report(request)

    assert error.value.status_code == 403


def test_self_report_is_allowed_without_export_or_broader_access():
    request = ReportRunRequest(
        report=ReportKey.ATTENDANCE,
        scope=ReportScope.SELF,
    )

    validate_self_report(request)

    assert SELF_REPORT_ACCESS.effective_scopes == [ReportScope.SELF]
    assert not SELF_REPORT_ACCESS.can_read_team
    assert not SELF_REPORT_ACCESS.can_read_workspace
    assert not SELF_REPORT_ACCESS.can_export


@pytest.mark.asyncio
@pytest.mark.parametrize("has_employee", [True, False])
async def test_owner_analytics_is_restricted_to_self(has_employee):
    employee_id = uuid4() if has_employee else None
    user_id = uuid4()

    result = SimpleNamespace(
        scalar_one_or_none=lambda: employee_id
    )

    session = SimpleNamespace(
        execute=AsyncMock(return_value=result)
    )

    scope = SimpleNamespace(
        session=session,
        workspace_id=uuid4(),
        user_id=user_id,
        role_key="owner",
    )

    access = await self_analytics_access(scope)

    assert access.scope == AnalyticsScope.SELF
    assert access.actor_user_id == user_id
    assert access.employee_ids == (
        frozenset({employee_id})
        if has_employee
        else frozenset()
    )

    # None would mean unrestricted employees; never permit it here.
    assert access.employee_ids is not None

    statement = session.execute.await_args.args[0]
    assert user_id in statement.compile().params.values()


@pytest.mark.parametrize(
    "suffix,method",
    [
        ("/reports/catalog", "get"),
        ("/reports/run", "post"),
        ("/analytics/overview", "get"),
    ],
)
def test_self_endpoints_registered_with_key_security(suffix, method):
    from app.main import app

    path = (
        "/api/v1/workspaces/{workspace_id}/integrations"
        + suffix
    )

    operation = app.openapi()["paths"][path][method]

    assert {"WorkspaceAPIKey": []} in operation["security"]