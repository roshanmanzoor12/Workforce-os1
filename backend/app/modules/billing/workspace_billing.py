from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import func, select

from app.config import settings
from app.db.tenant import tenant_session, validate_tenant_cluster_key, validate_tenant_database_name
from app.db.tenant_models import TenantMetadata
from app.modules.devices.models import Device
from app.modules.workspaces.models import Workspace, WorkspaceMembership, TenantDatabaseRegistry

from .account_service import AccountBillingService
from .plans import get_plan_definition, PlanCode
from .enums import SubscriptionStatus
from .exemptions import is_billing_exempt


async def workspace_account(db, workspace_id, user_id=None):
    workspace = await db.get(Workspace, workspace_id)
    if workspace is None or not workspace.is_active or workspace.status == "archived":
        raise HTTPException(404, "Workspace not found.")
    if user_id is not None:
        member = await db.scalar(select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "active",
        ))
        if member is None:
            raise HTTPException(403, "Active workspace membership is required.")
    return workspace.created_by_user_id


async def workspace_status(db, workspace_id, user_id):
    owner_id = await workspace_account(db, workspace_id, user_id)
    membership = await db.scalar(select(WorkspaceMembership).where(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user_id,
        WorkspaceMembership.status == "active",
    ))
    role = str(membership.role_key).strip().lower().replace("-", "_").replace(" ", "_")
    manager = role in {"owner", "admin", "senior", "senior_manager"}
    code, status = await AccountBillingService().get_effective_subscription(db, user_id=owner_id)
    exempt = await is_billing_exempt(db, owner_id) or await is_billing_exempt(db, user_id)
    if exempt:
        code, status = PlanCode.BUSINESS, SubscriptionStatus.ACTIVE
    active = status.value in {"active", "trialing"} and code.value != "free"
    plan = get_plan_definition(code)
    plus = code.value in {"professional", "business"}
    return {
        "workspace_id": workspace_id, "plan_code": code, "status": status,
        "can_manage_billing": manager, "restricted": not active,
        "billing_exempt": exempt,
        "features": {
            "payroll": active, "reports": active, "meetings": active,
            "monitoring": active and plan.monitoring_enabled,
            "live_screen": active and plan.live_screen_enabled,
            "channels": active and plus, "ai_assistance": active and plus,
            "advanced_analytics": active and plan.advanced_analytics_enabled,
        },
    }


async def require_workspace_access(db, workspace_id, user_id):
    state = await workspace_status(db, workspace_id, user_id)
    if state['restricted']:
        manager = state['can_manage_billing']
        raise HTTPException(402 if manager else 403, {
            'code': 'WORKSPACE_SUBSCRIPTION_REQUIRED' if manager else 'WORKSPACE_UNAVAILABLE',
            'message': 'Choose or renew a workspace plan to continue.' if manager else 'Workspace access is currently unavailable.',
            'can_manage_billing': manager,
        })
    return state


async def require_workspace_feature(db, workspace_id, user_id, feature):
    """Billing gate supplements RBAC; it never replaces permission checks."""
    result = await workspace_status(db, workspace_id, user_id)
    if not result["features"].get(feature, False):
        raise HTTPException(402, {
            "code": "WORKSPACE_SUBSCRIPTION_REQUIRED",
            "message": "Renew or upgrade the workspace subscription.",
        })


async def count_devices(db, owner_id):
    rows = (await db.execute(select(Workspace, TenantDatabaseRegistry).join(
        TenantDatabaseRegistry, TenantDatabaseRegistry.workspace_id == Workspace.id,
        isouter=True,
    ).where(Workspace.created_by_user_id == owner_id,
            Workspace.is_active.is_(True), Workspace.status != "archived"))).all()
    total = 0
    for workspace, registry in rows:
        if registry is None or registry.status != "ready":
            raise HTTPException(503, "Device allowance cannot be verified while a workspace is not ready.")
        async with tenant_session(
            validate_tenant_database_name(registry.database_name),
            cluster_key=validate_tenant_cluster_key(registry.cluster_key),
        ) as tenant:
            identity = list((await tenant.scalars(select(TenantMetadata))).all())
            if len(identity) != 1 or identity[0].workspace_id != workspace.id or not identity[0].is_active:
                raise HTTPException(503, "Tenant identity could not be verified.")
            # Offline/disabled devices still consume a registered device slot.
            total += int(await tenant.scalar(select(func.count(Device.id)).where(
                Device.status != "revoked",
            )) or 0)
    return total


def device_limit(code):
    return {"starter": 30, "professional": 50,
            "business": settings.billing_advanced_device_limit}.get(code.value)


async def require_device_capacity(db, workspace_id):
    owner_id = await workspace_account(db, workspace_id)
    if await is_billing_exempt(db, owner_id):
        return
    code, status = await AccountBillingService().get_effective_subscription(db, user_id=owner_id)
    if status.value not in {"active", "trialing"}:
        raise HTTPException(402, "The workspace subscription must be renewed.")
    limit = device_limit(code)
    if limit is None:
        raise HTTPException(409, "The device allowance is not configured.")
    if await count_devices(db, owner_id) >= limit:
        raise HTTPException(409, "The billing account device limit has been reached.")
