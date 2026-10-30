$ErrorActionPreference = "Stop"


$Root = "C:\workforce-os\apps\web"

$LiveMessageFile = Join-Path `
    $Root `
    "components\channels\channel-live-message-list.tsx"

$MessageItemFile = Join-Path `
    $Root `
    "components\channels\channel-message-item.tsx"

$RealtimeRoomFile = Join-Path `
    $Root `
    "components\channels\channel-realtime-room.tsx"


Set-Location $Root


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Live Message Contract Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# 1/7 REQUIRED FILES
# =========================================================

Write-Host "[1/7] Required files..."


$RequiredFiles = @(
    $LiveMessageFile,
    $MessageItemFile,
    $RealtimeRoomFile
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
# 2/7 LIVE MESSAGE PROP CONTRACT
# =========================================================

Write-Host "[2/7] ChannelLiveMessageList currentUserId contract..."


$LiveMessageSource = Get-Content `
    $LiveMessageFile `
    -Raw


$RequiredLiveMessageTokens = @(
    "interface ChannelLiveMessageListProps",
    "currentUserId?",
    "currentUserId = null",
    "currentUserId={"
)


foreach ($Token in $RequiredLiveMessageTokens)
{
    if (
        $LiveMessageSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "ChannelLiveMessageList missing token: " +
            $Token
        )
    }
}


Write-Host "PASS ChannelLiveMessageList currentUserId contract"
Write-Host ""


# =========================================================
# 3/7 MESSAGE ITEM PROP CONTRACT
# =========================================================

Write-Host "[3/7] ChannelMessageItem currentUserId contract..."


$MessageItemSource = Get-Content `
    $MessageItemFile `
    -Raw


$RequiredMessageItemTokens = @(
    "currentUserId?",
    "currentUserId"
)


foreach ($Token in $RequiredMessageItemTokens)
{
    if (
        $MessageItemSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "ChannelMessageItem missing token: " +
            $Token
        )
    }
}


Write-Host "PASS ChannelMessageItem currentUserId contract"
Write-Host ""


# =========================================================
# 4/7 REALTIME ROOM CONTRACT
# =========================================================

Write-Host "[4/7] ChannelRealtimeRoom propagation..."


$RealtimeRoomSource = Get-Content `
    $RealtimeRoomFile `
    -Raw


$RequiredRealtimeTokens = @(
    "currentUserId",
    "<ChannelLiveMessageList",
    "currentUserId={"
)


foreach ($Token in $RequiredRealtimeTokens)
{
    if (
        $RealtimeRoomSource.IndexOf(
            $Token,
            [System.StringComparison]::Ordinal
        ) -lt 0
    )
    {
        throw (
            "ChannelRealtimeRoom missing token: " +
            $Token
        )
    }
}


Write-Host "PASS ChannelRealtimeRoom propagation"
Write-Host ""


# =========================================================
# 5/7 DUPLICATE FILE CHECK
# =========================================================

Write-Host "[5/7] Duplicate component check..."


$Matches = @(
    Get-ChildItem `
        -Path $Root `
        -Filter "channel-live-message-list.tsx" `
        -Recurse `
        -File
)


if ($Matches.Count -ne 1)
{
    Write-Host ""
    Write-Host "Found files:"

    foreach ($Match in $Matches)
    {
        Write-Host (
            " - " +
            $Match.FullName
        )
    }

    throw (
        "Expected exactly one " +
        "channel-live-message-list.tsx, found " +
        $Matches.Count
    )
}


$ExpectedPath = (
    [System.IO.Path]::GetFullPath(
        $LiveMessageFile
    )
)

$ActualPath = (
    [System.IO.Path]::GetFullPath(
        $Matches[0].FullName
    )
)


if (
    $ActualPath -ne
    $ExpectedPath
)
{
    throw (
        "Unexpected ChannelLiveMessageList path: " +
        $ActualPath
    )
}


Write-Host "PASS duplicate component check"
Write-Host ""


# =========================================================
# 6/7 TYPESCRIPT
# =========================================================

Write-Host "[6/7] TypeScript..."


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
# 7/7 PRODUCTION BUILD
# =========================================================

Write-Host "[7/7] Production build..."


& npm run build


if ($LASTEXITCODE -ne 0)
{
    throw "Production build failed."
}


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C LIVE MESSAGE CONTRACT: PASS"
Write-Host "================================================="
Write-Host "Required files:                 PASS"
Write-Host "Live message current user:      PASS"
Write-Host "Message item current user:      PASS"
Write-Host "Realtime propagation:           PASS"
Write-Host "Duplicate component check:      PASS"
Write-Host "TypeScript:                     PASS"
Write-Host "Production build:               PASS"
Write-Host "================================================="