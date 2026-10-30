from __future__ import annotations

from tests.modules.devices.phase13_3_agent_signal_contract import (
    api_path,
)
from tests.modules.devices.phase13_3_openapi_helpers import (
    operation,
)


def test_app_observation_route_exists():
    operation(
        method="POST",
        path=api_path(
            "/device-agent/app-observation"
        ),
    )


def test_app_status_route_exists():
    operation(
        method="GET",
        path=api_path(
            "/device-agent/app-status"
        ),
    )


def test_app_history_route_exists():
    operation(
        method="GET",
        path=api_path(
            "/device-agent/app-history"
        ),
    )