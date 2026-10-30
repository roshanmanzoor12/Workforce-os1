from __future__ import annotations

from app.modules.live_monitoring.browser_share_router import router as browser_screen_share_router

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.lifespan import lifespan
from app.modules.billing.access_dependency import enforce_workspace_subscription

from app.middleware.error_handler import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware


# =========================================================
# CONTROL-PLANE ROUTERS
# =========================================================

from app.modules.health.router import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.workspaces.router import router as workspaces_router

from app.modules.workspace_permissions.router import (
    router as workspace_permissions_router,
)
from app.modules.workspace_invitations.router import (
    router as workspace_invitations_router,
)
from app.modules.workspace_rbac.router import router as workspace_rbac_router
from app.modules.memberships.router import router as memberships_router
from app.modules.organizations.router import (
    router as organizations_router,
)
from app.modules.employee_records.router import (
    router as employee_records_router,
)
from app.modules.recruitment.router import (
    router as recruitment_router,
)
from app.modules.employee_lifecycle.router import (
    router as employee_lifecycle_router,
)
from app.modules.performance.router import (
    router as performance_router,
)
from app.modules.discipline.router import (
    router as discipline_router,
)
from app.modules.projects.router import router as projects_router
from app.modules.tasks.router import router as tasks_router

from app.modules.api_keys.authentication_router import (
    router as api_key_authentication_router,
)

from app.modules.api_keys.employee_read_router import (
    router as api_key_employee_read_router,
)
from app.modules.api_keys.self_read_router import (
    router as api_key_self_read_router,
)
from app.modules.personal_social.router import router as personal_social_router

from app.modules.chat.features_router import router as chat_features_router
# =========================================================
# SOCIAL / COMMUNICATION
# =========================================================

from app.modules.friends.router import router as friends_router
from app.modules.chat.router import router as chat_router
from app.modules.chat.pagination_router import (
    router as chat_pagination_router,
)
from app.modules.chat.realtime_router import (
    router as chat_realtime_router,
)
from app.modules.chat.realtime_commands_router import (
    router as chat_realtime_commands_router,
)
from app.modules.channels.router import (
    router as workspace_channels_router,
)
from app.modules.attachments.router import router as attachments_router
from app.modules.attachments.message_router import (
    router as attachment_message_router,
)
from app.modules.calls.router import router as calls_router

from app.modules.voice_channels.router import (
    router as voice_channels_router,
)

# Notification endpoint functions
from app.modules.notifications.router import (
    delete_notification,
    get_notification_preferences,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    mark_notification_unread,
    unread_count,
    update_notification_preferences,
)

from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationMutationResponse,
    NotificationPreferenceResponse,
    NotificationUnreadCountResponse,
)


# =========================================================
# DEVICES
# =========================================================

from app.modules.devices.router import router as devices_router
from app.modules.devices.activation_router import (
    router as device_activation_router,
)
from app.modules.devices.registration_router import (
    router as device_registration_router,
)
from app.modules.devices.credential_router import (
    router as device_credential_router,
)
from app.modules.devices.agent_router import router as device_agent_router
from app.modules.live_monitoring.auto_flow_router import router as live_auto_flow_router
from app.modules.devices.heartbeat_api_router import (
    router as device_heartbeat_api_router,
)


# =========================================================
# EMPLOYEES
# =========================================================

from app.modules.employees.router import router as employees_router


# =========================================================
# ACTIVITY
# =========================================================

from app.modules.activity.activity_api_router import (
    router as activity_api_router,
)
from app.modules.monitoring.router import router as monitoring_router


# =========================================================
# APP TRACKING
# =========================================================

from app.modules.app_tracking.app_tracking_api_router import (
    router as app_tracking_api_router,
)


# =========================================================
# WEBSITE TRACKING
# =========================================================

from app.modules.website_tracking.website_tracking_api_router import (
    router as website_tracking_api_router,
)


# =========================================================
# TENANT API
# =========================================================

from app.modules.tenant_api.router import router as tenant_api_router
from app.modules.api_keys.router import router as api_keys_router


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    dependencies=[Depends(enforce_workspace_subscription)],
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)


# =========================================================
# NOTIFICATION ROUTES
# =========================================================

api_prefix = settings.api_v1_prefix.rstrip("/")
notifications_prefix = f"{api_prefix}/notifications"

