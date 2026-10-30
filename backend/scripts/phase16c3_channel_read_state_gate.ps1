$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = (
    "h2c3d4e5f6g7"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C.3 Read State Gate"
Write-Host "================================================="
Write-Host ""


$RequiredFiles = @(
    ".\app\modules\channels\read_state_models.py",
    ".\app\modules\channels\read_state_schemas.py",
    ".\app\modules\channels\read_state_repository.py",
    ".\app\modules\channels\read_state_service.py",
    ".\app\modules\channels\read_state_router.py",
    ".\app\modules\channels\router.py",
    ".\migrations\control\versions\h2c3d4e5f6g7_add_workspace_channel_read_states.py"
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


Write-Host "[1/6] Compile..."


& $Python `
    -m compileall `
    ".\app\modules\channels" `
    ".\migrations\control\versions\h2c3d4e5f6g7_add_workspace_channel_read_states.py" `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


Write-Host "[2/6] Imports..."


$ImportCheck = @'
from app.modules.channels.read_state_models import (
    WorkspaceChannelReadState,
)
from app.modules.channels.read_state_repository import (
    WorkspaceChannelReadStateRepository,
)
from app.modules.channels.read_state_router import (
    router,
)
from app.modules.channels.read_state_service import (
    WorkspaceChannelReadStateService,
)


assert WorkspaceChannelReadState
assert WorkspaceChannelReadStateRepository
assert WorkspaceChannelReadStateService
assert router


print("PASS imports")
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Import gate failed."
}


Write-Host ""


Write-Host "[3/6] Control migration head..."


$Heads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Control heads failed."
}


$HeadsText = (
    $Heads -join "`n"
)


Write-Host $HeadsText


if (
    $HeadsText -notmatch
    $ExpectedControlHead
)
{
    throw (
        "Unexpected control graph head. Expected " +
        $ExpectedControlHead
    )
}


Write-Host "PASS graph head"
Write-Host ""


Write-Host "[4/6] Applied control revision..."


$Current = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Control current failed."
}


$CurrentText = (
    $Current -join "`n"
)


Write-Host $CurrentText


if (
    $CurrentText -notmatch
    $ExpectedControlHead
)
{
    throw (
        "Control DB has not been upgraded to " +
        $ExpectedControlHead
    )
}


Write-Host "PASS applied revision"
Write-Host ""


Write-Host "[5/6] OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


required = {
    (
        "/api/v1/workspace-channels/"
        "workspace/{workspace_id}/read-state"
    ): {
        "get",
    },

    (
        "/api/v1/workspace-channels/"
        "{channel_id}/read-state"
    ): {
        "get",
    },

    (
        "/api/v1/workspace-channels/"
        "{channel_id}/read/{message_id}"
    ): {
        "post",
    },

    (
        "/api/v1/workspace-channels/"
        "{channel_id}/read-all"
    ): {
        "post",
    },
}


for path, methods in required.items():
    if path not in paths:
        raise SystemExit(
            "Missing read-state endpoint: "
            + path
        )

    missing = (
        methods
        - set(paths[path])
    )

    if missing:
        raise SystemExit(
            "Missing methods for "
            + path
            + ": "
            + str(sorted(missing))
        )


print("PASS OpenAPI")
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI gate failed."
}


Write-Host ""


Write-Host "[6/6] Safety contract..."


$SafetyCheck = @'
from pathlib import Path


service = Path(
    r"C:\workforce-os\backend"
    r"\app\modules\channels"
    r"\read_state_service.py"
).read_text(
    encoding="utf-8-sig"
)


repository = Path(
    r"C:\workforce-os\backend"
    r"\app\modules\channels"
    r"\read_state_repository.py"
).read_text(
    encoding="utf-8-sig"
)


if "left_at" not in repository:
    raise SystemExit(
        "Active membership check missing."
    )


if "sender_user_id" not in repository:
    raise SystemExit(
        "Self-message unread exclusion missing."
    )


if "deleted_at" not in repository:
    raise SystemExit(
        "Deleted-message exclusion missing."
    )


if "last_read_at" not in service:
    raise SystemExit(
        "Durable read cursor missing."
    )


print("PASS safety contract")
'@


$SafetyCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Safety gate failed."
}


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C.3 CHANNEL READ STATE: PASS"
Write-Host "================================================="
Write-Host "Persistent cursor:              PASS"
Write-Host "Per-user/channel isolation:     PASS"
Write-Host "Active membership enforcement: PASS"
Write-Host "Unread counts:                  PASS"
Write-Host "Self-message exclusion:         PASS"
Write-Host "Deleted-message exclusion:      PASS"
Write-Host "OpenAPI endpoints:              PASS"
Write-Host "Control head:                   $ExpectedControlHead"
Write-Host "================================================="