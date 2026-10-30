from uuid import uuid4

import pytest

from app.modules.discipline.models import (
    DisciplinaryIncident,
)
from app.modules.discipline.router import router
from app.modules.discipline.schemas import (
    IncidentCreate,
    IncidentUpdate,
)


def test_discipline_routes_exist() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/discipline/incidents"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/discipline/incidents/{incident_id}"
        in paths
    )


def test_discipline_table_name() -> None:
    assert (
        DisciplinaryIncident.__tablename__
        == "disciplinary_incidents"
    )


def test_valid_incident() -> None:
    incident = IncidentCreate(
        employee_id=uuid4(),
        category="attendance",
        summary="Repeated late arrivals.",
    )

    assert incident.employee_id is not None
    assert incident.category == "attendance"
    assert incident.summary == (
        "Repeated late arrivals."
    )


def test_incident_requires_summary() -> None:
    with pytest.raises(ValueError):
        IncidentCreate(
            employee_id=uuid4(),
            category="policy",
        )


def test_incident_update() -> None:
    update = IncidentUpdate(
        status="resolved",
    )

    assert update.status == "resolved"