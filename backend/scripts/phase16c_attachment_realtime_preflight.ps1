$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Realtime Preflight"
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


$AttachmentService =
    Join-Path `
        $BackendRoot `
        "app\modules\attachments\service.py"


$RealtimeEvents =
    Join-Path `
        $BackendRoot `
        "app\modules\channels\realtime_events.py"


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


Write-Host "[1/7] Checking files..."


if (
    -not (
        Test-Path $Python
    )
) {
    Fail-Gate `
        "Backend virtualenv Python not found."
}


if (
    -not (
        Test-Path $AttachmentService
    )
) {
    Fail-Gate `
        "Attachment service not found."
}


if (
    -not (
        Test-Path $RealtimeEvents
    )
) {
    Fail-Gate `
        "Channel realtime_events.py not found."
}


Pass-Step `
    "Required files present"


Write-Host ""
Write-Host "[2/7] Checking obsolete channel membership field..."


$BadMembershipCheck =
    Select-String `
        -Path $AttachmentService `
        -Pattern `
        "WorkspaceChannelMember\.is_active" `
        -Quiet


if ($BadMembershipCheck) {
    Fail-Gate `
        "Attachment service still references WorkspaceChannelMember.is_active."
}


Pass-Step `
    "No obsolete WorkspaceChannelMember.is_active reference"


Write-Host ""
Write-Host "[3/7] Checking active membership contract..."


$HasLeftAtCheck =
    Select-String `
        -Path $AttachmentService `
        -Pattern `
        "WorkspaceChannelMember\.left_at" `
        -Quiet


if (
    -not $HasLeftAtCheck
) {
    Fail-Gate `
        "Attachment service does not check WorkspaceChannelMember.left_at."
}


Pass-Step `
    "Channel membership uses left_at"


Write-Host ""
Write-Host "[4/7] Checking active channel contract..."


$HasChannelActiveCheck =
    Select-String `
        -Path $AttachmentService `
        -Pattern `
        "WorkspaceChannel\.is_active" `
        -Quiet


if (
    -not $HasChannelActiveCheck
) {
    Fail-Gate `
        "Attachment service does not verify WorkspaceChannel.is_active."
}


Pass-Step `
    "Inactive channels denied"


Write-Host ""
Write-Host "[5/7] Compiling attachment service..."


& $Python `
    -m compileall `
    ".\app\modules\attachments\service.py" `
    -q


if (
    $LASTEXITCODE -ne 0
) {
    Fail-Gate `
        "Attachment service compile failed."
}


Pass-Step `
    "Attachment service compile"


Write-Host ""
Write-Host "[6/7] Importing attachment service..."


& $Python `
    -c `
    "from app.modules.attachments.service import AttachmentService; print('PASS AttachmentService import')"


if (
    $LASTEXITCODE -ne 0
) {
    Fail-Gate `
        "AttachmentService import failed."
}


Pass-Step `
    "AttachmentService import"


Write-Host ""
Write-Host "[7/7] Importing realtime publisher..."


& $Python `
    -c `
    "from app.modules.channels.realtime_events import WorkspaceChannelRealtimeEventPublisher, channel_realtime_events; print('PASS channel realtime publisher import')"


if (
    $LASTEXITCODE -ne 0
) {
    Fail-Gate `
        "Channel realtime publisher import failed."
}


Pass-Step `
    "Realtime publisher preserved"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C ATTACHMENT REALTIME PREFLIGHT PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Attachment access contract        PASS"
Write-Host "Inactive channel rejection        PASS"
Write-Host "Legacy is_active bug removed      PASS"
Write-Host "Attachment service compile        PASS"
Write-Host "Attachment service import         PASS"
Write-Host "Realtime publisher import         PASS"
Write-Host ""
Write-Host "Ready for attachment.bound wiring."
Write-Host "================================================="
Write-Host ""