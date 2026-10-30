from __future__ import annotations

from tests.modules.devices.phase13_3_agent_signal_contract import (
    api_path,
)
from tests.modules.devices.phase13_3_openapi_helpers import (
    operation,
)


def test_activity_state_route_exists():
    operation(
        method="POST",
        path=api_path(
            "/device-agent/activity-state"
        ),
    )


def test_activity_status_route_exists():
    operation(
        method="GET",
        path=api_path(
            "/device-agent/activity-status"
        ),
    )


def test_activity_methods_are_exact():
    assert (
        api_path(
            "/device-agent/activity-state"
        )
        != api_path(
            "/device-agent/activity-status"
        )
    )