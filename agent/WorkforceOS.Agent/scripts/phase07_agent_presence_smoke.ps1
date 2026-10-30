$ErrorActionPreference = "Stop"

$ProjectDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

Write-Host ""
Write-Host "========================================"
Write-Host " WorkforceOS Phase 07 Presence Smoke"
Write-Host "========================================"
Write-Host ""

Push-Location `
    $ProjectDirectory

try
{
    Write-Host "Building WorkforceOS Agent..."
    Write-Host ""

    dotnet build

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw "WorkforceOS Agent build failed."
    }

    Write-Host ""
    Write-Host "Checking enrollment/authentication..."
    Write-Host ""

    $StatusOutput =
        dotnet run `
            --no-build `
            -- `
            --status `
            2>&1

    $StatusExitCode =
        $LASTEXITCODE

    $StatusText =
        (
            $StatusOutput |
            Out-String
        )

    Write-Host $StatusText.Trim()

    if (
        $StatusExitCode -ne 0
    )
    {
        throw (
            "Agent status check failed with exit code " +
            $StatusExitCode
        )
    }

    if (
        -not $StatusText.Contains(
            "Backend authentication succeeded."
        )
    )
    {
        throw (
            "Backend authentication was not confirmed."
        )
    }

    Write-Host ""
    Write-Host "Checking device presence..."
    Write-Host ""

    $PresenceOutput =
        dotnet run `
            --no-build `
            -- `
            --presence `
            2>&1

    $PresenceExitCode =
        $LASTEXITCODE

    $PresenceText =
        (
            $PresenceOutput |
            Out-String
        )

    Write-Host $PresenceText.Trim()

    if (
        $PresenceExitCode -ne 0
    )
    {
        throw (
            "Agent presence check failed with exit code " +
            $PresenceExitCode
        )
    }

    if (
        -not $PresenceText.Contains(
            "Device UUID:"
        )
    )
    {
        throw (
            "Presence response did not include device UUID."
        )
    }

    if (
        -not $PresenceText.Contains(
            "Online Timeout Seconds:"
        )
    )
    {
        throw (
            "Presence response did not include online timeout."
        )
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host " PHASE 07 AGENT PRESENCE SMOKE: PASS"
    Write-Host "========================================"
    Write-Host ""
}
finally
{
    Pop-Location
}