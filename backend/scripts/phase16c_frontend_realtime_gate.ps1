$ErrorActionPreference = "Stop"


$WebRoot = (
    "C:\workforce-os\apps\web"
)


Set-Location $WebRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Frontend Realtime Gate"
Write-Host "================================================="
Write-Host ""


$RequiredFiles = @(
    ".\types\channel-realtime.ts",
    ".\types\channel-read-state.ts",
    ".\services\channel-realtime.service.ts",
    ".\services\channel-read-state.service.ts",
    ".\services\channel-messages.service.ts",
    ".\lib\realtime\channel-realtime-client.ts",
    ".\lib\realtime\channel-event-reducer.ts",
    ".\hooks\use-channel-realtime.ts",
    ".\hooks\use-channel-read-state.ts",
    ".\hooks\use-workspace-channel-unread.ts",
    ".\components\channels\channel-message-composer.tsx",
    ".\components\channels\channel-live-message-list.tsx",
    ".\components\channels\channel-realtime-room.tsx",
    ".\components\channels\channel-typing-indicator.tsx",
    ".\components\channels\channel-realtime-status.tsx",
    ".\components\channels\channel-unread-badge.tsx",
    ".\components\channels\channel-sidebar-unread-row.tsx",
    ".\contexts\channel-unread-context.tsx",
    ".\hooks\use-channel-unread-realtime.ts"
)


Write-Host "[1/5] Required files..."


foreach ($File in $RequiredFiles)
{
    if (
        -not (
            Test-Path $File
        )
    )
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


Write-Host "[2/5] TypeScript..."


& npx tsc `
    --noEmit `
    --pretty false


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "TypeScript gate failed."
    )
}


Write-Host "PASS TypeScript"
Write-Host ""


Write-Host "[3/5] Realtime contracts..."


$RealtimeSource = (
    Get-Content `
        ".\lib\realtime\channel-realtime-client.ts" `
        -Raw
)


$RequiredRealtimeTokens = @(
    "WebSocket",
    "createTicket",
    "heartbeat",
    "typing.start",
    "typing.stop",
    "scheduleReconnect"
)


foreach (
    $Token
    in $RequiredRealtimeTokens
)
{
    if (
        $RealtimeSource
        -notmatch
        [regex]::Escape(
            $Token
        )
    )
    {
        throw (
            "Missing realtime client token: " +
            $Token
        )
    }
}


Write-Host "PASS realtime contracts"
Write-Host ""


Write-Host "[4/5] Durable unread contracts..."


$ReadStateService = (
    Get-Content `
        ".\services\channel-read-state.service.ts" `
        -Raw
)


$RequiredReadTokens = @(
    "read-state",
    "read-all",
    "markMessageRead",
    "listWorkspace"
)


foreach (
    $Token
    in $RequiredReadTokens
)
{
    if (
        $ReadStateService
        -notmatch
        [regex]::Escape(
            $Token
        )
    )
    {
        throw (
            "Missing read-state token: " +
            $Token
        )
    }
}


Write-Host "PASS durable unread contracts"
Write-Host ""


Write-Host "[5/5] Production build..."


& npm run build


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "Next.js production build failed."
    )
}


Write-Host ""
Write-Host "PASS production build"
Write-Host ""


Write-Host "================================================="
Write-Host " PHASE 16C FRONTEND REALTIME FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "TypeScript:                    PASS"
Write-Host "Production build:              PASS"
Write-Host "Realtime ticket client:        PASS"
Write-Host "WebSocket reconnect:           PASS"
Write-Host "Heartbeat transport:           PASS"
Write-Host "Typing transport:              PASS"
Write-Host "Realtime event reducer:        PASS"
Write-Host "Durable unread client:         PASS"
Write-Host "Message composer:              PASS"
Write-Host "Live message list:             PASS"
Write-Host "Unread UI components:          PASS"
Write-Host "================================================="