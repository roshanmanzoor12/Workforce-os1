from __future__ import annotations

from typing import Any

from tests.modules.devices.phase13_3_agent_signal_contract import (
    EXPECTED_AGENT_SIGNAL_ENDPOINTS,
)
from tests.modules.devices.phase13_3_openapi_helpers import (
    operation,
)


SENSITIVE_RESPONSE_FIELDS = (
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


def test_agent_signal_responses_do_not_expose_secrets():
    failures: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        EXPECTED_AGENT_SIGNAL_ENDPOINTS
    ):
        item = operation(
            method=method,
            path=path,
        )

        responses = item.get(
            "responses",
            {}
        )

        serialized = _serialized(
            responses
        )

        leaked = [
            field
            for field
            in SENSITIVE_RESPONSE_FIELDS
            if field
            in serialized
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
        "Sensitive fields exposed by "
        "agent signal response contracts: "
        + "; ".join(
            failures
        )
    )