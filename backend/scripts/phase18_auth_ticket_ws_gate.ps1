$ErrorActionPreference = "Stop"


. (
    Join-Path `
        $PSScriptRoot `
        "phase18_common.ps1"
)


Set-Location $script:Phase18BackendRoot


Write-Host "================================================="
Write-Host " Phase 18 Auth -> Ticket -> WebSocket Gate"
Write-Host "================================================="
Write-Host ""


Write-Host "[1/4] Ticket service contract..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_ticket.py" `
    -Tokens @(
        "_ATOMIC_CONSUME_LUA",
        "redis_client.eval",
        "secrets.token_urlsafe",
        "workspace_id",
        "channel_id",
        "user_id"
    )


Write-Host "PASS ticket service contract"
Write-Host ""


Write-Host "[2/4] WebSocket ticket contract..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_websocket.py" `
    -Tokens @(
        "channel_realtime_ticket_service",
        ".consume(",
        "code=4401",
        "ChannelAccessGuard",
        "code=4403"
    )


Write-Host "PASS WebSocket ticket contract"
Write-Host ""


Write-Host "[3/4] No direct JWT WebSocket auth..."


$WebSocketSource = Get-Content `
    ".\app\modules\channels\realtime_websocket.py" `
    -Raw


$Forbidden = @(
    "decode_token(",
    "jwt.decode(",
    "Authorization"
)


foreach ($Token in $Forbidden)
{
    if (
        $WebSocketSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -ge 0
    )
    {
        Fail-Phase18 (
            "Direct JWT WebSocket auth detected: {0}" `
                -f $Token
        )
    }
}


Write-Host "PASS one-time-ticket-only WebSocket auth"
Write-Host ""


Write-Host "[4/4] Phase 17 auth security tests..."


Invoke-Phase18Pytest `
    -Tests @(
        ".\tests\channels\test_phase17_ticket_atomicity.py",
        ".\tests\channels\test_phase17_websocket_hardening.py"
    ) `
    -Label "Auth-ticket-WebSocket security"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 18 AUTH -> TICKET -> WEBSOCKET: PASS"
Write-Host "================================================="

exit 0