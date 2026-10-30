from __future__ import annotations

from app.main import app


def test_final_phase11_7_openapi_contract(
) -> None:
    paths = app.openapi().get(
        "paths",
        {},
    )

    expected = {
        (
            "/api/v1/workspace-memberships/"
            "{workspace_id}/bootstrap-owner"
        ): {
            "post",
        },
        (
            "/api/v1/workspace-memberships/"
            "{workspace_id}/me"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/departments"
        ): {
            "get",
            "post",
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
            "{workspace_id}/employees"
        ): {
            "get",
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "records"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "employees/{employee_id}/events"
        ): {
            "post",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/attendance/"
            "employees/{employee_id}/summary"
        ): {
            "get",
        },
    }

    for path, required_methods in (
        expected.items()
    ):
        assert path in paths

        actual_methods = {
            method.lower()
            for method
            in paths[path].keys()
        }

        assert (
            required_methods
            .issubset(
                actual_methods
            )
        )