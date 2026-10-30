from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.holidays.models import (
    HolidayTreatment,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# CREATE
# =========================================================


class HolidayCreateRequest(
    BaseModel
):
    holiday_date: date

    name: str = Field(
        min_length=1,
        max_length=160,
    )

    treatment: HolidayTreatment = (
        HolidayTreatment.PAID
    )

    region: str | None = Field(
        default=None,
        max_length=120,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


# =========================================================
# UPDATE
# =========================================================


class HolidayUpdateRequest(
    BaseModel
):
    holiday_date: (
        date | None
    ) = None

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )

    treatment: (
        HolidayTreatment
        | None
    ) = None

    region: str | None = Field(
        default=None,
        max_length=120,
    )

    description: (
        str | None
    ) = Field(
        default=None,
        max_length=500,
    )

    is_active: (
        bool | None
    ) = None


# =========================================================
# RESPONSE
# =========================================================


class HolidayResponse(
    ORMModel
):
    id: uuid.UUID

    holiday_date: date

    name: str

    treatment: HolidayTreatment

    region: str | None

    description: str | None

    is_active: bool

    created_by_user_id: (
        uuid.UUID | None
    )

    created_at: datetime

    updated_at: datetime


__all__ = [
    "HolidayCreateRequest",
    "HolidayUpdateRequest",
    "HolidayResponse",
]