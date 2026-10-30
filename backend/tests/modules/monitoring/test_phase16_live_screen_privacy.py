from __future__ import annotations

from app.modules.live_monitoring.schemas import (
    LiveMonitoringCapabilitiesResponse,
    LiveScreenResponse,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringService,
)


FORBIDDEN_RESPONSE_FIELDS = {
    "device_secret",
    "secret_hash",
    "credential_hash",
    "password",
    "passwords",
    "clipboard",
    "keystrokes",
    "typed_text",
    "last_ip_address",
    "database_name",
    "cluster_key",
}


def test_live_screen_response_has_no_agent_secrets():
    fields = {
        name.lower()
        for name
        in LiveScreenResponse
        .model_fields
        .keys()
    }

    leaked = sorted(
        fields
        & FORBIDDEN_RESPONSE_FIELDS
    )

    assert not leaked, (
        "Live Screen response exposes "
        "forbidden fields: "
        + ", ".join(
            leaked
        )
    )


def test_live_monitoring_capabilities_are_privacy_safe():
    capabilities = (
        LiveMonitoringService
        .capabilities()
    )

    assert isinstance(
        capabilities,
        LiveMonitoringCapabilitiesResponse,
    )

    assert (
        capabilities
        .captures_keystrokes
        is False
    )

    assert (
        capabilities
        .captures_clipboard
        is False
    )

    assert (
        capabilities
        .captures_passwords
        is False
    )

    assert (
        capabilities
        .captures_mouse_coordinates
        is False
    )


def test_live_screen_requires_acceptance():
    capabilities = (
        LiveMonitoringService
        .capabilities()
    )

    assert (
        capabilities
        .live_screen_requires_acceptance
        is True
    )


def test_live_screen_requires_visible_indicator():
    capabilities = (
        LiveMonitoringService
        .capabilities()
    )

    assert (
        capabilities
        .live_screen_visible_indicator
        is True
    )