$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = Join-Path `
    $BackendRoot `
    ".venv\Scripts\python.exe"


Set-Location $BackendRoot


function Fail-Gate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 17 RUNTIME REGRESSION: FAIL"
    Write-Host "================================================="
    Write-Host "ERROR:" $Message
    Write-Host "================================================="
    Write-Host ""

    exit 1
}


function Assert-ExitCode
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Gate $Message
    }
}


function Invoke-PowerShellGate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Label
    )

    if (-not (Test-Path $Path))
    {
        Fail-Gate (
            "Missing gate: {0}" -f $Path
        )
    }

    Write-Host ""
    Write-Host "-------------------------------------------------"
    Write-Host $Label
    Write-Host "-------------------------------------------------"

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Path

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Gate (
            "{0} failed with exit code {1}." `
                -f $Label, $LASTEXITCODE
        )
    }

    Write-Host "PASS $Label"
}


Write-Host "================================================="
Write-Host " WorkforceOS Phase 17 Runtime Regression Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# 1/8 REQUIRED FILES
# =========================================================

Write-Host "[1/8] Required runtime files..."


$RequiredFiles = @(
    ".\app\modules\channels\realtime_ticket.py",
    ".\app\modules\channels\realtime_websocket.py",
    ".\app\modules\channels\realtime_service.py",
    ".\app\modules\channels\realtime_presence.py",
    ".\app\modules\channels\realtime_pubsub.py",
    ".\app\modules\channels\realtime_replay.py",
    ".\app\modules\channels\realtime_bus.py",
    ".\app\modules\channels\realtime_events.py",
    ".\app\modules\channels\realtime_attachment_bridge.py",
    ".\app\modules\channels\read_state_repository.py",
    ".\app\modules\attachments\service.py",
    ".\scripts\phase17_hardening_foundation_gate.ps1",
    ".\scripts\phase17_batch2_gate.ps1"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        Fail-Gate (
            "Missing required runtime file: {0}" `
                -f $File
        )
    }
}


Write-Host "PASS required runtime files"
Write-Host ""


# =========================================================
# 2/8 COMPILE
# =========================================================

Write-Host "[2/8] Compiling realtime runtime..."


& $Python `
    -m compileall `
    ".\app\modules\channels" `
    ".\app\modules\attachments" `
    -q


Assert-ExitCode `
    "Realtime runtime compile failed."


Write-Host "PASS realtime runtime compile"
Write-Host ""


# =========================================================
# 3/8 IMPORT CONTRACT
# =========================================================

Write-Host "[3/8] Runtime import contract..."


$ImportProbe = @'
from app.modules.channels.realtime_ticket import (
    WorkspaceChannelRealtimeTicketService,
    channel_realtime_ticket_service,
)

from app.modules.channels.realtime_websocket import (
    WorkspaceChannelRealtimeWebSocket,
    channel_realtime_websocket,
)

from app.modules.channels.realtime_service import (
    WorkspaceChannelRealtimeService,
    channel_realtime_service,
)

from app.modules.channels.realtime_presence import (
    WorkspaceChannelRealtimePresence,
    channel_realtime_presence,
)

from app.modules.channels.realtime_pubsub import (
    ChannelRealtimePubSubSession,
)

from app.modules.channels.realtime_replay import (
    ChannelRealtimeReplayPolicy,
    ReplayWindowExceeded,
)

from app.modules.channels.realtime_events import (
    WorkspaceChannelRealtimeEventPublisher,
    channel_realtime_events,
)

from app.modules.channels.realtime_attachment_bridge import (
    WorkspaceChannelRealtimeAttachmentBridge,
    channel_realtime_attachment_bridge,
)

from app.modules.channels.read_state_repository import (
    WorkspaceChannelReadStateRepository,
)

print("PASS runtime imports")
'@


$ImportProbe |
    & $Python -


Assert-ExitCode `
    "Runtime import contract failed."


Write-Host "PASS runtime imports"
Write-Host ""


# =========================================================
# 4/8 SECURITY CONTRACT
# =========================================================

Write-Host "[4/8] Realtime security source contract..."


$TicketSource = Get-Content `
    ".\app\modules\channels\realtime_ticket.py" `
    -Raw

$WebSocketSource = Get-Content `
    ".\app\modules\channels\realtime_websocket.py" `
    -Raw

$PresenceSource = Get-Content `
    ".\app\modules\channels\realtime_presence.py" `
    -Raw

$ReadStateSource = Get-Content `
    ".\app\modules\channels\read_state_repository.py" `
    -Raw

$AttachmentSource = Get-Content `
    ".\app\modules\attachments\service.py" `
    -Raw


