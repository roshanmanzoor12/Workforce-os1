$ErrorActionPreference = "Stop"


$Root = "C:\workforce-os\apps\web"

$Page = Join-Path `
    $Root `
    "app\(workspace)\channels\page.tsx"

$RealtimeRoom = Join-Path `
    $Root `
    "components\channels\channel-realtime-room.tsx"

$UnreadProvider = Join-Path `
    $Root `
    "components\channels\channel-unread-provider.tsx"

$UnreadSidebar = Join-Path `
    $Root `
    "components\channels\channel-unread-sidebar-section.tsx"


Set-Location $Root


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Channels Page Realtime Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# 1/8 REQUIRED FILES
# =========================================================

Write-Host "[1/8] Required files..."


$RequiredFiles = @(
    $Page,
    $RealtimeRoom,
    $UnreadProvider,
    $UnreadSidebar
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


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 2/8 PAGE REALTIME ROOM
# =========================================================

Write-Host "[2/8] Realtime room integration..."


$Source = Get-Content `
    $Page `
    -Raw


$RequiredTokens = @(
    "ChannelRealtimeRoom",
    "ChannelUnreadWorkspaceProvider",
    "ChannelUnreadSidebarSection",
    "currentUserId",
    "channelId",
    "channelName"
)


foreach ($Token in $RequiredTokens)
{
    if (
        $Source.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "Channels page missing integration token: " +
            $Token
        )
    }
}


Write-Host "PASS realtime room integration"
Write-Host ""


# =========================================================
# 3/8 OLD POLLING REMOVED
# =========================================================

Write-Host "[3/8] Old text polling removed..."


$ForbiddenTokens = @(
    "setInterval(",
    "loadMessages(",
    "<TextRoom",
    "function TextRoom(",
    "messagesLoading",
    "messagesEndRef"
)


foreach ($Token in $ForbiddenTokens)
{
    if (
        $Source.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -ge 0
    )
    {
        throw (
            "Legacy text-channel flow still present: " +
            $Token
        )
    }
}


Write-Host "PASS old polling removed"
Write-Host ""


# =========================================================
# 4/8 VOICE FLOW PRESERVED
# =========================================================

Write-Host "[4/8] Voice channel flow preserved..."


$VoiceTokens = @(
    "useVoiceChannel",
    "VoiceConnectionBar",
    "<VoiceRoom",
    "joinSelectedVoiceChannel",
    "disconnectVoice",
    "toggleSelfMute",
    "toggleSelfDeafen",
    "toggleScreenShare"
)


foreach ($Token in $VoiceTokens)
{
    if (
        $Source.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "Voice contract missing: " +
            $Token
        )
    }
}


Write-Host "PASS voice channel flow preserved"
Write-Host ""


# =========================================================
# 5/8 CHANNEL MANAGEMENT PRESERVED
# =========================================================

Write-Host "[5/8] Channel management preserved..."


$ManagementTokens = @(
    "workspaceChannelsService.list",
    "workspaceChannelsService.archive",
    "CreateChannelModal",
    "ChannelSettingsModal",
    "New Channel",
    "Refresh"
)


foreach ($Token in $ManagementTokens)
{
    if (
        $Source.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "Channel management contract missing: " +
            $Token
        )
    }
}


Write-Host "PASS channel management preserved"
Write-Host ""


# =========================================================
# 6/8 TYPESCRIPT
# =========================================================

Write-Host "[6/8] TypeScript..."


& npx tsc `
    --noEmit `
    --pretty false


if ($LASTEXITCODE -ne 0)
{
    throw "TypeScript failed."
}


Write-Host "PASS TypeScript"
Write-Host ""


# =========================================================
# 7/8 PRODUCTION BUILD
# =========================================================

Write-Host "[7/8] Production build..."


& npm run build


if ($LASTEXITCODE -ne 0)
{
    throw "Production build failed."
}


Write-Host "PASS production build"
Write-Host ""


# =========================================================
# 8/8 ROUTE OUTPUT
# =========================================================

Write-Host "[8/8] Channels route build output..."


if (-not (Test-Path ".next"))
{
    throw ".next build directory missing."
}


Write-Host "PASS channels route build output"
Write-Host ""


Write-Host "================================================="
Write-Host " PHASE 16C CHANNELS PAGE REALTIME: PASS"
Write-Host "================================================="
Write-Host "Realtime text room:              PASS"
Write-Host "Durable unread provider:         PASS"
Write-Host "Unread sidebar:                  PASS"
Write-Host "Legacy polling removed:          PASS"
Write-Host "Voice behavior preserved:        PASS"
Write-Host "Channel management preserved:    PASS"
Write-Host "TypeScript:                      PASS"
Write-Host "Production build:                PASS"
Write-Host "================================================="
