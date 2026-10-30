from __future__ import annotations

from app.main import app


def test_attendance_rest_routes_exist(
) -> None:
    paths = app.openapi()["paths"]

    expected = {
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "employees/{employee_id}/events"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/records"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "records/{attendance_record_id}"
        ): {
            "get",
            "patch",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "employees/{employee_id}/summary"
        ): {
            "get",
        },
    }

    for path, methods in expected.items():
        assert path in paths

        actual = {
            key.lower()
            for key
            in paths[path].keys()
        }

        assert methods.issubset(
            actual
        )