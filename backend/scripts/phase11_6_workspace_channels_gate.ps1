$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Workspace Channels Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# PREFLIGHT
# =========================================================

Write-Host "[preflight] PostgreSQL 5434..."

$DbPort = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $DbPort.TcpTestSucceeded)
{
    throw "PostgreSQL 127.0.0.1:5434 unavailable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/6] Compiling..."

& $Python `
    -m py_compile `
    .\app\modules\channels\enums.py `
    .\app\modules\channels\models.py `
    .\app\modules\channels\schemas.py `
    .\app\modules\channels\repository.py `
    .\app\modules\channels\service.py `
    .\app\modules\channels\router.py `
    .\migrations\control\versions\a6b7c8d9e0f1_add_workspace_channels.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channels compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/6] Social/channel tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    .\tests\modules\channels `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel tests failed."
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. MIGRATION
# =========================================================

Write-Host "[3/6] Control migration..."

$CurrentRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $CurrentRevision

if (
    $CurrentRevision -notmatch
    "a6b7c8d9e0f1"
)
{
    throw (
        "Expected current control revision " +
        "a6b7c8d9e0f1."
    )
}

Write-Host "PASS migration"
Write-Host ""


# =========================================================
# 4. MODEL CONTRACT
# =========================================================

Write-Host "[4/6] Channel model contract..."

$ModelScript = @'
from app.modules.channels.models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
    WorkspaceChannelMessage,
)

assert (
    WorkspaceChannel.__tablename__
    == "workspace_channels"
)

assert (
    WorkspaceChannelMember.__tablename__
    == "workspace_channel_members"
)

assert (
    WorkspaceChannelMessage.__tablename__
    == "workspace_channel_messages"
)

print(
    "PASS workspace channel model"
)

print(
    "PASS workspace channel membership model"
)

print(
    "PASS workspace channel message model"
)
'@

$ModelScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel model contract failed."
}

Write-Host ""


# =========================================================
# 5. API CONTRACT
# =========================================================

Write-Host "[5/6] Workspace channel API..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/workspace-channels": {
        "post",
    },
    "/api/v1/workspace-channels/workspace/{workspace_id}": {
        "get",
    },
    "/api/v1/workspace-channels/{channel_id}": {
        "patch",
        "delete",
    },
    "/api/v1/workspace-channels/{channel_id}/messages": {
        "get",
        "post",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing path: {path}"
        )

    for method in methods:
        if method not in paths[path]:
            raise RuntimeError(
                f"Missing {method.upper()} {path}"
            )

        print(
            "PASS:",
            method.upper(),
            path,
        )

print(
    "PASS workspace channel API"
)
'@

$ApiScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel API contract failed."
}

Write-Host ""


# =========================================================
# 6. SECURITY BOUNDARIES
# =========================================================

Write-Host "[6/6] Workspace channel boundaries..."

$BoundaryScript = @'
import inspect

from app.modules.channels.repository import (
    WorkspaceChannelRepository,
)
from app.modules.channels.router import (
    create_workspace_channel,
    send_channel_message,
)
from app.modules.channels.service import (
    WorkspaceChannelService,
)

repository_source = inspect.getsource(
    WorkspaceChannelRepository
)

service_source = inspect.getsource(
    WorkspaceChannelService
)

create_source = inspect.getsource(
    create_workspace_channel
)

message_source = inspect.getsource(
    send_channel_message
)

required_repository_tokens = (
    "workspace_id",
    "created_by_user_id",
)

for token in required_repository_tokens:
    if token not in repository_source:
        raise RuntimeError(
            f"Missing workspace boundary: {token}"
        )

if "_require_active_member" not in service_source:
    raise RuntimeError(
        "Channel membership boundary missing."
    )

if "_require_manager" not in service_source:
    raise RuntimeError(
        "Channel manager boundary missing."
    )

if "get_current_verified_user" not in create_source:
    raise RuntimeError(
        "Channel creation authentication missing."
    )

if "get_current_verified_user" not in message_source:
    raise RuntimeError(
        "Channel message authentication missing."
    )

print(
    "PASS verified-user channel authentication"
)

print(
    "PASS workspace creator creation boundary"
)

print(
    "PASS workspace-scoped channel identity"
)

print(
    "PASS active channel membership boundary"
)

print(
    "PASS channel owner/admin management boundary"
)
'@

$BoundaryScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel boundary check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 WORKSPACE CHANNELS: PASS"
Write-Host "================================================="
Write-Host ""