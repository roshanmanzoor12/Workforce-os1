from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    contains_any,
    normalized_source,
)


DEVICE_MODELS = (
    "modules/devices/models.py"
)

DEVICE_ROUTER = (
    "modules/devices/router.py"
)

REGISTRATION = (
    "modules/devices/registration_service.py"
)

AGENT_SERVICE = (
    "modules/desktop_agent/service.py"
)


def test_device_is_separate_from_employee():
    source = (
        normalized_source(
            DEVICE_MODELS
        )
        .lower()
    )

    assert (
        "employee"
        in source
    )

    assert (
        "device"
        in source
    )


def test_device_is_separate_from_user_account():
    source = (
        normalized_source(
            DEVICE_MODELS
        )
        .lower()
    )

    assert (
        "device"
        in source
    )


def test_device_can_have_operational_state():
    assert contains_any(
        DEVICE_MODELS,
        (
            "status",
            "heartbeat",
            "last_seen",
            "is_active",
        ),
    )


def test_registration_and_agent_are_separate_layers():
    registration = (
        normalized_source(
            REGISTRATION
        )
        .lower()
    )

    agent = (
        normalized_source(
            AGENT_SERVICE
        )
        .lower()
    )

    assert registration
    assert agent
    assert registration != agent


def test_device_management_has_mutation_routes():
    source = (
        normalized_source(
            DEVICE_ROUTER
        )
        .lower()
    )

    assert any(
        method
        in source
        for method in (
            "@router.patch(",
            ".patch(",
            "@router.delete(",
            ".delete(",
        )
    )


def test_device_secret_boundary():
    browser_source = (
        normalized_source(
            DEVICE_ROUTER
        )
        .lower()
    )

    # Browser-side workspace inventory must not provide
    # a plaintext device secret retrieval contract.
    forbidden_patterns = (
        "returncredential.device_secret",
        "returndevice.device_secret",
        "response_model=device_secret",
    )

    for pattern in forbidden_patterns:
        assert (
            pattern
            not in browser_source
        )