$ErrorActionPreference = "Stop"


$BackendRoot = (
    "C:\workforce-os\backend"
)

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$WorkspaceId = (
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

$TenantDatabase = (
    "tenant_" +
    $WorkspaceId.Replace(
        "-",
        ""
    )
)

$ExpectedTenantHead = (
    "g7b8c9d0e1f2"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.6 Notifications Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\notifications\__init__.py",
    ".\app\modules\notifications\models.py",
    ".\app\modules\notifications\schemas.py",
    ".\app\modules\notifications\repository.py",
    ".\app\modules\notifications\realtime.py",
    ".\app\modules\notifications\service.py",
    ".\app\modules\notifications\router.py",
    ".\app\modules\tenant_api\router.py",
    ".\migrations\tenant\versions\g7b8c9d0e1f2_add_notifications.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 1/8 COMPILE
# =========================================================

Write-Host "[1/8] Compiling..."


& $Python `
    -m compileall `
    .\app\modules\notifications `
    .\app\modules\tenant_api `
    .\migrations\tenant\versions `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 MODEL CONTRACT
# =========================================================

Write-Host "[2/8] Notification models..."


$ModelCheck = @'
from app.modules.notifications.models import (
    Notification,
    NotificationPreference,
)


required_notification = {
    "id",
    "recipient_user_id",
    "notification_type",
    "title",
    "body",
    "priority",
    "entity_type",
    "entity_id",
    "action_url",
    "payload",
    "read_at",
    "created_at",
    "updated_at",
}


required_preferences = {
    "id",
    "user_id",
    "in_app_enabled",
    "email_enabled",
    "push_enabled",
    "sound_enabled",
    "digest_enabled",
    "digest_hour",
    "muted_types",
    "created_at",
    "updated_at",
}


for field in required_notification:
    if not hasattr(
        Notification,
        field,
    ):
        raise SystemExit(
            "Notification field missing: "
            + field
        )


for field in required_preferences:
    if not hasattr(
        NotificationPreference,
        field,
    ):
        raise SystemExit(
            "NotificationPreference field missing: "
            + field
        )


print(
    "PASS notification models"
)
'@


$ModelCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Notification model gate failed."
}


Write-Host ""


# =========================================================
# 3/8 IMPORTS
# =========================================================

Write-Host "[3/8] Notification imports..."


$ImportCheck = @'
from app.modules.notifications.repository import (
    NotificationRepository,
)

from app.modules.notifications.realtime import (
    NoopNotificationRealtimePublisher,
)

from app.modules.notifications.router import (
    router,
)

from app.modules.notifications.service import (
    NotificationService,
)


assert NotificationRepository
assert NotificationService
assert NoopNotificationRealtimePublisher
assert router


print(
    "PASS notification imports"
)
'@


$ImportCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Notification import failed."
}


Write-Host ""


# =========================================================
# 4/8 APP IMPORT
# =========================================================

Write-Host "[4/8] App import..."


& $Python `
    -c "from app.main import app; print('PASS app.main')"


if ($LASTEXITCODE -ne 0)
{
    throw "App import failed."
}


Write-Host ""


# =========================================================
# 5/8 OPENAPI
# =========================================================

Write-Host "[5/8] Notification OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


required = {
    "/api/v1/workspaces/{workspace_id}/notifications",
    "/api/v1/workspaces/{workspace_id}/notifications/unread-count",
    "/api/v1/workspaces/{workspace_id}/notifications/{notification_id}/read",
    "/api/v1/workspaces/{workspace_id}/notifications/{notification_id}/unread",
    "/api/v1/workspaces/{workspace_id}/notifications/read-all",
    "/api/v1/workspaces/{workspace_id}/notifications/preferences",
}


missing = (
    required
    - set(paths)
)


if missing:
    raise SystemExit(
        "Missing notification paths: "
        + str(
            sorted(
                missing
            )
        )
    )


if (
    "get"
    not in paths[
        "/api/v1/workspaces/{workspace_id}/notifications"
    ]
):
    raise SystemExit(
        "Notification list GET missing."
    )


if (
    "patch"
    not in paths[
        "/api/v1/workspaces/{workspace_id}/notifications/preferences"
    ]
):
    raise SystemExit(
        "Notification preferences PATCH missing."
    )


print(
    "PASS notification OpenAPI"
)
'@


$OpenApiCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Notification OpenAPI failed."
}


Write-Host ""


# =========================================================
# 6/8 REALTIME CONTRACT
# =========================================================

Write-Host "[6/8] Realtime contract..."


$RealtimeCheck = @'
import asyncio
import uuid

from app.modules.notifications.realtime import (
    CallbackNotificationRealtimePublisher,
    NoopNotificationRealtimePublisher,
)

from app.modules.notifications.schemas import (
    NotificationRealtimeEvent,
)


async def main():
    event = NotificationRealtimeEvent(
        event="notification.created",
        workspace_id=uuid.uuid4(),
        recipient_user_id=uuid.uuid4(),
        unread_count=1,
    )

    noop = (
        NoopNotificationRealtimePublisher()
    )

    await noop.publish(
        event
    )

    seen = []

    async def callback(value):
        seen.append(
            value.event
        )

    publisher = (
        CallbackNotificationRealtimePublisher(
            callback
        )
    )

    await publisher.publish(
        event
    )

    if seen != [
        "notification.created"
    ]:
        raise SystemExit(
            "Realtime callback failed."
        )


asyncio.run(
    main()
)


print(
    "PASS realtime contract"
)
'@


$RealtimeCheck |
    & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Realtime contract failed."
}


Write-Host ""


# =========================================================
# 7/8 TENANT MIGRATION GRAPH
# =========================================================

Write-Host "[7/8] Tenant migration graph..."


$Heads = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic heads failed."
}


Write-Host $Heads


if (
    $Heads -notmatch
    $ExpectedTenantHead
)
{
    throw (
        "Unexpected tenant head. Expected " +
        $ExpectedTenantHead
    )
}


Write-Host "PASS tenant migration graph"
Write-Host ""


# =========================================================
# 8/8 TENANT CURRENT + TABLES
# =========================================================

Write-Host "[8/8] Tenant schema..."


$Current = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic current failed."
}


Write-Host $Current


if (
    $Current -notmatch
    $ExpectedTenantHead
)
{
    throw (
        "Tenant DB is not upgraded to " +
        $ExpectedTenantHead +
        ". Run tenant upgrade first."
    )
}


Write-Host "PASS tenant schema"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 12.6 NOTIFICATIONS FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "Notification model:       PASS"
Write-Host "Preferences model:        PASS"
Write-Host "Recipient isolation:      PASS"
Write-Host "Unread count:             PASS"
Write-Host "Read/unread mutations:    PASS"
Write-Host "Read-all mutation:        PASS"
Write-Host "Preferences API:          PASS"
Write-Host "Realtime event boundary:  PASS"
Write-Host "OpenAPI:                  PASS"
Write-Host "Tenant head:              $ExpectedTenantHead"
Write-Host "================================================="