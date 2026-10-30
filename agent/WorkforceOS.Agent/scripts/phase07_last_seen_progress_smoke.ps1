#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$Executable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$ObservationSeconds = 35

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 07 Last-Seen Smoke"
Write-Host "============================================="
Write-Host ""

if (-not (Test-Path $Executable))
{
    throw "Published WorkforceOS Agent was not found."
}

function Get-Presence
{
    $Output =
        & $Executable `
            --presence `
            2>&1

    $ExitCode =
        $LASTEXITCODE

    $Text =
        $Output |
        Out-String

    if ($ExitCode -ne 0)
    {
        throw (
            "Presence command failed:`n" +
            $Text
        )
    }

    if (-not $Text.Contains("Online: True"))
    {
        throw (
            "Device is not online:`n" +
            $Text
        )
    }

    $LastSeenMatch =
        [regex]::Match(
            $Text,
            "(?m)^Last Seen:\s*(.+)$"
        )

    if (-not $LastSeenMatch.Success)
    {
        throw "Unable to extract Last Seen timestamp."
    }

    $LastSeenText =
        $LastSeenMatch.Groups[1].Value.Trim()

    $LastSeen =
        [DateTimeOffset]::Parse(
            $LastSeenText
        )

    return @{
        Text = $Text
        LastSeen = $LastSeen
    }
}

Write-Host "Reading first presence..."

$First =
    Get-Presence

Write-Host $First.Text.Trim()

Write-Host ""
Write-Host (
    "Waiting " +
    $ObservationSeconds +
    " seconds..."
)

Start-Sleep `
    -Seconds $ObservationSeconds

Write-Host ""
Write-Host "Reading second presence..."

$Second =
    Get-Presence

Write-Host $Second.Text.Trim()

if ($Second.LastSeen -le $First.LastSeen)
{
    throw (
        "Last Seen timestamp did not advance. " +
        "The recurring heartbeat is not confirmed."
    )
}

$Advance =
    $Second.LastSeen - $First.LastSeen

Write-Host ""
Write-Host (
    "Heartbeat timestamp advanced by " +
    [Math]::Round(
        $Advance.TotalSeconds,
        2
    ) +
    " seconds."
)

Write-Host ""
Write-Host "============================================="
Write-Host " PHASE 07 LAST-SEEN PROGRESS: PASS"
Write-Host "============================================="
Write-Host ""