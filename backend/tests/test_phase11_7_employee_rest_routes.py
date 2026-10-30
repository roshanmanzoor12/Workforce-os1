from __future__ import annotations

from app.main import app


def test_employee_rest_routes_exist(
) -> None:
    paths = app.openapi()["paths"]

    expected = {
        (
            "/api/v1/workspaces/"
            "{workspace_id}/departments"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/departments/"
            "{department_id}"
        ): {
            "get",
            "patch",
            "delete",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/teams"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/teams/{team_id}"
        ): {
            "get",
            "patch",
            "delete",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/employees"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/employees/"
            "{employee_id}"
        ): {
            "get",
            "patch",
            "delete",
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