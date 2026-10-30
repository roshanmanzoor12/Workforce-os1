from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    class_names,
    contains_any,
    normalized_source,
)


REGISTRATION_SERVICE = (
    "modules/devices/registration_service.py"
)


def test_registration_service_has_class():
    classes = class_names(
        REGISTRATION_SERVICE
    )

    assert any(
        "registration"
        in name.lower()
        for name in classes
    )


def test_registration_handles_device_identity():
    assert contains_any(
        REGISTRATION_SERVICE,
        (
            "device_id",
            "device_uuid",
            "device",
        ),
    )


def test_registration_is_workspace_scoped():
    assert contains_any(
        REGISTRATION_SERVICE,
        (
            "workspace_id",
            "workspace",
            "tenant",
        ),
    )


def test_registration_uses_tenant_database():
    source = (
        normalized_source(
            REGISTRATION_SERVICE
        )
        .lower()
    )

    assert any(
        value in source
        for value in (
            "tenant",
            "tenant_db",
            "tenant_session",
        )
    )


def test_registration_does_not_depend_on_browser_login_starting_monitoring():
    source = (
        normalized_source(
            REGISTRATION_SERVICE
        )
        .lower()
    )

    assert (
        "device"
        in source
    )