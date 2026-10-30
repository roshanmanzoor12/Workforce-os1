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
    Write-Host "FAIL:" $Message
    Write-Host ""

    exit 1
}


function Assert-LastExitCode
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


try
{
    Write-Host "================================================="
    Write-Host " WorkforceOS Phase 17 Hardening Batch 2 Gate"
    Write-Host "================================================="
    Write-Host ""


    # =====================================================
    # 1. REQUIRED FILES
    # =====================================================

    Write-Host "[1/8] Required files..."


    $RequiredFiles = @(
        ".\app\modules\channels\realtime_ticket.py",
        ".\app\modules\channels\realtime_websocket.py",
        ".\app\modules\channels\realtime_service.py",
        ".\app\modules\channels\realtime_presence.py",
        ".\app\modules\channels\read_state_repository.py",
        ".\app\modules\channels\realtime_pubsub.py",
        ".\app\modules\channels\realtime_replay.py",
        ".\scripts\phase17_attachment_access_contract.py",
        ".\tests\channels\test_phase17_realtime_security.py",
        ".\scripts\phase17_hardening_foundation_gate.ps1"
    )


    foreach ($File in $RequiredFiles)
    {
        if (-not (Test-Path $File))
        {
            Fail-Gate (
                "Missing required file: {0}" -f $File
            )
        }
    }


    Write-Host "PASS required files"
    Write-Host ""


    # =====================================================
    # 2. COMPILE
    # =====================================================

    Write-Host "[2/8] Compiling Batch 2..."


    & $Python `
        -m compileall `
        ".\app\modules\channels" `
        ".\app\modules\attachments\service.py" `
        ".\scripts\phase17_attachment_access_contract.py" `
        ".\tests\channels\test_phase17_realtime_security.py" `
        -q


    Assert-LastExitCode `
        "Batch 2 compile failed."


    Write-Host "PASS compile"
    Write-Host ""


    # =====================================================
    # 3. IMPORT GATE
    # =====================================================

    Write-Host "[3/8] Batch 2 imports..."


    $ImportProbe = @'
from app.modules.channels.realtime_ticket import (
    WorkspaceChannelRealtimeTicketService,
)
from app.modules.channels.realtime_websocket import (
    WorkspaceChannelRealtimeWebSocket,
)
from app.modules.channels.realtime_service import (
    WorkspaceChannelRealtimeService,
)
from app.modules.channels.realtime_presence import (
    WorkspaceChannelRealtimePresence,
)
from app.modules.channels.read_state_repository import (
    WorkspaceChannelReadStateRepository,
)
from app.modules.channels.realtime_pubsub import (
    ChannelRealtimePubSubSession,
)
from app.modules.channels.realtime_replay import (
    ChannelRealtimeReplayPolicy,
)

print("PASS Batch 2 imports")
'@


    $ImportProbe |
        & $Python -


    Assert-LastExitCode `
        "Batch 2 import gate failed."


    Write-Host "PASS imports"
    Write-Host ""


    # =====================================================
    # 4. ATOMIC TICKET WIRING
    # =====================================================

    Write-Host "[4/8] Atomic ticket wiring..."


    $TicketSource = Get-Content `
        ".\app\modules\channels\realtime_ticket.py" `
        -Raw


    if (
        $TicketSource.IndexOf(
            "_ATOMIC_CONSUME_LUA",
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate `
            "Atomic ticket Lua contract missing."
    }


    if (
        $TicketSource.IndexOf(
            "redis_client.eval",
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate `
            "Atomic Redis ticket consume not wired."
    }


    if (
        $TicketSource.IndexOf(
            "await redis_client.get(",
            [System.StringComparison]::Ordinal
        ) -ge 0
    )
    {
        Fail-Gate (
            "Ticket service still contains non-atomic " +
            "GET consume."
        )
    }


    Write-Host "PASS atomic ticket wiring"
    Write-Host ""


    # =====================================================
    # 5. WEBSOCKET HARDENING
    # =====================================================

    Write-Host "[5/8] WebSocket hardening wiring..."


    $WebSocketSource = Get-Content `
        ".\app\modules\channels\realtime_websocket.py" `
        -Raw


    $RequiredWebSocketTokens = @(
        "ChannelAccessGuard",
        "ControlSessionLocal",
        "ChannelRateLimiter",
        "ChannelRealtimePubSubSession",
        "require_membership_revalidation",
        "code=4403",
        "code=4429"
    )


    foreach ($Token in $RequiredWebSocketTokens)
    {
        if (
            $WebSocketSource.IndexOf(
                $Token,
                [System.StringComparison]::Ordinal
            ) -lt 0
        )
        {
            Fail-Gate (
                "Missing WebSocket hardening token: {0}" `
                    -f $Token
            )
        }
    }


    Write-Host "PASS WebSocket hardening wiring"
    Write-Host ""


    # =====================================================
    # 6. READ STATE + ATTACHMENT
    # =====================================================

    Write-Host "[6/8] Read-state + attachment contracts..."


    $ReadStateSource = Get-Content `
        ".\app\modules\channels\read_state_repository.py" `
        -Raw


    if (
        $ReadStateSource.IndexOf(
            "ChannelReadStateUpserter",
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate `
            "Read-state UPSERT is not wired."
    }


    if (
        $ReadStateSource.IndexOf(
            ".upsert_and_flush(",
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        Fail-Gate (
            "Read-state repository does not use " +
            "atomic UPSERT."
        )
    }


    & $Python `
        ".\scripts\phase17_attachment_access_contract.py"


    Assert-LastExitCode `
        "Attachment lifecycle contract failed."


    Write-Host "PASS read-state + attachment contracts"
    Write-Host ""


    # =====================================================
    # 7. SECURITY TESTS
    # =====================================================

    Write-Host "[7/8] Realtime security tests..."


    & $Python `
        -m pytest `
        ".\tests\channels\test_phase17_realtime_security.py" `
        -q


    Assert-LastExitCode `
        "Realtime security tests failed."


    Write-Host "PASS realtime security tests"
    Write-Host ""


    # =====================================================
    # 8. BATCH 1 REGRESSION
    # =====================================================

    Write-Host "[8/8] Batch 1 regression..."


    $FoundationGate = Join-Path `
        $BackendRoot `
        "scripts\phase17_hardening_foundation_gate.ps1"


    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $FoundationGate


    Assert-LastExitCode `
        "Phase 17 Batch 1 regression failed."


    Write-Host "PASS Batch 1 regression"
    Write-Host ""


    # =====================================================
    # FINAL
    # =====================================================

    Write-Host "================================================="
    Write-Host " PHASE 17 HARDENING BATCH 2: PASS"
    Write-Host "================================================="
    Write-Host "Required files:                    PASS"
    Write-Host "Python compile:                    PASS"
    Write-Host "Import safety:                     PASS"
    Write-Host "Atomic ticket wiring:              PASS"
    Write-Host "Membership revalidation:           PASS"
    Write-Host "Realtime rate limiting:            PASS"
    Write-Host "Presence/typing lifetime:          PASS"
    Write-Host "Read-state UPSERT wiring:          PASS"
    Write-Host "Attachment lifecycle:              PASS"
    Write-Host "Redis pubsub lifecycle:            PASS"
    Write-Host "Replay bounds:                     PASS"
    Write-Host "Realtime security tests:           PASS"
    Write-Host "Batch 1 regression:                PASS"
    Write-Host "================================================="
    Write-Host ""

    exit 0
}
catch
{
    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 17 HARDENING BATCH 2: FAIL"
    Write-Host "================================================="
    Write-Host "ERROR:" $_.Exception.Message
    Write-Host "================================================="
    Write-Host ""

    exit 1
}