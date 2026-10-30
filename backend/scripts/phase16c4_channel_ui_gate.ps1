$ErrorActionPreference = "Stop"


$Root = (
    "C:\workforce-os\apps\web"
)


Set-Location $Root


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C.4 Channel UI Gate"
Write-Host "================================================="
Write-Host ""


$Files = @(
    ".\components\channels\channel-message-item.tsx",
    ".\components\channels\channel-live-message-list.tsx",
    ".\components\channels\channel-realtime-room.tsx",
    ".\components\channels\channel-message-composer.tsx",
    ".\components\channels\channel-realtime-status.tsx",
    ".\components\channels\channel-typing-indicator.tsx",
    ".\components\channels\channel-unread-badge.tsx",
    ".\components\channels\channel-sidebar-unread-row.tsx",
    ".\components\channels\channel-unread-provider.tsx",
    ".\components\channels\channel-unread-summary.tsx",
    ".\components\channels\channel-unread-sidebar-section.tsx",
    ".\contexts\channel-unread-context.tsx",
    ".\hooks\use-channel-realtime.ts",
    ".\hooks\use-channel-read-state.ts",
    ".\hooks\use-workspace-channel-unread.ts",
    ".\hooks\use-active-channel-read-sync.ts",
    ".\lib\realtime\channel-message-dedupe.ts"
)


Write-Host "[1/4] Required files..."


foreach (
    $File in $Files
)
{
    if (
        -not (
            Test-Path $File
        )
    )
    {
        throw (
            "Missing file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


Write-Host "[2/4] TypeScript..."


& npx tsc `
    --noEmit `
    --pretty false


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "TypeScript failed."
    )
}


Write-Host "PASS TypeScript"
Write-Host ""


Write-Host "[3/4] Contract checks..."


$Room = (
    Get-Content `
        ".\components\channels\channel-realtime-room.tsx" `
        -Raw
)


$MessageItem = (
    Get-Content `
        ".\components\channels\channel-message-item.tsx" `
        -Raw
)


$Sidebar = (
    Get-Content `
        ".\components\channels\channel-sidebar-unread-row.tsx" `
        -Raw
)


$RequiredRoomTokens = @(
    "latest",
    "markMessageRead",
    "markAllRead",
    "currentUserId",
    "resume",
    "typingStart",
    "typingStop"
)


foreach (
    $Token
    in $RequiredRoomTokens
)
{
    if (
        $Room
        -notmatch
        [regex]::Escape(
            $Token
        )
    )
    {
        throw (
            "Room contract missing: " +
            $Token
        )
    }
}


if (
    $MessageItem
    -notmatch
    "currentUserId"
)
{
    throw (
        "ChannelMessageItem currentUserId contract missing."
    )
}


if (
    $Sidebar
    -notmatch
    "ChannelUnreadBadge"
)
{
    throw (
        "Unread badge integration missing."
    )
}


Write-Host "PASS contracts"
Write-Host ""


Write-Host "[4/4] Production build..."


& npm run build


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "Production build failed."
    )
}


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C.4 CHANNEL UI: PASS"
Write-Host "================================================="
Write-Host "TypeScript:                    PASS"
Write-Host "Production build:              PASS"
Write-Host "Realtime room:                 PASS"
Write-Host "Current user propagation:      PASS"
Write-Host "Read cursor integration:       PASS"
Write-Host "Unread row foundation:         PASS"
Write-Host "Message dedupe helper:         PASS"
Write-Host "================================================="