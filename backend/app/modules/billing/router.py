from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .access_schemas import (
    WorkspaceCreationAccessResponse,
)
from .api_schemas import (
    AccountEntitlementsPublic,
    BillingPlansResponse,
    CurrentSubscriptionPublic,
)
from .api_service import BillingAPIService


router = APIRouter(
    prefix="/billing",
    tags=["Billing"],
)


ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


VerifiedUser = Annotated[
    User,
    Depends(get_current_verified_user),
]


def get_billing_api_service(
    db: ControlDB,
) -> BillingAPIService:
    return BillingAPIService(
        db
    )


BillingAPI = Annotated[
    BillingAPIService,
    Depends(get_billing_api_service),
]


@router.get(
    "/plans",
    response_model=BillingPlansResponse,
    status_code=status.HTTP_200_OK,
    summary="List WorkforceOS plans",
)
async def list_plans(
    billing: BillingAPI,
) -> BillingPlansResponse:
    return billing.list_plans()


@router.get(
    "/subscription",
    response_model=CurrentSubscriptionPublic,
    status_code=status.HTTP_200_OK,
    summary="Get current account subscription",
)
async def get_current_subscription(
    billing: BillingAPI,
    current_user: VerifiedUser,
) -> CurrentSubscriptionPublic:
    return await billing.get_current_subscription(
        user_id=current_user.id
    )


@router.get(
    "/entitlements",
    response_model=AccountEntitlementsPublic,
    status_code=status.HTTP_200_OK,
    summary="Get current account entitlements",
)
async def get_current_entitlements(
    billing: BillingAPI,
    current_user: VerifiedUser,
) -> AccountEntitlementsPublic:
    return await billing.get_current_entitlements(
        user_id=current_user.id
    )


@router.get(
    "/workspace-access",
    response_model=WorkspaceCreationAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check workspace creation access",
)
async def get_workspace_creation_access(
    billing: BillingAPI,
    current_user: VerifiedUser,
) -> WorkspaceCreationAccessResponse:
    return await billing.get_workspace_creation_access(
        user_id=current_user.id
    )


__all__ = [
    "router",
]


from .payments_router import router as payments_router

router.include_router(payments_router)