app.add_api_route(
    notifications_prefix,
    list_notifications,
    methods=["GET"],
    response_model=NotificationListResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/unread-count",
    unread_count,
    methods=["GET"],
    response_model=NotificationUnreadCountResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/{{notification_id}}/read",
    mark_notification_read,
    methods=["POST"],
    response_model=NotificationMutationResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/{{notification_id}}/unread",
    mark_notification_unread,
    methods=["POST"],
    response_model=NotificationMutationResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/read-all",
    mark_all_notifications_read,
    methods=["POST"],
    response_model=NotificationMarkAllReadResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/{{notification_id}}",
    delete_notification,
    methods=["DELETE"],
    response_model=NotificationMutationResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/preferences",
    get_notification_preferences,
    methods=["GET"],
    response_model=NotificationPreferenceResponse,
    tags=["notifications"],
)

app.add_api_route(
    f"{notifications_prefix}/preferences",
    update_notification_preferences,
    methods=["PATCH"],
    response_model=NotificationPreferenceResponse,
    tags=["notifications"],
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST ID
# =========================================================

app.add_middleware(RequestIDMiddleware)


# =========================================================
# GLOBAL EXCEPTION HANDLERS
# =========================================================

register_exception_handlers(app)


# =========================================================
# CONTROL PLANE
# =========================================================

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    billing_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    workspaces_router,
    prefix=settings.api_v1_prefix,
)


app.include_router(
    workspace_invitations_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    workspace_rbac_router,
    prefix=settings.api_v1_prefix,
)


from app.modules.workspace_rbac.scope_registration import (
    register_membership_scope_routes as _register_membership_scope_routes,
)

_register_membership_scope_routes(
    app,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    memberships_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    organizations_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    employee_records_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    recruitment_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    employee_lifecycle_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    projects_router, 
    prefix=settings.api_v1_prefix
)
app.include_router(
    tasks_router, 
    prefix=settings.api_v1_prefix
)

app.include_router(
    api_key_authentication_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    api_key_employee_read_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    api_key_self_read_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    personal_social_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_features_router,
    prefix=settings.api_v1_prefix,
)
# =========================================================
# SOCIAL / COMMUNICATION
# =========================================================

app.include_router(
    friends_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_pagination_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_realtime_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_realtime_commands_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    workspace_channels_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    attachments_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    attachment_message_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    calls_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    voice_channels_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    performance_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    discipline_router,
    prefix=settings.api_v1_prefix,
)
# =========================================================
# DEVICES
# =========================================================

app.include_router(
    devices_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    device_activation_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    device_registration_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    device_credential_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    device_agent_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    live_auto_flow_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    device_heartbeat_api_router,
    prefix=settings.api_v1_prefix,
)


# =========================================================
# EMPLOYEE API
# =========================================================



# =========================================================
# ACTIVITY
# =========================================================

app.include_router(
    activity_api_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    monitoring_router,
    prefix=settings.api_v1_prefix,
)



# =========================================================
# APP TRACKING
# =========================================================

app.include_router(
    app_tracking_api_router,
    prefix=settings.api_v1_prefix,
)


# =========================================================
# WEBSITE TRACKING
# =========================================================

app.include_router(
    website_tracking_api_router,
    prefix=settings.api_v1_prefix,
)


# =========================================================
# TENANT API
# =========================================================

app.include_router(
    tenant_api_router,
    prefix=settings.api_v1_prefix,
)


app.include_router(
    api_keys_router,
    prefix=settings.api_v1_prefix,
)


# =========================================================
# ROOT
# =========================================================

@app.get(
    "/",
    tags=["Root"],
)
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "status": "running",
    }

# Personal dashboard registration
from app.modules.personal_dashboard.router import router as personal_dashboard_router

app.include_router(
    personal_dashboard_router,
    prefix=settings.api_v1_prefix,
)

# Personal account registration
from app.modules.personal_account.router import router as personal_account_router

app.include_router(
    personal_account_router,
    prefix=settings.api_v1_prefix,
)

# Personal Notes registration
from app.modules.notes.personal_router import (
    router as personal_notes_router,
)

app.include_router(
    personal_notes_router,
    prefix=settings.api_v1_prefix,
)

# Personal Goals registration
from app.modules.goals.personal_router import (
    router as personal_goals_router,
)

app.include_router(
    personal_goals_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(browser_screen_share_router, prefix=settings.api_v1_prefix)

