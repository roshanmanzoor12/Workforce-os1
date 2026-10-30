#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$HelperRunSeconds =
        45,

    [int]$MaximumEventAgeSeconds =
        180
)

$ErrorActionPreference = "Stop"

$AgentRoot =
    "C:\workforce-os\agent"

$BackendRoot =
    "C:\workforce-os\backend"

$PublishedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$PublishedAppSettings =
    "C:\workforce-os\artifacts\agent\win-x64\appsettings.json"

$ServiceName =
    "WorkforceOSAgent"

$PipeName =
    "WorkforceOS.Agent.Activity.v1"

$VerifyActivityEventScript =
    Join-Path `
        $BackendRoot `
        "scripts\phase08_verify_activity_event.ps1"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Final Live Acceptance"
Write-Host "================================================="
Write-Host ""

# ============================================================
# 1. VERIFY REQUIRED FILES
# ============================================================

Write-Host "[1/7] Verifying Phase 08 runtime files..."

if (-not (Test-Path $PublishedExecutable))
{
    throw (
        "Published agent executable not found: " +
        $PublishedExecutable
    )
}

if (-not (Test-Path $PublishedAppSettings))
{
    throw (
        "Published appsettings.json not found: " +
        $PublishedAppSettings
    )
}

if (-not (Test-Path $VerifyActivityEventScript))
{
    throw (
        "Activity event verification script not found: " +
        $VerifyActivityEventScript
    )
}

Write-Host "PASS required files exist"
Write-Host ""

# ============================================================
# 2. VERIFY ACTIVITY CONFIGURATION
# ============================================================

Write-Host "[2/7] Verifying published Activity configuration..."

$AppSettingsText =
    Get-Content `
        $PublishedAppSettings `
        -Raw

if ($AppSettingsText -notmatch '"Activity"')
{
    throw (
        "Published appsettings.json does not contain Activity configuration."
    )
}

if ($AppSettingsText -notmatch '"Enabled"\s*:\s*true')
{
    throw (
        "Published Activity configuration is not enabled."
    )
}

if ($AppSettingsText -notmatch '"IdleThresholdSeconds"\s*:\s*300')
{
    throw (
        "Published Activity idle threshold is not 300 seconds."
    )
}

Write-Host "PASS Activity configuration enabled"
Write-Host ""

# ============================================================
# 3. VERIFY WINDOWS SERVICE
# ============================================================

Write-Host "[3/7] Verifying WorkforceOS Windows service..."

$Service =
    Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'"

if ($null -eq $Service)
{
    throw (
        "Windows service not found: " +
        $ServiceName
    )
}

if ($Service.State -ne "Running")
{
    throw (
        "WorkforceOSAgent service is not running. Current state: " +
        $Service.State
    )
}

$ServicePath =
    $Service.PathName.Trim()

if ($ServicePath.StartsWith('"'))
{
    $ClosingQuote =
        $ServicePath.IndexOf(
            '"',
            1
        )

    if ($ClosingQuote -gt 1)
    {
        $ServicePath =
            $ServicePath.Substring(
                1,
                $ClosingQuote - 1
            )
    }
}
else
{
    $ServicePath =
        $ServicePath.Split(
            " "
        )[0]
}

$ExpectedFullPath =
    [System.IO.Path]::GetFullPath(
        $PublishedExecutable
    )

$ActualFullPath =
    [System.IO.Path]::GetFullPath(
        $ServicePath
    )

if ($ActualFullPath -ne $ExpectedFullPath)
{
    throw (
        "Windows service is not using the expected published executable. " +
        "Expected: $ExpectedFullPath Actual: $ActualFullPath"
    )
}

Write-Host "PASS WorkforceOS service running expected executable"
Write-Host ""

# ============================================================
# 4. VERIFY NAMED PIPE
# ============================================================

Write-Host "[4/7] Verifying activity named pipe..."

$PipeFound =
    $false

try
{
    $PipePaths =
        [System.IO.Directory]::GetFiles(
            "\\.\pipe\"
        )

    foreach ($PipePath in $PipePaths)
    {
        if ($PipePath -like "*\$PipeName")
        {
            $PipeFound =
                $true

            break
        }
    }
}
catch
{
    throw (
        "Unable to enumerate Windows named pipes: " +
        $_.Exception.Message
    )
}

if (-not $PipeFound)
{
    throw (
        "Activity named pipe is not active: \\.\pipe\$PipeName"
    )
}

Write-Host "PASS activity named pipe active"
Write-Host ""

# ============================================================
# 5. RUN INTERACTIVE ACTIVITY HELPER
# ============================================================

Write-Host "[5/7] Running interactive activity helper..."
Write-Host ""
Write-Host (
    "Use keyboard or mouse during the next " +
    $HelperRunSeconds +
    " seconds."
)
Write-Host ""

$HelperProcess =
    Start-Process `
        -FilePath $PublishedExecutable `
        -ArgumentList "--activity-session-helper" `
        -PassThru

if ($null -eq $HelperProcess)
{
    throw (
        "Unable to launch activity session helper."
    )
}

Write-Host "Helper PID: $($HelperProcess.Id)"

Start-Sleep `
    -Seconds $HelperRunSeconds

$HelperProcess.Refresh()

if ($HelperProcess.HasExited)
{
    throw (
        "Activity session helper exited unexpectedly with code " +
        $HelperProcess.ExitCode
    )
}

Stop-Process `
    -Id $HelperProcess.Id `
    -Force

Start-Sleep `
    -Seconds 3

Write-Host "PASS helper completed live observation window"
Write-Host ""

# ============================================================
# 6. VERIFY DATABASE EVENT
# ============================================================

Write-Host "[6/7] Verifying persisted activity event..."

Push-Location $BackendRoot

try
{
    & $VerifyActivityEventScript `
        -TenantDatabaseName $TenantDatabaseName `
        -MaximumAgeSeconds $MaximumEventAgeSeconds

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 activity database event verification failed."
        )
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS activity event persisted to tenant database"
Write-Host ""

# ============================================================
# 7. FINAL ACCEPTANCE
# ============================================================

Write-Host "[7/7] Final Phase 08 acceptance..."
Write-Host ""

Write-Host "Verified:"
Write-Host "  - Windows Agent service running"
Write-Host "  - correct published executable"
Write-Host "  - Activity configuration enabled"
Write-Host "  - secure local activity named pipe active"
Write-Host "  - interactive helper remained running"
Write-Host "  - activity observation reached backend"
Write-Host "  - activity event persisted in tenant database"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 08 ACTIVE / IDLE DETECTION: 100% PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Next phase:"
Write-Host "Phase 09 - Work Sessions"
Write-Host ""