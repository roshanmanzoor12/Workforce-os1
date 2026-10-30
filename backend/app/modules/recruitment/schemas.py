from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class RecruitmentSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class JobStatusValue(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class CandidateStatusValue(StrEnum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InterviewStatusValue(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class JobCreateRequest(RecruitmentSchema):
    title: str = Field(min_length=2, max_length=150)
    department_id: uuid.UUID | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=50)
    closing_date: datetime | None = None

    @field_validator("title", "description", "location", "employment_type")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class JobUpdateRequest(RecruitmentSchema):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    department_id: uuid.UUID | None = None
    description: str | None = None
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=50)
    closing_date: datetime | None = None
    status: JobStatusValue | None = None


class JobResponse(RecruitmentSchema):
    id: uuid.UUID
    title: str
    department_id: uuid.UUID | None
    description: str | None
    location: str | None
    employment_type: str | None
    closing_date: datetime | None
    status: JobStatusValue


class JobListResponse(RecruitmentSchema):
    items: list[JobResponse] = Field(default_factory=list)
    total: int = Field(ge=0)


class CandidateCreateRequest(RecruitmentSchema):
    job_id: uuid.UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    resume_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None

    @field_validator("first_name", "last_name", "phone", "resume_url", "notes")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class CandidateUpdateRequest(RecruitmentSchema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    resume_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    status: CandidateStatusValue | None = None


class CandidateResponse(RecruitmentSchema):
    id: uuid.UUID
    job_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    resume_url: str | None
    notes: str | None
    status: CandidateStatusValue


class CandidateListResponse(RecruitmentSchema):
    items: list[CandidateResponse] = Field(default_factory=list)
    total: int = Field(ge=0)


class InterviewCreateRequest(RecruitmentSchema):
    candidate_id: uuid.UUID
    interviewer_user_id: uuid.UUID | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    notes: str | None = None


class InterviewUpdateRequest(RecruitmentSchema):
    interviewer_user_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: InterviewStatusValue | None = None
    notes: str | None = None


class InterviewResponse(RecruitmentSchema):
    id: uuid.UUID
    candidate_id: uuid.UUID
    interviewer_user_id: uuid.UUID | None
    starts_at: datetime
    ends_at: datetime | None
    status: InterviewStatusValue
    notes: str | None


class InterviewListResponse(RecruitmentSchema):
    items: list[InterviewResponse] = Field(default_factory=list)
    total: int = Field(ge=0)


class DeleteResponse(RecruitmentSchema):
    success: bool
    message: str