#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"
$ProjectDirectory = Split-Path -Parent $PSScriptRoot
$PublishDirectory = "C:\workforce-os\artifacts\agent\win-x64"
$ExecutablePath = Join-Path $PublishDirectory "WorkforceOS.Agent.exe"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 07 Publish + Restart"
Write-Host "============================================="
Write-Host ""

# =========================================================
# VALIDATE SERVICE
# =========================================================

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

Write-Host "Current service status:"
Write-Host $Service.Status
Write-Host ""

# =========================================================
# STOP SERVICE
# =========================================================

if ($Service.Status -ne "Stopped")
{
    Write-Host "Stopping existing WorkforceOS Agent service..."

    Stop-Service `
        -Name $ServiceName `
        -Force `
        -ErrorAction Stop

    $Service =
        Get-Service `
            -Name $ServiceName `
            -ErrorAction Stop

    $Service.WaitForStatus(
        "Stopped",
        [TimeSpan]::FromSeconds(20)
    )

    $Service =
        Get-Service `
            -Name $ServiceName `
            -ErrorAction Stop

    if ($Service.Status -ne "Stopped")
    {
        throw "WorkforceOS Agent service did not stop."
    }

    Write-Host "Service stopped."
}
else
{
    Write-Host "Service is already stopped."
}

# =========================================================
# BUILD + PUBLISH
# =========================================================

Push-Location $ProjectDirectory

try
{
    Write-Host ""
    Write-Host "Building Release configuration..."
    Write-Host ""

    dotnet build `
        --configuration Release

    if ($LASTEXITCODE -ne 0)
    {
        throw "WorkforceOS Agent Release build failed."
    }

    Write-Host ""
    Write-Host "Release build passed."

    Write-Host ""
    Write-Host "Cleaning publish directory..."

    if (Test-Path $PublishDirectory)
    {
        Remove-Item `
            -Path $PublishDirectory `
            -Recurse `
            -Force `
            -ErrorAction Stop
    }

    New-Item `
        -ItemType Directory `
        -Path $PublishDirectory `
        -Force |
        Out-Null

    Write-Host ""
    Write-Host "Publishing WorkforceOS Agent for win-x64..."
    Write-Host ""

    dotnet publish `
        --configuration Release `
        --runtime win-x64 `
        --self-contained false `
        --output $PublishDirectory

    if ($LASTEXITCODE -ne 0)
    {
        throw "WorkforceOS Agent publish failed."
    }

    Write-Host ""
    Write-Host "Publish completed."
}
finally
{
    Pop-Location
}

# =========================================================
# VERIFY PUBLISHED EXECUTABLE
# =========================================================

if (-not (Test-Path $ExecutablePath))
{
    throw (
        "Published WorkforceOS Agent executable was not found: " +
        $ExecutablePath
    )
}

$Executable =
    Get-Item `
        -Path $ExecutablePath `
        -ErrorAction Stop

if ($Executable.Length -le 0)
{
    throw "Published WorkforceOS Agent executable is empty."
}

Write-Host ""
Write-Host "Published executable:"
Write-Host $ExecutablePath

Write-Host ""
Write-Host "Executable size:"
Write-Host $Executable.Length

# =========================================================
# VERIFY SERVICE CONFIGURATION
# =========================================================

$ServiceConfiguration =
    Get-CimInstance `
        -ClassName Win32_Service `
        -Filter "Name='$ServiceName'"

if ($null -eq $ServiceConfiguration)
{
    throw "Unable to read WorkforceOS Agent Windows service configuration."
}

$ConfiguredPath =
    [string]$ServiceConfiguration.PathName

Write-Host ""
Write-Host "Configured service binary:"
Write-Host $ConfiguredPath

# PowerShell -like comparison is case-insensitive by default.
# Service PathName may contain quotes around the executable.
$ExpectedPathPattern =
    "*" + $ExecutablePath + "*"

if ($ConfiguredPath -notlike $ExpectedPathPattern)
{
    throw (
        "Windows service is not configured to use the Phase 07 published executable."
    )
}

Write-Host "Service binary path verified."

# =========================================================
# START SERVICE
# =========================================================

Write-Host ""
Write-Host "Starting WorkforceOS Agent service..."

Start-Service `
    -Name $ServiceName `
    -ErrorAction Stop

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

$Service.WaitForStatus(
    "Running",
    [TimeSpan]::FromSeconds(20)
)

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw "WorkforceOS Agent service did not start."
}

# =========================================================
# VERIFY PROCESS
# =========================================================

Start-Sleep -Seconds 3

$ServiceConfiguration =
    Get-CimInstance `
        -ClassName Win32_Service `
        -Filter "Name='$ServiceName'"

if ($null -eq $ServiceConfiguration)
{
    throw "Unable to reload WorkforceOS Agent service configuration."
}

$ProcessId =
    [int]$ServiceConfiguration.ProcessId

if ($ProcessId -le 0)
{
    throw "WorkforceOS Agent service process is not running."
}

$AgentProcess =
    Get-Process `
        -Id $ProcessId `
        -ErrorAction Stop

if ($AgentProcess.HasExited)
{
    throw "WorkforceOS Agent process exited after service startup."
}

# =========================================================
# VERIFY SERVICE STABILITY
# =========================================================

Start-Sleep -Seconds 2

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw (
        "WorkforceOS Agent service did not remain running after startup."
    )
}

# =========================================================
# RESULT
# =========================================================

Write-Host ""
Write-Host "Service Status:"
Write-Host $Service.Status

Write-Host ""
Write-Host "Service Process ID:"
Write-Host $ProcessId

Write-Host ""
Write-Host "Published Binary:"
Write-Host $ExecutablePath

Write-Host ""
Write-Host "============================================="
Write-Host " PHASE 07 PUBLISH + RESTART: PASS"
Write-Host "============================================="
Write-Host ""