$TicketTokens = @(
    "_ATOMIC_CONSUME_LUA",
    "redis_client.eval",
    "ticket_ttl_seconds"
)


foreach ($Token in $TicketTokens)
{
    if (
        $TicketSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate (
            "Ticket hardening token missing: {0}" `
                -f $Token
        )
    }
}


if (
    $TicketSource.IndexOf(
        "await redis_client.get(",
        [System.StringComparison]::Ordinal
    ) -ge 0
)
{
    Fail-Gate (
        "Realtime ticket consume regressed to " +
        "non-atomic GET behavior."
    )
}


$WebSocketTokens = @(
    "ChannelAccessGuard",
    "ChannelRateLimiter",
    "ChannelRealtimePubSubSession",
    "require_membership_revalidation",
    "code=4403",
    "code=4429"
)


foreach ($Token in $WebSocketTokens)
{
    if (
        $WebSocketSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate (
            "WebSocket hardening token missing: {0}" `
                -f $Token
        )
    }
}


if (
    $PresenceSource.IndexOf(
        "PresenceLifetimeGuard",
        [System.StringComparison]::Ordinal
    ) -lt 0
)
{
    Fail-Gate `
        "Presence lifetime guard is not wired."
}


if (
    $ReadStateSource.IndexOf(
        "ChannelReadStateUpserter",
        [System.StringComparison]::Ordinal
    ) -lt 0
)
{
    Fail-Gate `
        "Read-state atomic UPSERT is not wired."
}


if (
    $AttachmentSource.IndexOf(
        "WorkspaceChannelMember.left_at.is_(",
        [System.StringComparison]::Ordinal
    ) -lt 0
)
{
    Fail-Gate `
        "Attachment left_at lifecycle check missing."
}


Write-Host "PASS realtime security source contract"
Write-Host ""


# =========================================================
# 5/8 PHASE 17 BATCH 1 REGRESSION
# =========================================================

Write-Host "[5/8] Phase 17 Batch 1 regression..."


Invoke-PowerShellGate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_hardening_foundation_gate.ps1"
    ) `
    -Label "Phase 17 Batch 1"


Write-Host ""


# =========================================================
# 6/8 PHASE 17 BATCH 2 REGRESSION
# =========================================================

Write-Host "[6/8] Phase 17 Batch 2 regression..."


Invoke-PowerShellGate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_batch2_gate.ps1"
    ) `
    -Label "Phase 17 Batch 2"


Write-Host ""


# =========================================================
# 7/8 PHASE 16C REGRESSION
# =========================================================

Write-Host "[7/8] Phase 16C realtime regression..."


$Phase16CCandidates = @(
    ".\scripts\phase16c_attachment_backend_wiring_gate.ps1",
    ".\scripts\phase16c_attachment_realtime_preflight.ps1"
)


$Phase16CRan = $false


foreach ($Candidate in $Phase16CCandidates)
{
    if (Test-Path $Candidate)
    {
        Invoke-PowerShellGate `
            -Path (
                Resolve-Path $Candidate
            ).Path `
            -Label (
                "Phase 16C regression - " +
                (Split-Path $Candidate -Leaf)
            )

        $Phase16CRan = $true
    }
}


if (-not $Phase16CRan)
{
    Fail-Gate (
        "No certified Phase 16C backend regression " +
        "gate was found."
    )
}


Write-Host "PASS Phase 16C realtime regression"
Write-Host ""


# =========================================================
# 8/8 SECURITY TESTS
# =========================================================

Write-Host "[8/8] Phase 17 realtime security tests..."


if (
    -not (
        Test-Path `
            ".\tests\channels\test_phase17_realtime_security.py"
    )
)
{
    Fail-Gate `
        "Phase 17 realtime security test file missing."
}


& $Python `
    -m pytest `
    ".\tests\channels\test_phase17_realtime_security.py" `
    -q


Assert-ExitCode `
    "Phase 17 realtime security tests failed."


Write-Host "PASS realtime security tests"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 17 RUNTIME REGRESSION: PASS"
Write-Host "================================================="
Write-Host "Required runtime files:           PASS"
Write-Host "Python compile:                   PASS"
Write-Host "Runtime imports:                  PASS"
Write-Host "Security source contracts:        PASS"
Write-Host "Phase 17 Batch 1 regression:      PASS"
Write-Host "Phase 17 Batch 2 regression:      PASS"
Write-Host "Phase 16C realtime regression:    PASS"
Write-Host "Realtime security tests:          PASS"
Write-Host "================================================="
Write-Host ""

exit 0