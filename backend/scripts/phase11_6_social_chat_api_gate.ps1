$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Social/Chat API Gate"
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
    throw (
        "PostgreSQL is not reachable on " +
        "127.0.0.1:5434."
    )
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/5] Compiling..."

& $Python `
    -m py_compile `
    .\app\modules\friends\repository.py `
    .\app\modules\friends\schemas.py `
    .\app\modules\friends\service.py `
    .\app\modules\friends\router.py `
    .\app\modules\chat\repository.py `
    .\app\modules\chat\service.py `
    .\app\modules\chat\router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 social/chat API compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/5] Social/chat tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 social/chat tests failed."
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. MIGRATION
# =========================================================

Write-Host "[3/5] Control migration..."

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
    "e4f5a6b7c8d9"
)
{
    throw (
        "Expected Phase 11.6 revision " +
        "e4f5a6b7c8d9."
    )
}

Write-Host "PASS migration"
Write-Host ""


# =========================================================
# 4. OPENAPI CONTRACT
# =========================================================

Write-Host "[4/5] OpenAPI contract..."

@'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/friends/requests/{target_user_id}": {
        "post",
    },
    "/api/v1/friends/requests/{friendship_id}/accept": {
        "post",
    },
    "/api/v1/friends/requests/{friendship_id}": {
        "delete",
    },
    "/api/v1/friends/blocks/{target_user_id}": {
        "post",
        "delete",
    },
    "/api/v1/friends": {
        "get",
    },
    "/api/v1/chat/direct": {
        "post",
    },
    "/api/v1/chat/groups": {
        "post",
    },
    "/api/v1/chat/conversations": {
        "get",
    },
    "/api/v1/chat/{conversation_id}/members/{target_user_id}": {
        "post",
        "delete",
    },
    "/api/v1/chat/{conversation_id}/messages": {
        "post",
        "get",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing OpenAPI path: {path}"
        )

    actual = {
        method.lower()
        for method in paths[path].keys()
    }

    for method in methods:
        if method not in actual:
            raise RuntimeError(
                "Missing operation: "
                f"{method.upper()} {path}"
            )

        print(
            "PASS:",
            method.upper(),
            path,
        )

print(
    "PASS social/chat OpenAPI"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Social/chat OpenAPI contract failed."
}

Write-Host ""


# =========================================================
# 5. SECURITY / ACCESS BOUNDARY
# =========================================================

Write-Host "[5/5] Access/privacy boundaries..."

@'
import inspect

from app.modules.chat import router as chat_router_module
from app.modules.friends import router as friends_router_module

chat_source = inspect.getsource(
    chat_router_module
)

friends_source = inspect.getsource(
    friends_router_module
)

required = (
    "get_current_verified_user",
    "get_control_db",
)

for token in required:
    if token not in chat_source:
        raise RuntimeError(
            f"Chat router missing dependency: {token}"
        )

    if token not in friends_source:
        raise RuntimeError(
            f"Friends router missing dependency: {token}"
        )

print(
    "PASS verified-user authentication boundary"
)

print(
    "PASS control DB dependency boundary"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Social/chat access-boundary check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 SOCIAL/CHAT API: PASS"
Write-Host "================================================="
Write-Host ""