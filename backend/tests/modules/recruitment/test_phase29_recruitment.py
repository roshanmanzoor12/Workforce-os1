from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.modules.recruitment.router import router
from app.modules.recruitment.schemas import (
    CandidateCreateRequest,
    InterviewCreateRequest,
    JobCreateRequest,
)


def test_phase29_job_schema() -> None:
    request = JobCreateRequest(
        title="  Backend Engineer  ",
        description="  Build APIs  ",
    )

    assert request.title == "Backend Engineer"
    assert request.description == "Build APIs"


def test_phase29_candidate_schema() -> None:
    job_id = uuid.uuid4()

    request = CandidateCreateRequest(
        job_id=job_id,
        first_name="  Ali  ",
        last_name="  Khan  ",
        email="ali@example.com",
    )

    assert request.job_id == job_id
    assert request.first_name == "Ali"
    assert request.last_name == "Khan"


def test_phase29_interview_schema() -> None:
    candidate_id = uuid.uuid4()
    starts_at = datetime.now(timezone.utc)

    request = InterviewCreateRequest(
        candidate_id=candidate_id,
        starts_at=starts_at,
    )

    assert request.candidate_id == candidate_id
    assert request.starts_at == starts_at


def test_phase29_routes_registered() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/recruitment/jobs"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/recruitment/candidates"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}/recruitment/interviews"
        in paths
    )


def test_phase29_unknown_fields_rejected() -> None:
    with pytest.raises(ValueError):
        JobCreateRequest(
            title="Engineer",
            unknown_field="invalid",
        )