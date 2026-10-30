from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recruitment.models import (
    Candidate,
    CandidateStatus,
    Interview,
    JobPosting,
)
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


class RecruitmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(
        self,
        request: JobCreateRequest,
    ) -> JobResponse:
        job = JobPosting(**request.model_dump())
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return JobResponse.model_validate(job)

    async def list_jobs(
        self,
        status_filter: str | None = None,
    ) -> JobListResponse:
        statement = select(JobPosting)

        if status_filter:
            statement = statement.where(
                JobPosting.status == status_filter,
            )

        statement = statement.order_by(
            JobPosting.created_at.desc(),
        )

        result = await self.session.execute(statement)
        items = list(result.scalars().all())

        return JobListResponse(
            items=[
                JobResponse.model_validate(item)
                for item in items
            ],
            total=len(items),
        )

    async def update_job(
        self,
        job_id: uuid.UUID,
        request: JobUpdateRequest,
    ) -> JobResponse:
        job = await self.session.get(JobPosting, job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )

        for key, value in request.model_dump(
            exclude_unset=True,
        ).items():
            setattr(job, key, value)

        await self.session.commit()
        await self.session.refresh(job)

        return JobResponse.model_validate(job)

    async def create_candidate(
        self,
        request: CandidateCreateRequest,
    ) -> CandidateResponse:
        job = await self.session.get(
            JobPosting,
            request.job_id,
        )

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting was not found.",
            )

        candidate = Candidate(
            **request.model_dump(
                mode="json",
            ),
        )

        self.session.add(candidate)
        await self.session.commit()
        await self.session.refresh(candidate)

        return CandidateResponse.model_validate(candidate)

    async def list_candidates(
        self,
        job_id: uuid.UUID | None = None,
        status_filter: str | None = None,
    ) -> CandidateListResponse:
        statement = select(Candidate)

        if job_id is not None:
            statement = statement.where(
                Candidate.job_id == job_id,
            )

        if status_filter:
            statement = statement.where(
                Candidate.status == status_filter,
            )

        statement = statement.order_by(
            Candidate.created_at.desc(),
        )

        result = await self.session.execute(statement)
        items = list(result.scalars().all())

        return CandidateListResponse(
            items=[
                CandidateResponse.model_validate(item)
                for item in items
            ],
            total=len(items),
        )

    async def update_candidate(
        self,
        candidate_id: uuid.UUID,
        request: CandidateUpdateRequest,
    ) -> CandidateResponse:
        candidate = await self.session.get(
            Candidate,
            candidate_id,
        )

        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate was not found.",
            )

        for key, value in request.model_dump(
            exclude_unset=True,
            mode="json",
        ).items():
            setattr(candidate, key, value)

        await self.session.commit()
        await self.session.refresh(candidate)

        return CandidateResponse.model_validate(candidate)

    async def create_interview(
        self,
        request: InterviewCreateRequest,
    ) -> InterviewResponse:
        candidate = await self.session.get(
            Candidate,
            request.candidate_id,
        )

        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate was not found.",
            )

        interview = Interview(**request.model_dump())
        self.session.add(interview)
        await self.session.commit()
        await self.session.refresh(interview)

        return InterviewResponse.model_validate(interview)

    async def list_interviews(
        self,
        candidate_id: uuid.UUID | None = None,
    ) -> InterviewListResponse:
        statement = select(Interview)

        if candidate_id is not None:
            statement = statement.where(
                Interview.candidate_id == candidate_id,
            )

        statement = statement.order_by(
            Interview.starts_at.asc(),
        )

        result = await self.session.execute(statement)
        items = list(result.scalars().all())

        return InterviewListResponse(
            items=[
                InterviewResponse.model_validate(item)
                for item in items
            ],
            total=len(items),
        )

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        request: InterviewUpdateRequest,
    ) -> InterviewResponse:
        interview = await self.session.get(
            Interview,
            interview_id,
        )

        if interview is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview was not found.",
            )

        for key, value in request.model_dump(
            exclude_unset=True,
        ).items():
            setattr(interview, key, value)

        await self.session.commit()
        await self.session.refresh(interview)

        return InterviewResponse.model_validate(interview)

    async def delete_interview(
        self,
        interview_id: uuid.UUID,
    ) -> DeleteResponse:
        interview = await self.session.get(
            Interview,
            interview_id,
        )

        if interview is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview was not found.",
            )

        await self.session.delete(interview)
        await self.session.commit()

        return DeleteResponse(
            success=True,
            message="Interview deleted.",
        )