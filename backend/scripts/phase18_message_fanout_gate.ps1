$ErrorActionPreference = "Stop"


. (
    Join-Path `
        $PSScriptRoot `
        "phase18_common.ps1"
)


Set-Location $script:Phase18BackendRoot


Write-Host "================================================="
Write-Host " Phase 18 Two-Client Message Fanout Gate"
Write-Host "================================================="
Write-Host ""


Write-Host "[1/3] Realtime publisher contract..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_events.py" `
    -Tokens @(
        "message_created",
        "MESSAGE_CREATED",
        "channel_realtime_bus",
        ".publish("
    )


Write-Host "PASS publisher contract"
Write-Host ""


Write-Host "[2/3] WebSocket fanout transport..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_websocket.py" `
    -Tokens @(
        "ChannelRealtimePubSubSession",
        "_redis_to_websocket",
        "send_text"
    )


Write-Host "PASS transport contract"
Write-Host ""


Write-Host "[3/3] Certified two-client runtime regression..."


Invoke-Phase18LegacyGate `
    -Regex "(?is)(two[\s_-]*client.*message|message.*two[\s_-]*client|message.*fanout|fanout.*message)" `
    -Label "Two-client message fanout"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 18 TWO-CLIENT MESSAGE FANOUT: PASS"
Write-Host "================================================="

exit 0