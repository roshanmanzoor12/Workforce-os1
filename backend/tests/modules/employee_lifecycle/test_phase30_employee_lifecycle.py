from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.modules.employee_lifecycle.router import router
from app.modules.employee_lifecycle.schemas import (
    OffboardingCreateRequest,
    OnboardingCreateRequest,
)


def test_phase30_onboarding_schema() -> None:
    request = OnboardingCreateRequest(
        employee_id=uuid.uuid4(),
        start_date=date(2026, 10, 10),
        tasks=[
            "  Create account  ",
            "",
            "  Issue laptop  ",
        ],
    )

    assert request.tasks == [
        "Create account",
        "Issue laptop",
    ]


def test_phase30_offboarding_schema() -> None:
    request = OffboardingCreateRequest(
        employee_id=uuid.uuid4(),
        last_working_date=date(2026, 11, 1),
        reason="  Resignation  ",
    )

    assert request.reason == "Resignation"


def test_phase30_routes_registered() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/employee-lifecycle/onboarding"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/employee-lifecycle/onboarding/{record_id}"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/employee-lifecycle/offboarding"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/employee-lifecycle/offboarding/{record_id}"
        in paths
    )


def test_phase30_unknown_fields_rejected() -> None:
    with pytest.raises(ValueError):
        OnboardingCreateRequest(
            employee_id=uuid.uuid4(),
            unknown_field="invalid",
        )