from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    EMPLOYMENT_STATUS_ON_LEAVE,
    EMPLOYMENT_STATUS_SUSPENDED,
    EMPLOYMENT_STATUS_TERMINATED,
)


# =========================================================
# SHARED TYPES
# =========================================================


EmploymentStatus = Literal[
    "active",
    "on_leave",
    "suspended",
    "terminated",
]


# =========================================================
# BASE CONFIG
# =========================================================


class EmployeeSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# =========================================================
# DEPARTMENT REQUESTS
# =========================================================


class DepartmentCreateRequest(
    EmployeeSchemaBase
):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "name",
        "code",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_department_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


class DepartmentUpdateRequest(
    EmployeeSchemaBase
):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    is_active: bool | None = None

    @field_validator(
        "name",
        "code",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_department_update_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


# =========================================================
# TEAM REQUESTS
# =========================================================


class TeamCreateRequest(
    EmployeeSchemaBase
):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    department_id: uuid.UUID | None = None

    @field_validator(
        "name",
        "code",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_team_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


class TeamUpdateRequest(
    EmployeeSchemaBase
):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    department_id: uuid.UUID | None = None

    is_active: bool | None = None

    @field_validator(
        "name",
        "code",
        "description",
        mode="before",
    )
    @classmethod
    def normalize_team_update_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


# =========================================================
# EMPLOYEE REQUESTS
# =========================================================


class EmployeeCreateRequest(
    EmployeeSchemaBase
):
    user_id: uuid.UUID | None = None

    employee_code: str = Field(
        min_length=1,
        max_length=50,
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    work_email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=50,
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    job_title: str | None = Field(
        default=None,
        max_length=150,
    )

    employment_status: EmploymentStatus = (
        EMPLOYMENT_STATUS_ACTIVE
    )

    hire_date: date | None = None
    termination_date: date | None = None

    department_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None

    @field_validator(
        "employee_code",
        "first_name",
        "last_name",
        "phone_number",
        "avatar_url",
        "job_title",
        mode="before",
    )
    @classmethod
    def normalize_employee_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @field_validator(
        "work_email",
        mode="before",
    )
    @classmethod
    def normalize_work_email(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = (
            value
            .strip()
            .lower()
        )

        if not normalized:
            return None

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_employment_dates(
        self,
    ) -> EmployeeCreateRequest:
        if (
            self.hire_date is not None
            and self.termination_date is not None
            and self.termination_date
            < self.hire_date
        ):
            raise ValueError(
                "termination_date cannot be before hire_date."
            )

        if (
            self.employment_status
            == EMPLOYMENT_STATUS_TERMINATED
            and self.termination_date is None
        ):
            raise ValueError(
                "termination_date is required when employment_status is terminated."
            )

        return self


class EmployeeUpdateRequest(
    EmployeeSchemaBase
):
    user_id: uuid.UUID | None = None

    employee_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    work_email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=50,
    )

    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    job_title: str | None = Field(
        default=None,
        max_length=150,
    )

    employment_status: EmploymentStatus | None = None

    hire_date: date | None = None
    termination_date: date | None = None

    department_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None

    is_active: bool | None = None

    @field_validator(
        "employee_code",
        "first_name",
        "last_name",
        "phone_number",
        "avatar_url",
        "job_title",
        mode="before",
    )
    @classmethod
    def normalize_employee_update_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @field_validator(
        "work_email",
        mode="before",
    )
    @classmethod
    def normalize_employee_update_email(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = (
            value
            .strip()
            .lower()
        )

        if not normalized:
            return None

        return normalized

    @model_validator(
        mode="after",
    )
    def validate_update_dates(
        self,
    ) -> EmployeeUpdateRequest:
        if (
            self.hire_date is not None
            and self.termination_date is not None
            and self.termination_date
            < self.hire_date
        ):
            raise ValueError(
                "termination_date cannot be before hire_date."
            )

        return self


# =========================================================
# PUBLIC DEPARTMENT
# =========================================================


class DepartmentPublic(
    EmployeeSchemaBase
):
    id: uuid.UUID

    name: str
    code: str | None
    description: str | None

    is_active: bool

    created_at: datetime
    updated_at: datetime


# =========================================================
# PUBLIC TEAM
# =========================================================


class TeamPublic(
    EmployeeSchemaBase
):
    id: uuid.UUID

    name: str
    code: str | None
    description: str | None

    department_id: uuid.UUID | None

    is_active: bool

    created_at: datetime
    updated_at: datetime


# =========================================================
# PUBLIC EMPLOYEE
# =========================================================


class EmployeePublic(
    EmployeeSchemaBase
):
    id: uuid.UUID

    user_id: uuid.UUID | None

    employee_code: str

    first_name: str
    last_name: str
    full_name: str

    work_email: EmailStr | None
    phone_number: str | None
    avatar_url: str | None

    job_title: str | None

    employment_status: EmploymentStatus

    hire_date: date | None
    termination_date: date | None

    department_id: uuid.UUID | None
    team_id: uuid.UUID | None
    manager_id: uuid.UUID | None

    is_active: bool

    created_at: datetime
    updated_at: datetime


# =========================================================
# EXPANDED EMPLOYEE
# =========================================================


class EmployeeDetailResponse(
    EmployeeSchemaBase
):
    employee: EmployeePublic

    department: DepartmentPublic | None = None
    team: TeamPublic | None = None
    manager: EmployeePublic | None = None


# =========================================================
# CREATE / UPDATE RESPONSES
# =========================================================


class DepartmentResponse(
    EmployeeSchemaBase
):
    message: str
    department: DepartmentPublic


class TeamResponse(
    EmployeeSchemaBase
):
    message: str
    team: TeamPublic


class EmployeeResponse(
    EmployeeSchemaBase
):
    message: str
    employee: EmployeePublic


# =========================================================
# LIST RESPONSES
# =========================================================


class DepartmentListResponse(
    EmployeeSchemaBase
):
    departments: list[
        DepartmentPublic
    ]

    total: int = Field(
        ge=0,
    )


class TeamListResponse(
    EmployeeSchemaBase
):
    teams: list[
        TeamPublic
    ]

    total: int = Field(
        ge=0,
    )


class EmployeeListResponse(
    EmployeeSchemaBase
):
    employees: list[
        EmployeePublic
    ]

    total: int = Field(
        ge=0,
    )


# =========================================================
# STATUS / DELETE RESPONSES
# =========================================================


class EmployeeDeleteResponse(
    EmployeeSchemaBase
):
    message: str
    success: bool


class DepartmentDeleteResponse(
    EmployeeSchemaBase
):
    message: str
    success: bool


class TeamDeleteResponse(
    EmployeeSchemaBase
):
    message: str
    success: bool


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "EmploymentStatus",
    "DepartmentCreateRequest",
    "DepartmentUpdateRequest",
    "TeamCreateRequest",
    "TeamUpdateRequest",
    "EmployeeCreateRequest",
    "EmployeeUpdateRequest",
    "DepartmentPublic",
    "TeamPublic",
    "EmployeePublic",
    "EmployeeDetailResponse",
    "DepartmentResponse",
    "TeamResponse",
    "EmployeeResponse",
    "DepartmentListResponse",
    "TeamListResponse",
    "EmployeeListResponse",
    "EmployeeDeleteResponse",
    "DepartmentDeleteResponse",
    "TeamDeleteResponse",
]