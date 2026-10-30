from __future__ import annotations

from tests.modules.devices.phase13_3_agent_signal_contract import (
    api_path,
)
from tests.modules.devices.phase13_3_openapi_helpers import (
    openapi_paths,
)


EXPECTED = {
    api_path(
        "/device-agent/activity-state"
    ): {
        "post",
    },

    api_path(
        "/device-agent/activity-status"
    ): {
        "get",
    },

    api_path(
        "/device-agent/app-observation"
    ): {
        "post",
    },

    api_path(
        "/device-agent/app-status"
    ): {
        "get",
    },

    api_path(
        "/device-agent/app-history"
    ): {
        "get",
    },
}


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
}


def test_agent_signal_http_methods_are_exact():
    paths = openapi_paths()

    failures: list[str] = []

    for (
        path,
        expected_methods,
    ) in EXPECTED.items():
        item = paths.get(
            path
        )

        if not isinstance(
            item,
            dict,
        ):
            failures.append(
                f"missing {path}"
            )
            continue

        actual_methods = {
            key.lower()
            for key in item.keys()
            if key.lower()
            in HTTP_METHODS
        }

        if (
            actual_methods
            != expected_methods
        ):
            failures.append(
                (
                    f"{path}: "
                    f"expected="
                    f"{sorted(expected_methods)} "
                    f"actual="
                    f"{sorted(actual_methods)}"
                )
            )

    assert not failures, (
        "Agent signal HTTP contract failed: "
        + "; ".join(
            failures
        )
    )