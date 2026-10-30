#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"

$PublishedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$OutputDirectory =
    "C:\workforce-os\artifacts\diagnostics\phase08"

$HelperStdout =
    Join-Path `
        $OutputDirectory `
        "helper.stdout.log"

$HelperStderr =
    Join-Path `
        $OutputDirectory `
        "helper.stderr.log"

$EventLogOutput =
    Join-Path `
        $OutputDirectory `
        "windows-service-events.txt"

$HelperSeconds = 35

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Service Activity Diagnostics"
Write-Host "================================================="
Write-Host ""

New-Item `
    -ItemType Directory `
    -Path $OutputDirectory `
    -Force |
    Out-Null

Remove-Item `
    -Path $HelperStdout `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -Path $HelperStderr `
    -Force `
    -ErrorAction SilentlyContinue

Remove-Item `
    -Path $EventLogOutput `
    -Force `
    -ErrorAction SilentlyContinue


# ============================================================
# 1. VERIFY SERVICE
# ============================================================

Write-Host "[1/5] Verifying Windows service..."

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

if ($null -eq $Service)
{
    throw "Windows service not found: $ServiceName"
}

if ($Service.Status -ne "Running")
{
    throw "WorkforceOSAgent service is not running."
}

Write-Host "PASS service running"
Write-Host ""


# ============================================================
# 2. RECORD START TIME
# ============================================================

Write-Host "[2/5] Preparing diagnostic window..."

$StartTime =
    Get-Date

Write-Host "Diagnostic start: $StartTime"
Write-Host ""


# ============================================================
# 3. RUN HELPER
# ============================================================

Write-Host "[3/5] Running interactive helper..."

$Helper =
    Start-Process `
        -FilePath $PublishedExecutable `
        -ArgumentList "--activity-session-helper" `
        -RedirectStandardOutput $HelperStdout `
        -RedirectStandardError $HelperStderr `
        -PassThru

if ($null -eq $Helper)
{
    throw "Unable to start activity helper."
}

Write-Host "Helper PID: $($Helper.Id)"
Write-Host "Use keyboard or mouse during the next $HelperSeconds seconds."
Write-Host ""

Start-Sleep `
    -Seconds $HelperSeconds

$Helper.Refresh()

if (-not $Helper.HasExited)
{
    Stop-Process `
        -Id $Helper.Id `
        -Force

    Start-Sleep `
        -Seconds 2
}

Write-Host "PASS helper diagnostic window completed"
Write-Host ""


# ============================================================
# 4. SHOW HELPER LOGS
# ============================================================

Write-Host "[4/5] Helper logs..."
Write-Host ""

Write-Host "----- HELPER STDOUT -----"

if (Test-Path $HelperStdout)
{
    Get-Content `
        $HelperStdout
}
else
{
    Write-Host "<no stdout>"
}

Write-Host ""
Write-Host "----- HELPER STDERR -----"

if (Test-Path $HelperStderr)
{
    Get-Content `
        $HelperStderr
}
else
{
    Write-Host "<no stderr>"
}

Write-Host ""


# ============================================================
# 5. CAPTURE WINDOWS SERVICE EVENTS
# ============================================================

Write-Host "[5/5] Capturing Windows service-related events..."
Write-Host ""

$RelevantEvents =
    Get-WinEvent `
        -FilterHashtable @{
            LogName = "Application"
            StartTime = $StartTime.AddMinutes(-1)
        } `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Message -like "*WorkforceOS*" `
        -or $_.ProviderName -like "*WorkforceOS*" `
        -or $_.Message -like "*ActivityServiceReceiver*" `
        -or $_.Message -like "*ActivityBackendReportingWorker*" `
        -or $_.Message -like "*ActivityPipe*" `
        -or $_.Message -like "*activity-state*"
    }

if ($null -eq $RelevantEvents)
{
    Write-Host "No matching Application log events found."
}
else
{
    $RelevantEvents |
        Select-Object `
            TimeCreated,
            LevelDisplayName,
            ProviderName,
            Id,
            Message |
        Format-List |
        Out-String |
        Tee-Object `
            -FilePath $EventLogOutput |
        Write-Host
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 08 SERVICE DIAGNOSTICS COMPLETE"
Write-Host "================================================="
Write-Host ""
Write-Host "Files:"
Write-Host $HelperStdout
Write-Host $HelperStderr
Write-Host $EventLogOutput
Write-Host ""