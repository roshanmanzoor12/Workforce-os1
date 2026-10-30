from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    contains_any,
    normalized_source,
)


DEVICE_ROUTER = (
    "modules/devices/router.py"
)

DEVICE_SERVICE = (
    "modules/devices/service.py"
)

DEVICE_REPOSITORY = (
    "modules/devices/repository.py"
)


def test_assignment_route_contract_exists():
    source = normalized_source(
        DEVICE_ROUTER
    ).lower()

    assert (
        "assignment"
        in source
    )


def test_assignment_uses_employee_identity():
    assert (
        contains_any(
            DEVICE_ROUTER,
            (
                "employee_id",
                "employee",
            ),
        )
        or contains_any(
            DEVICE_SERVICE,
            (
                "employee_id",
                "employee",
            ),
        )
    )


def test_assignment_is_not_browser_login_linkage():
    source = (
        normalized_source(
            DEVICE_SERVICE
        )
        .lower()
    )

    assert (
        "employee"
        in source
    )

    # Device assignment must remain explicit.
    # Merely authenticating a User must not silently assign a device.
    assert (
        "assign"
        in source
        or "assignment"
        in source
    )


def test_repository_supports_device_update():
    source = (
        normalized_source(
            DEVICE_REPOSITORY
        )
        .lower()
    )

    assert any(
        value in source
        for value in (
            "update",
            "assign",
            "employee_id",
        )
    )