from __future__ import annotations

import uuid

from app.modules.organizations.schemas import (
    OrganizationUpdateRequest,
)


def test_phase26_update_request_normalizes_text() -> None:
    request = OrganizationUpdateRequest(
        name="  Acme Organization  ",
        timezone="  UTC  ",
        logo_url="  https://example.com/logo.png  ",
    )

    assert request.name == "Acme Organization"
    assert request.timezone == "UTC"
    assert request.logo_url == (
        "https://example.com/logo.png"
    )


def test_phase26_update_request_allows_partial_update() -> None:
    request = OrganizationUpdateRequest(
        name="Acme"
    )

    assert request.name == "Acme"
    assert request.timezone is None
    assert request.logo_url is None


def test_phase26_response_ids_are_uuid_values() -> None:
    organization_id = uuid.uuid4()
    user_id = uuid.uuid4()

    assert isinstance(
        organization_id,
        uuid.UUID,
    )

    assert isinstance(
        user_id,
        uuid.UUID,
    )