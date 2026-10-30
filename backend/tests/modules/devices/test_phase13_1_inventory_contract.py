from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    class_names,
    contains_any,
    normalized_source,
)


DEVICE_MODELS = (
    "modules/devices/models.py"
)

DEVICE_ROUTER = (
    "modules/devices/router.py"
)


def test_device_model_exists():
    classes = class_names(
        DEVICE_MODELS
    )

    assert any(
        "device"
        in name.lower()
        for name in classes
    )


def test_device_has_workspace_or_tenant_scope():
    assert contains_any(
        DEVICE_MODELS,
        (
            "workspace_id",
            "tenant",
        ),
    )


def test_device_has_employee_assignment_reference():
    assert contains_any(
        DEVICE_MODELS,
        (
            "employee_id",
            "assigned_employee",
        ),
    )


def test_device_tracks_last_seen_or_heartbeat():
    assert contains_any(
        DEVICE_MODELS,
        (
            "last_heartbeat",
            "heartbeat",
            "last_seen",
            "last_seen_at",
        ),
    )


def test_device_tracks_agent_or_client_version():
    assert contains_any(
        DEVICE_MODELS,
        (
            "agent_version",
            "version",
        ),
    )


def test_workspace_device_collection_route_exists():
    source = normalized_source(
        DEVICE_ROUTER
    ).lower()

    assert (
        "devices"
        in source
    )


def test_device_router_exposes_read_operation():
    source = normalized_source(
        DEVICE_ROUTER
    ).lower()

    assert (
        ".get("
        in source
        or "@router.get("
        in source
    )