from __future__ import annotations

from app.db.tenant_base import (
    TenantBase,
)
from app.main import app
from app.modules.meetings.enums import (
    MeetingStatus,
    MeetingType,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_meeting_is_tenant_scoped(
) -> None:
    assert issubclass(
        Meeting,
        TenantBase,
    )


def test_participant_is_tenant_scoped(
) -> None:
    assert issubclass(
        MeetingParticipant,
        TenantBase,
    )


def test_meeting_tables(
) -> None:
    assert (
        Meeting.__tablename__
        == "meetings"
    )

    assert (
        MeetingParticipant.__tablename__
        == "meeting_participants"
    )


def test_meeting_has_required_columns(
) -> None:
    columns = {
        column.name
        for column
        in Meeting.__table__.columns
    }

    required = {
        "id",
        "title",
        "description",
        "meeting_type",
        "status",
        "scheduled_start_at",
        "scheduled_end_at",
        "started_at",
        "ended_at",
        "location",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )


def test_participant_has_employee_fk(
) -> None:
    targets = {
        fk.target_fullname
        for fk
        in MeetingParticipant
        .__table__
        .columns["employee_id"]
        .foreign_keys
    }

    assert (
        "employees.id"
        in targets
    )


def test_participant_has_meeting_fk(
) -> None:
    targets = {
        fk.target_fullname
        for fk
        in MeetingParticipant
        .__table__
        .columns["meeting_id"]
        .foreign_keys
    }

    assert (
        "meetings.id"
        in targets
    )


def test_meeting_status_values(
) -> None:
    assert (
        MeetingStatus.SCHEDULED.value
        == "scheduled"
    )

    assert (
        MeetingStatus.ACTIVE.value
        == "active"
    )

    assert (
        MeetingStatus.COMPLETED.value
        == "completed"
    )

    assert (
        MeetingStatus.CANCELLED.value
        == "cancelled"
    )


def test_meeting_type_values(
) -> None:
    assert (
        MeetingType.VIDEO.value
        == "video"
    )

    assert (
        MeetingType.VOICE.value
        == "voice"
    )

    assert (
        MeetingType.IN_PERSON.value
        == "in_person"
    )


def test_member_can_create_meeting(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MEETINGS_CREATE
                .value
            ),
        )
    )


def test_member_cannot_manage_meeting(
) -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MEETINGS_MANAGE
                .value
            ),
        )
    )


def test_admin_can_manage_meeting(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .MEETINGS_MANAGE
                .value
            ),
        )
    )


def test_meeting_routes_exist(
) -> None:
    paths = app.openapi().get(
        "paths",
        {},
    )

    expected = {
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}"
        ): {
            "get",
            "patch",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/start"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/end"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/cancel"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/participants"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/participants/"
            "{employee_id}"
        ): {
            "delete",
        },
    }

    for path, methods in expected.items():
        assert path in paths

        actual = {
            method.lower()
            for method
            in paths[path].keys()
        }

        assert methods.issubset(
            actual
        )


def test_permissions_routes_exist(
) -> None:
    paths = app.openapi().get(
        "paths",
        {},
    )

    expected = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/permissions/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/permissions/check"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/permissions/catalog"
        ),
    ]

    for path in expected:
        assert path in paths