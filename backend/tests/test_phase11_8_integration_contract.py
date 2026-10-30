from __future__ import annotations

from pathlib import Path

from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)


def test_meeting_models_remain_tenant_isolated(
) -> None:
    for model in (
        Meeting,
        MeetingParticipant,
    ):
        columns = {
            column.name
            for column
            in model.__table__.columns
        }

        assert (
            "workspace_id"
            not in columns
        )


def test_meeting_self_response_uses_employee_user_link(
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


def test_self_response_does_not_accept_employee_id_from_payload(
) -> None:
    text = Path(
        "app/modules/meetings/"
        "self_schemas.py"
    ).read_text(
        encoding="utf-8",
    )

    request_section = text.split(
        "class MeetingSelfResponseRequest",
        1,
    )[1].split(
        "class MeetingSelfResponseResult",
        1,
    )[0]

    assert (
        "employee_id"
        not in request_section
    )


def test_monitoring_control_is_permission_only(
) -> None:
    text = Path(
        "app/modules/monitoring_control/"
        "service.py"
    ).read_text(
        encoding="utf-8",
    ).lower()

    forbidden = [
        "capture_keystrokes",
        "capture_clipboard",
        "capture_password",
        "capture_typed_text",
        "mouse_coordinates =",
        "stealth_mode = true",
    ]

    for token in forbidden:
        assert token not in text


def test_monitoring_control_uses_workspace_permissions(
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


def test_tenant_api_wires_phase11_8_routes(
) -> None:
    text = Path(
        "app/modules/tenant_api/router.py"
    ).read_text(
        encoding="utf-8",
    )

    required = [
        "workspace_permissions_router",
        "meetings_self_router",
        "meetings_router",
        "monitoring_control_router",
    ]

    for token in required:
        assert token in text