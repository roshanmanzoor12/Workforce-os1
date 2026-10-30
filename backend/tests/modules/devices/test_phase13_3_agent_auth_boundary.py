from __future__ import annotations

import inspect

from app.modules.activity.agent_router import (
    get_device_activity_status,
    report_device_activity_state,
)
from app.modules.app_tracking.agent_history_router import (
    get_device_app_history,
)
from app.modules.app_tracking.agent_router import (
    report_device_app_observation,
)
from app.modules.app_tracking.status_router import (
    get_device_current_app_status,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)


ENDPOINTS = (
    report_device_activity_state,
    get_device_activity_status,
    report_device_app_observation,
    get_device_current_app_status,
    get_device_app_history,
)


def _uses_authenticated_device_dependency(
    endpoint,
) -> bool:
    signature = inspect.signature(
        endpoint
    )

    for parameter in (
        signature.parameters.values()
    ):
        default = parameter.default

        dependency = getattr(
            default,
            "dependency",
            None,
        )

        if (
            dependency
            is get_authenticated_device
        ):
            return True

    return False


def test_agent_signal_routes_require_authenticated_device():
    failures = [
        endpoint.__name__
        for endpoint in ENDPOINTS
        if not (
            _uses_authenticated_device_dependency(
                endpoint
            )
        )
    ]

    assert not failures, (
        "Agent signal endpoints missing "
        "get_authenticated_device dependency: "
        + ", ".join(
            failures
        )
    )