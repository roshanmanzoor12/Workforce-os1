from __future__ import annotations

from typing import Any

from tests.modules.monitoring.phase14_monitoring_overview_contract import (
    MONITORING_OVERVIEW_ENDPOINTS,
)
from tests.modules.monitoring.phase14_openapi_helpers import (
    operation,
)


FORBIDDEN_BROWSER_FIELDS = (
    "device_secret",
    "secret_hash",
    "credential_hash",
    "database_name",
    "cluster_key",
)


def _serialized(
    value: Any,
) -> str:
    return repr(
        value
    ).lower()


def test_monitoring_browser_contract_does_not_expose_agent_secrets():
    failures: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        MONITORING_OVERVIEW_ENDPOINTS
    ):
        item = operation(
            method=method,
            path=path,
        )

        response_text = _serialized(
            item.get(
                "responses",
                {},
            )
        )

        leaked = [
            field
            for field
            in FORBIDDEN_BROWSER_FIELDS
            if field
            in response_text
        ]

        if leaked:
            failures.append(
                (
                    f"{method} {path}: "
                    + ", ".join(
                        leaked
                    )
                )
            )

    assert not failures, (
        "Browser monitoring API exposes "
        "sensitive device/tenant fields: "
        + "; ".join(
            failures
        )
    )