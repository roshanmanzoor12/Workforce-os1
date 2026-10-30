from __future__ import annotations

from pathlib import Path


ROOTS = [
    Path(
        "app/modules/meetings"
    ),
    Path(
        "app/modules/monitoring_control"
    ),
    Path(
        "app/modules/workspace_permissions"
    ),
]


def test_phase11_8_has_no_database_credentials(
) -> None:
    forbidden = [
        "postgresql://",
        "asyncpg://",
        "tenant_password",
        "database_password",
        "connection_string =",
    ]

    for root in ROOTS:
        for path in root.rglob(
            "*.py"
        ):
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            for token in forbidden:
                assert (
                    token
                    not in text
                )


def test_phase11_8_has_no_invasive_capture(
) -> None:
    forbidden = [
        "capture_keystrokes",
        "record_keystrokes",
        "capture_clipboard",
        "clipboard_contents",
        "capture_password",
        "password_contents",
        "capture_typed_text",
        "record_typed_text",
        "mouse_coordinates =",
        "stealth_mode = true",
    ]

    for root in ROOTS:
        for path in root.rglob(
            "*.py"
        ):
            text = path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            for token in forbidden:
                assert (
                    token
                    not in text
                )


def test_meeting_self_identity_is_backend_derived(
) -> None:
    text = Path(
        "app/modules/meetings/"
        "self_service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "Employee.user_id"
        in text
    )

    assert (
        "actor_user_id"
        in text
    )


def test_monitoring_uses_permission_service(
) -> None:
    text = Path(
        "app/modules/monitoring_control/"
        "service.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "WorkspacePermissionService"
        in text
    )

    assert (
        "TenantScope"
        in text
    )