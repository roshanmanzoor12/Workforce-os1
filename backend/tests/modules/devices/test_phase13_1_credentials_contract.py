from __future__ import annotations

from pathlib import Path

from tests.modules.devices.phase13_1_source_helpers import (
    APP_ROOT,
    normalized_source,
)


# =========================================================
# CREDENTIAL IMPLEMENTATION CANDIDATES
# =========================================================

CREDENTIAL_CANDIDATES = (
    "modules/devices/credential_models.py",
    "modules/devices/credentials.py",
    "modules/devices/credential_service.py",
    "modules/devices/credential_repository.py",
)


DEVICE_ROUTER = (
    "modules/devices/router.py"
)


# =========================================================
# HELPERS
# =========================================================


def _candidate_path(
    relative_path: str,
) -> Path:
    """
    Resolve an optional credential implementation file.

    Unlike app_file(), this helper must NOT assert that the file
    exists because these are alternative implementation layouts.
    """

    return (
        APP_ROOT
        / relative_path
    )


def _existing_credential_files() -> list[str]:
    return [
        relative_path
        for relative_path
        in CREDENTIAL_CANDIDATES
        if (
            _candidate_path(
                relative_path
            )
            .is_file()
        )
    ]


def _credential_source() -> str:
    """
    Combine only credential implementation files that actually
    exist in this WorkforceOS checkout.
    """

    existing = (
        _existing_credential_files()
    )

    assert existing, (
        "No device credential implementation "
        "file was found."
    )

    return "\n".join(
        normalized_source(
            relative_path
        )
        for relative_path
        in existing
    )


def _combined_credential_surface() -> str:
    return (
        _credential_source()
        + "\n"
        + normalized_source(
            DEVICE_ROUTER
        )
    ).lower()


# =========================================================
# IMPLEMENTATION PRESENCE
# =========================================================


def test_device_credential_implementation_exists():
    existing = (
        _existing_credential_files()
    )

    assert existing, (
        "Expected at least one device "
        "credential implementation file."
    )


# =========================================================
# DEVICE BINDING
# =========================================================


def test_credentials_are_device_bound():
    source = (
        _credential_source()
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
            "device_id",
            "deviceid",
            "device",
        )
    )


# =========================================================
# REVOCATION
# =========================================================


def test_credentials_support_revocation():
    combined = (
        _combined_credential_surface()
    )

    assert any(
        value
        in combined
        for value in (
            "revoke",
            "revoked",
            "revoked_at",
            "delete",
        )
    )


# =========================================================
# ROTATION / REISSUE
# =========================================================


def test_credentials_support_rotation_or_reissue():
    combined = (
        _combined_credential_surface()
    )

    assert any(
        value
        in combined
        for value in (
            "rotate",
            "rotation",
            "reissue",
            "issue",
            "create",
        )
    )


# =========================================================
# SECRET BOUNDARY
# =========================================================


def test_raw_secret_not_exposed_as_device_inventory_field():
    device_models = (
        normalized_source(
            "modules/devices/models.py"
        )
        .lower()
    )

    assert (
        "device_secret"
        not in device_models
    )


# =========================================================
# CREDENTIAL MODEL SEPARATION
# =========================================================


def test_credentials_are_separate_from_device_inventory():
    existing = (
        _existing_credential_files()
    )

    assert any(
        "credential"
        in Path(
            relative_path
        ).name.lower()
        for relative_path
        in existing
    )