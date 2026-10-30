#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$ServiceName =
    "WorkforceOSAgent"

$DisplayName =
    "WorkforceOS Agent"

$Description =
    "WorkforceOS disclosed workforce monitoring agent."

$ProjectDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$RepositoryRoot =
    Resolve-Path `
        (
            Join-Path `
                $ProjectDirectory `
                "..\..\"
        )

$PublishDirectory =
    Join-Path `
        $RepositoryRoot `
        "artifacts\agent\win-x64"

$ExecutablePath =
    Join-Path `
        $PublishDirectory `
        "WorkforceOS.Agent.exe"

$ProgramDataDirectory =
    Join-Path `
        $env:ProgramData `
        "WorkforceOS\Agent"

Write-Host ""
Write-Host "WorkforceOS Agent Service Installation"
Write-Host "======================================"
Write-Host ""

if (
    -not (
        Test-Path `
            $ExecutablePath
    )
)
{
    throw @"
Published agent executable does not exist:

$ExecutablePath

Run scripts\publish-agent.ps1 first.
"@
}

Write-Host "Published executable:"
Write-Host $ExecutablePath
Write-Host ""

# =========================================================
# PRE-INSTALL AUTHENTICATION CHECK
# =========================================================

Write-Host "Verifying local enrollment and backend authentication..."
Write-Host ""

& $ExecutablePath `
    --status

if (
    $LASTEXITCODE -ne 0
)
{
    throw @"
Agent status/authentication verification failed.

Do not install the Windows Service yet.

Ensure:
1. Backend is running/reachable.
2. Agent has been enrolled.
3. --status succeeds.
4. Credential format has migrated to v2.
"@
}

Write-Host ""
Write-Host "Pre-install authentication check passed."

# =========================================================
# PROGRAMDATA
# =========================================================

New-Item `
    -ItemType Directory `
    -Force `
    $ProgramDataDirectory |
    Out-Null

$CredentialFile =
    Join-Path `
        $ProgramDataDirectory `
        "device-credentials.dat"

if (
    -not (
        Test-Path `
            $CredentialFile
    )
)
{
    throw @"
Device credential file was not found:

$CredentialFile

Enroll the agent before installing the Windows Service.
"@
}

# =========================================================
# STOP / REMOVE OLD SERVICE
# =========================================================

$ExistingService =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

if (
    $null -ne $ExistingService
)
{
    Write-Host ""
    Write-Host "Existing WorkforceOS Agent service found."

    if (
        $ExistingService.Status `
            -ne "Stopped"
    )
    {
        Write-Host "Stopping existing service..."

        Stop-Service `
            -Name $ServiceName `
            -Force

        $ExistingService.WaitForStatus(
            "Stopped",
            [TimeSpan]::FromSeconds(30)
        )
    }

    Write-Host "Removing existing service..."

    & sc.exe `
        delete `
        $ServiceName |
        Out-Host

    if (
        $LASTEXITCODE -ne 0
    )
    {
        throw "Unable to remove existing WorkforceOS Agent service."
    }

    Start-Sleep `
        -Seconds 2
}

# =========================================================
# DATA ACL
# =========================================================

Write-Host ""
Write-Host "Securing WorkforceOS ProgramData directory..."

& icacls.exe `
    $ProgramDataDirectory `
    /inheritance:r `
    /grant:r `
    "SYSTEM:(OI)(CI)F" `
    "BUILTIN\Administrators:(OI)(CI)F" `
    /T `
    /C |
    Out-Host

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Unable to secure WorkforceOS ProgramData directory."
}

# =========================================================
# CREATE SERVICE
# =========================================================

Write-Host ""
Write-Host "Creating Windows Service..."

$BinaryPath =
    "`"$ExecutablePath`""

New-Service `
    -Name $ServiceName `
    -BinaryPathName $BinaryPath `
    -DisplayName $DisplayName `
    -Description $Description `
    -StartupType Automatic

Write-Host "Configuring service recovery..."

& sc.exe `
    failure `
    $ServiceName `
    reset= 86400 `
    actions= restart/5000/restart/15000/restart/60000 |
    Out-Host

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Unable to configure service recovery."
}

& sc.exe `
    failureflag `
    $ServiceName `
    1 |
    Out-Host

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Unable to configure service failure actions."
}

# =========================================================
# START SERVICE
# =========================================================

Write-Host ""
Write-Host "Starting WorkforceOS Agent service..."

Start-Service `
    -Name $ServiceName

$Service =
    Get-Service `
        -Name $ServiceName

$Service.WaitForStatus(
    "Running",
    [TimeSpan]::FromSeconds(30)
)

$Service.Refresh()

if (
    $Service.Status `
        -ne "Running"
)
{
    throw "WorkforceOS Agent service did not enter Running state."
}

Write-Host ""
Write-Host "WorkforceOS Agent service installed successfully."
Write-Host ""
Write-Host "Service name:"
Write-Host $ServiceName
Write-Host ""
Write-Host "Status:"
Write-Host $Service.Status
Write-Host ""
Write-Host "Startup:"
Write-Host "Automatic"
Write-Host ""
Write-Host "Service identity:"
Write-Host "LocalSystem"