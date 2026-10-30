from __future__ import annotations

from tests.modules.monitoring.phase14_monitoring_overview_contract import (
    MONITORING_OVERVIEW_ENDPOINTS,
)
from tests.modules.monitoring.phase14_openapi_helpers import (
    operation,
)


def test_monitoring_overview_browser_contract():
    missing: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        MONITORING_OVERVIEW_ENDPOINTS
    ):
        try:
            operation(
                method=method,
                path=path,
            )

        except AssertionError:
            missing.append(
                f"{method} {path}"
            )

    assert not missing, (
        "Missing Monitoring Overview API contract: "
        + "; ".join(
            missing
        )
    )