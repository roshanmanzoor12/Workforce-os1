$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Backend Gate"
Write-Host "================================================="
Write-Host ""


$BackendRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $BackendRoot


$Python =
    Join-Path `
        $BackendRoot `
        ".venv\Scripts\python.exe"


$BridgeFile =
    ".\app\modules\channels\realtime_attachment_bridge.py"


$RouterFile =
    ".\app\modules\attachments\message_router.py"


$EventsFile =
    ".\app\modules\channels\realtime_events.py"


$SchemasFile =
    ".\app\modules\channels\realtime_schemas.py"


function Fail-Gate {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host "FAIL: $Message" `
        -ForegroundColor Red

    Write-Host ""

    exit 1
}


function Pass-Step {
    param(
        [string]$Message
    )

    Write-Host "PASS: $Message" `
        -ForegroundColor Green
}


Write-Host "[1/8] Required files..."


foreach (
    $File in @(
        $BridgeFile,
        $RouterFile,
        $EventsFile,
        $SchemasFile
    )
)
{
    if (
        -not (
            Test-Path $File
        )
    )
    {
        Fail-Gate `
            "Missing required file: $File"
    }
}


Pass-Step `
    "Required files present"


Write-Host ""
Write-Host "[2/8] Event enum contract..."


if (
    -not (
        Select-String `
            -Path $SchemasFile `
            -Pattern `
            'channel\.attachment\.bound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "channel.attachment.bound event type missing."
}


Pass-Step `
    "channel.attachment.bound exists"


Write-Host ""
Write-Host "[3/8] Publisher contract..."


if (
    -not (
        Select-String `
            -Path $EventsFile `
            -Pattern `
            'async def attachment_bound' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Realtime attachment_bound publisher missing."
}


Pass-Step `
    "attachment_bound publisher exists"


Write-Host ""
Write-Host "[4/8] Bridge contract..."


if (
    -not (
        Select-String `
            -Path $BridgeFile `
            -Pattern `
            '\.attachment_bound\(' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Attachment bridge does not call attachment_bound."
}


Pass-Step `
    "Attachment bridge publishes event"


Write-Host ""
Write-Host "[5/8] Channel bind route wiring..."


if (
    -not (
        Select-String `
            -Path $RouterFile `
            -Pattern `
            'channel_realtime_attachment_bridge' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Channel attachment route is not wired to realtime bridge."
}


if (
    -not (
        Select-String `
            -Path $RouterFile `
            -Pattern `
            '\.publish_bound\(' `
            -Quiet
    )
)
{
    Fail-Gate `
        "Channel bind route does not publish attachment.bound."
}


Pass-Step `
    "Channel bind route realtime wired"


Write-Host ""
Write-Host "[6/8] Compiling backend files..."


& $Python `
    -m compileall `
    ".\app\modules\attachments\message_router.py" `
    ".\app\modules\channels\realtime_attachment_bridge.py" `
    ".\app\modules\channels\realtime_events.py" `
    -q


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "Python compile failed."
}


Pass-Step `
    "Python compile"


Write-Host ""
Write-Host "[7/8] Import contracts..."


& $Python `
    -c `
    "from app.modules.attachments.message_router import router; from app.modules.channels.realtime_attachment_bridge import channel_realtime_attachment_bridge; from app.modules.channels.realtime_events import channel_realtime_events; print('PASS attachment realtime imports')"


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "Backend import contract failed."
}


Pass-Step `
    "Backend imports"


Write-Host ""
Write-Host "[8/8] Publisher signature..."


& $Python `
    -c `
    "import inspect; from app.modules.channels.realtime_events import channel_realtime_events; s=str(inspect.signature(channel_realtime_events.attachment_bound)); print(s); assert 'workspace_id' in s; assert 'channel_id' in s; assert 'message_id' in s; assert 'attachment_ids' in s; assert 'actor_user_id' in s; print('PASS attachment publisher signature')"


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "attachment_bound publisher signature invalid."
}


Pass-Step `
    "Publisher signature"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C ATTACHMENT BACKEND WIRING PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Realtime event enum              PASS"
Write-Host "Realtime publisher               PASS"
Write-Host "Attachment bridge                PASS"
Write-Host "Channel binding integration      PASS"
Write-Host "Compile                          PASS"
Write-Host "Imports                          PASS"
Write-Host "Publisher contract               PASS"
Write-Host ""
Write-Host "Backend attachment.bound wiring certified."
Write-Host "================================================="
Write-Host ""