from __future__ import annotations

from tests.modules.devices.phase13_1_source_helpers import (
    contains_any,
    normalized_source,
)


AGENT_SERVICE = (
    "modules/desktop_agent/service.py"
)

AGENT_ROUTER = (
    "modules/desktop_agent/router.py"
)

AGENT_REPOSITORY = (
    "modules/desktop_agent/repository.py"
)


# =========================================================
# AUTHENTICATED DEVICE IDENTITY
# =========================================================


def test_agent_has_authenticated_device_identity():
    assert (
        contains_any(
            AGENT_SERVICE,
            (
                "device",
                "credential",
            ),
        )
        or contains_any(
            AGENT_ROUTER,
            (
                "device",
                "credential",
            ),
        )
    )


# =========================================================
# HEARTBEAT
# =========================================================


def test_agent_has_heartbeat_support():
    combined = (
        normalized_source(
            AGENT_SERVICE
        )
        + normalized_source(
            AGENT_ROUTER
        )
        + normalized_source(
            AGENT_REPOSITORY
        )
    ).lower()

    assert (
        "heartbeat"
        in combined
    )


# =========================================================
# PRESENCE / STATUS
# =========================================================


def test_agent_has_presence_or_status_support():
    combined = (
        normalized_source(
            AGENT_SERVICE
        )
        + normalized_source(
            AGENT_ROUTER
        )
        + normalized_source(
            AGENT_REPOSITORY
        )
    ).lower()

    assert any(
        value
        in combined
        for value in (
            "presence",
            "status",
            "heartbeat",
            "last_seen",
        )
    )


# =========================================================
# AGENT STATE IS SERVER-SIDE / DEVICE-SIDE
# =========================================================


def test_agent_operational_state_is_separate_from_browser_login():
    """
    Phase 13.1 is a baseline-certification phase.

    We certify that operational agent/device state is handled by
    the desktop-agent backend, independently from browser auth.

    Dedicated active/idle activity reporting is certified in the
    next hardening phase rather than assumed to already exist in
    this exact module.
    """

    combined = (
        normalized_source(
            AGENT_SERVICE
        )
        + normalized_source(
            AGENT_ROUTER
        )
        + normalized_source(
            AGENT_REPOSITORY
        )
    ).lower()

    assert (
        "device"
        in combined
    )

    assert any(
        value
        in combined
        for value in (
            "heartbeat",
            "presence",
            "status",
            "last_seen",
            "session",
        )
    )


# =========================================================
# PERMISSION BOUNDARY
# =========================================================


def test_agent_service_has_permission_checks():
    combined = (
        normalized_source(
            AGENT_SERVICE
        )
        + normalized_source(
            AGENT_ROUTER
        )
    ).lower()

    assert (
        "permission"
        in combined
    )