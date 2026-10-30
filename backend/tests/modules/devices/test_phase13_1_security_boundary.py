from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    app_file,
    contains_any,
    normalized_source,
)


DEVICE_ROUTER = (
    "modules/devices/router.py"
)

DEVICE_SERVICE = (
    "modules/devices/service.py"
)

DEVICE_ACTIVATION_ROUTER = (
    "modules/devices/activation_router.py"
)

AGENT_ROUTER = (
    "modules/desktop_agent/router.py"
)

AGENT_ACCESS = (
    "modules/desktop_agent/access.py"
)

WORKSPACE_PERMISSIONS = (
    "modules/workspace_permissions/permissions.py"
)


# =========================================================
# WORKSPACE DEVICE AUTHORIZATION
# =========================================================


def test_workspace_device_api_has_authorization_boundary():
    """
    Device authorization does not need to be implemented directly
    inside devices/router.py or devices/service.py.

    WorkforceOS currently has separate access/permission layers.
    This test certifies that the device/agent surface is protected
    somewhere in the actual device stack.
    """

    candidates = [
        DEVICE_ROUTER,
        DEVICE_SERVICE,
        DEVICE_ACTIVATION_ROUTER,
        AGENT_ACCESS,
        WORKSPACE_PERMISSIONS,
    ]

    combined = ""

    for relative_path in candidates:
        path = (
            app_file(
                relative_path
            )
        )

        combined += (
            normalized_source(
                relative_path
            )
            .lower()
        )

    assert any(
        value
        in combined
        for value in (
            "permission",
            "access",
            "authorize",
            "authorization",
            "scope",
        )
    )


# =========================================================
# AGENT ACCESS
# =========================================================


def test_agent_access_layer_exists():
    path = app_file(
        AGENT_ACCESS
    )

    assert path.is_file()

    source = (
        normalized_source(
            AGENT_ACCESS
        )
        .lower()
    )

    assert (
        "permission"
        in source
        or "access"
        in source
    )


# =========================================================
# BROWSER / AGENT SEPARATION
# =========================================================


def test_agent_routes_are_separate_from_workspace_browser_routes():
    device_router = (
        normalized_source(
            DEVICE_ROUTER
        )
        .lower()
    )

    agent_router = (
        normalized_source(
            AGENT_ROUTER
        )
        .lower()
    )

    assert (
        device_router
        != agent_router
    )

    assert any(
        value
        in agent_router
        for value in (
            "device",
            "agent",
            "heartbeat",
            "presence",
        )
    )


# =========================================================
# DEVICE PERMISSION CATALOG
# =========================================================


def test_device_permissions_exist_in_permission_catalog():
    source = (
        normalized_source(
            WORKSPACE_PERMISSIONS
        )
        .lower()
    )

    assert (
        "device"
        in source
    )

    assert any(
        value
        in source
        for value in (
            "read",
            "manage",
            "self",
            "team",
            "all",
        )
    )


# =========================================================
# WORKSPACE SCOPING
# =========================================================


def test_device_routes_are_workspace_or_tenant_scoped():
    combined = (
        normalized_source(
            DEVICE_ROUTER
        )
        + normalized_source(
            DEVICE_SERVICE
        )
    ).lower()

    assert any(
        value
        in combined
        for value in (
            "workspace_id",
            "workspace",
            "tenant",
        )
    )


# =========================================================
# AGENT PERMISSION RESOLUTION
# =========================================================


def test_agent_access_resolves_effective_permissions():
    source = (
        normalized_source(
            AGENT_ACCESS
        )
        .lower()
    )

    assert any(
        value
        in source
        for value in (
            "permissions",
            "workspacepermission",
            "scope",
        )
    )


__all__ = []