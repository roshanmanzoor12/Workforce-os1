from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import TenantScope
from app.modules.recruitment.schemas import (
    CandidateCreateRequest,
    CandidateListResponse,
    CandidateResponse,
    CandidateUpdateRequest,
    DeleteResponse,
    InterviewCreateRequest,
    InterviewListResponse,
    InterviewResponse,
    InterviewUpdateRequest,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobUpdateRequest,
)
from app.modules.recruitment.service import RecruitmentService
from app.modules.workspaces.models import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/recruitment",
    tags=["Recruitment"],
)


def service(scope: TenantScope) -> RecruitmentService:
    return RecruitmentService(scope.session)


def require_manager(scope: TenantScope) -> None:
    if scope.role_key not in {
        WORKSPACE_ROLE_OWNER,
        WORKSPACE_ROLE_ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace OWNER or ADMIN role required.",
        )


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    request: JobCreateRequest,
    scope: TenantScope,
) -> JobResponse:
    require_manager(scope)
    return await service(scope).create_job(request)


@router.get(
    "/jobs",
    response_model=JobListResponse,
)
async def list_jobs(
    scope: TenantScope,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
) -> JobListResponse:
    return await service(scope).list_jobs(status_filter)


@router.patch(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
async def update_job(
    job_id: uuid.UUID,
    request: JobUpdateRequest,
    scope: TenantScope,
) -> JobResponse:
    require_manager(scope)
    return await service(scope).update_job(job_id, request)


@router.post(
    "/candidates",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_candidate(
    request: CandidateCreateRequest,
    scope: TenantScope,
) -> CandidateResponse:
    require_manager(scope)
    return await service(scope).create_candidate(request)


@router.get(
    "/candidates",
    response_model=CandidateListResponse,
)
async def list_candidates(
    scope: TenantScope,
    job_id: uuid.UUID | None = None,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
) -> CandidateListResponse:
    return await service(scope).list_candidates(
        job_id=job_id,
        status_filter=status_filter,
    )


@router.patch(
    "/candidates/{candidate_id}",
    response_model=CandidateResponse,
)
async def update_candidate(
    candidate_id: uuid.UUID,
    request: CandidateUpdateRequest,
    scope: TenantScope,
) -> CandidateResponse:
    require_manager(scope)
    return await service(scope).update_candidate(
        candidate_id,
        request,
    )


@router.post(
    "/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview(
    request: InterviewCreateRequest,
    scope: TenantScope,
) -> InterviewResponse:
    require_manager(scope)
    return await service(scope).create_interview(request)


@router.get(
    "/interviews",
    response_model=InterviewListResponse,
)
async def list_interviews(
    scope: TenantScope,
    candidate_id: uuid.UUID | None = None,
) -> InterviewListResponse:
    return await service(scope).list_interviews(candidate_id)


@router.patch(
    "/interviews/{interview_id}",
    response_model=InterviewResponse,
)
async def update_interview(
    interview_id: uuid.UUID,
    request: InterviewUpdateRequest,
    scope: TenantScope,
) -> InterviewResponse:
    require_manager(scope)
    return await service(scope).update_interview(
        interview_id,
        request,
    )


@router.delete(
    "/interviews/{interview_id}",
    response_model=DeleteResponse,
)
async def delete_interview(
    interview_id: uuid.UUID,
    scope: TenantScope,
) -> DeleteResponse:
    require_manager(scope)
    return await service(scope).delete_interview(
        interview_id,
    )


__all__ = ["router"]