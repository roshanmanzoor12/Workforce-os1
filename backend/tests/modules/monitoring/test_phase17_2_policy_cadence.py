from __future__ import annotations

import inspect

import pytest
from pydantic import (
    ValidationError as PydanticValidationError,
)

from app.modules.monitoring_admin.models import (
    MonitoringAdminPolicy,
)
from app.modules.monitoring_admin.schemas import (
    MonitoringAdminPolicyPublic,
    MonitoringAdminPolicyUpdate,
    MonitoringPolicyCapabilities,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)


def test_policy_model_has_screenshot_interval():
    assert hasattr(
        MonitoringAdminPolicy,
        "screenshot_interval_seconds",
    )


def test_policy_update_accepts_positive_interval():
    payload = (
        MonitoringAdminPolicyUpdate(
            screenshot_interval_seconds=300
        )
    )

    assert (
        payload
        .screenshot_interval_seconds
        == 300
    )


def test_policy_update_rejects_zero_interval():
    with pytest.raises(
        PydanticValidationError
    ):
        MonitoringAdminPolicyUpdate(
            screenshot_interval_seconds=0
        )


def test_public_policy_exposes_interval():
    assert (
        "screenshot_interval_seconds"
        in (
            MonitoringAdminPolicyPublic
            .model_fields
        )
    )


def test_capabilities_expose_interval():
    assert (
        "screenshot_interval_seconds"
        in (
            MonitoringPolicyCapabilities
            .model_fields
        )
    )


def test_service_maps_interval_to_public_policy():
    source = inspect.getsource(
        MonitoringAdminService
        .public_policy
    )

    assert (
        "screenshot_interval_seconds"
        in source
    )


def test_service_maps_interval_to_capabilities():
    source = inspect.getsource(
        MonitoringAdminService
        .capabilities_from_policy
    )

    assert (
        "screenshot_interval_seconds"
        in source
    )