from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.modules.employee_records.router import router
from app.modules.employee_records.schemas import (
    EmployeeRecordCreateRequest,
    EmployeeRecordUpdateRequest,
)


def test_phase28_create_schema_normalizes_strings() -> None:
    request = EmployeeRecordCreateRequest(
        record_type="personal",
        title="  Home address  ",
        value="  Lahore  ",
        notes="  Primary address  ",
    )

    assert request.title == "Home address"
    assert request.value == "Lahore"
    assert request.notes == "Primary address"


def test_phase28_update_schema_forbids_unknown_fields() -> None:
    with pytest.raises(ValueError):
        EmployeeRecordUpdateRequest(
            title="Address",
            unexpected="value",
        )


def test_phase28_routes_are_registered() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/employee-records/{employee_id}"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/employee-records/record/{record_id}"
        in paths
    )