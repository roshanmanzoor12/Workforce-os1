from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    app_file,
)


def test_core_device_files_exist():
    required = [
        "modules/devices/models.py",
        "modules/devices/repository.py",
        "modules/devices/service.py",
        "modules/devices/router.py",
    ]

    for path in required:
        assert app_file(
            path
        ).is_file()


def test_device_registration_service_exists():
    assert app_file(
        "modules/devices/registration_service.py"
    ).is_file()


def test_device_routing_components_exist():
    assert app_file(
        "modules/devices/routing_repository.py"
    ).is_file()

    assert app_file(
        "modules/devices/routing_service.py"
    ).is_file()


def test_device_activation_router_exists():
    assert app_file(
        "modules/devices/activation_router.py"
    ).is_file()


def test_desktop_agent_components_exist():
    assert app_file(
        "modules/desktop_agent/router.py"
    ).is_file()

    assert app_file(
        "modules/desktop_agent/service.py"
    ).is_file()

    assert app_file(
        "modules/desktop_agent/repository.py"
    ).is_file()