from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.modules.plans.schemas import (
    LimitCheckRequest,
    LimitCheckResponse,
    PlanCreate,
    PlanPublic,
    PlanUpdate,
)
from app.modules.plans.service import (
    DuplicatePlanCodeError,
    PlanNotFoundError,
    PlanService,
)

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
)

_service = PlanService()


@router.get("", response_model=list[PlanPublic])
def list_plans(
    active_only: bool = Query(default=False),
) -> list[PlanPublic]:
    return [
        PlanPublic.model_validate(plan)
        for plan in _service.list_plans(active_only=active_only)
    ]


@router.post(
    "",
    response_model=PlanPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(payload: PlanCreate) -> PlanPublic:
    try:
        plan = _service.create_plan(payload)
    except DuplicatePlanCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return PlanPublic.model_validate(plan)


@router.get("/{plan_id}", response_model=PlanPublic)
def get_plan(plan_id: UUID) -> PlanPublic:
    try:
        plan = _service.get_plan(plan_id)
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return PlanPublic.model_validate(plan)


@router.patch("/{plan_id}", response_model=PlanPublic)
def update_plan(plan_id: UUID, payload: PlanUpdate) -> PlanPublic:
    try:
        plan = _service.update_plan(plan_id, payload)
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return PlanPublic.model_validate(plan)


@router.post("/{plan_id}/activate", response_model=PlanPublic)
def activate_plan(plan_id: UUID) -> PlanPublic:
    try:
        plan = _service.set_active(plan_id, True)
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return PlanPublic.model_validate(plan)


@router.post("/{plan_id}/deactivate", response_model=PlanPublic)
def deactivate_plan(plan_id: UUID) -> PlanPublic:
    try:
        plan = _service.set_active(plan_id, False)
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return PlanPublic.model_validate(plan)


@router.post(
    "/{plan_id}/check-limit",
    response_model=LimitCheckResponse,
)
def check_plan_limit(
    plan_id: UUID,
    payload: LimitCheckRequest,
) -> LimitCheckResponse:
    try:
        configured_limit, allowed = _service.check_limit(
            plan_id,
            feature=payload.feature,
            current_usage=payload.current_usage,
        )
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return LimitCheckResponse(
        plan_id=plan_id,
        feature=payload.feature,
        current_usage=payload.current_usage,
        configured_limit=configured_limit,
        allowed=allowed,
    )