from __future__ import annotations

from app.modules.holidays.repository import (
    HolidayRepository,
)
from app.modules.holidays.service import (
    HolidayService,
)


def test_repository_has_workspace_resolver():
    assert hasattr(
        HolidayRepository,
        "workspace_for_date",
    )


def test_service_has_workspace_resolver():
    assert hasattr(
        HolidayService,
        (
            "resolve_workspace_"
            "holiday_for_date"
        ),
    )


def test_workspace_resolver_is_distinct_from_generic_resolver():
    assert (
        HolidayRepository.for_date
        is not
        HolidayRepository.workspace_for_date
    )