from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.modules.rules.permissions import (
    require_rules_access,
)
from app.modules.rules.schemas import (
    RuleCreate,
    RulePublic,
)
from app.modules.rules.service import (
    RuleNotFoundError,
    RulesService,
    RuleValidationError,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/rules",
    tags=["rules"],
)

_service = RulesService()


@router.get(
    "",
    response_model=list[RulePublic],
)
async def list_rules(
    workspace_id: UUID,
) -> list[RulePublic]:
    require_rules_access()

    items = await _service.list_rules(workspace_id)

    return [
        RulePublic.model_validate(item)
        for item in items
    ]


@router.post(
    "",
    response_model=RulePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    workspace_id: UUID,
    request: RuleCreate,
) -> RulePublic:
    require_rules_access()

    item = await _service.create_rule(
        workspace_id=workspace_id,
        name=request.name,
        event_type=request.event_type,
        conditions=[
            condition.model_dump()
            for condition in request.conditions
        ],
        actions=[
            action.model_dump()
            for action in request.actions
        ],
    )

    return RulePublic.model_validate(item)


@router.get(
    "/{rule_id}",
    response_model=RulePublic,
)
async def get_rule(
    workspace_id: UUID,
    rule_id: UUID,
) -> RulePublic:
    require_rules_access()

    try:
        item = await _service.get_rule(
            workspace_id,
            rule_id,
        )
    except RuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return RulePublic.model_validate(item)


@router.post(
    "/{rule_id}/enable",
    response_model=RulePublic,
)
async def enable_rule(
    workspace_id: UUID,
    rule_id: UUID,
) -> RulePublic:
    require_rules_access()

    try:
        item = await _service.set_enabled(
            workspace_id=workspace_id,
            rule_id=rule_id,
            is_enabled=True,
        )
    except RuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return RulePublic.model_validate(item)


@router.post(
    "/{rule_id}/disable",
    response_model=RulePublic,
)
async def disable_rule(
    workspace_id: UUID,
    rule_id: UUID,
) -> RulePublic:
    require_rules_access()

    try:
        item = await _service.set_enabled(
            workspace_id=workspace_id,
            rule_id=rule_id,
            is_enabled=False,
        )
    except RuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return RulePublic.model_validate(item)