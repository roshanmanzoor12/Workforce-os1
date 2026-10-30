#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"

$ExpectedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$PublishedAppSettings =
    "C:\workforce-os\artifacts\agent\win-x64\appsettings.json"

$PipeName =
    "WorkforceOS.Agent.Activity.v1"

$HelperSeconds =
    20

$DiagnosticDirectory =
    "C:\workforce-os\artifacts\diagnostics\phase08"

$HelperStdout =
    Join-Path `
        $DiagnosticDirectory `
        "activity-helper.stdout.log"

$HelperStderr =
    Join-Path `
        $DiagnosticDirectory `
        "activity-helper.stderr.log"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Pipeline Diagnostics"
Write-Host "================================================="
Write-Host ""

New-Item `
    -ItemType Directory `
    -Path $DiagnosticDirectory `
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


# ============================================================
# 1. SERVICE PATH
# ============================================================

Write-Host "[1/6] Checking Windows service executable..."

$ServiceInfo =
    Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'"

if ($null -eq $ServiceInfo)
{
    throw "Windows service not found: $ServiceName"
}

Write-Host "Service state: $($ServiceInfo.State)"
Write-Host "Service path: $($ServiceInfo.PathName)"

if ($ServiceInfo.State -ne "Running")
{
    throw "WorkforceOSAgent service is not running."
}

$ServicePath =
    $ServiceInfo.PathName.Trim()

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
        $ExpectedExecutable
    )

$ActualFullPath =
    [System.IO.Path]::GetFullPath(
        $ServicePath
    )

if ($ActualFullPath -ne $ExpectedFullPath)
{
    throw (
        "Service is not using the expected Phase 08 published executable. " +
        "Expected: $ExpectedFullPath Actual: $ActualFullPath"
    )
}

Write-Host "PASS service uses expected published executable"
Write-Host ""


# ============================================================
# 2. PUBLISHED FILES
# ============================================================

Write-Host "[2/6] Checking published Phase 08 files..."

if (-not (Test-Path $ExpectedExecutable))
{
    throw "Published executable not found: $ExpectedExecutable"
}

if (-not (Test-Path $PublishedAppSettings))
{
    throw "Published appsettings.json not found."
}

$ExecutableInfo =
    Get-Item `
        $ExpectedExecutable

Write-Host "Published executable modified: $($ExecutableInfo.LastWriteTime)"

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

Write-Host "PASS published Activity configuration exists"
Write-Host ""


# ============================================================
# 3. NAMED PIPE
# ============================================================

Write-Host "[3/6] Checking Phase 08 named pipe..."

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
    Write-Host (
        "INFO unable to enumerate named pipes directly: " +
        $_.Exception.Message
    )
}

if (-not $PipeFound)
{
    Write-Host ""
    Write-Host "FAIL named pipe not found:"
    Write-Host "\\.\pipe\$PipeName"
    Write-Host ""
    Write-Host "This normally means ActivityServiceReceiver is not running"
    Write-Host "inside the installed Windows service."
    Write-Host ""

    throw "Phase 08 activity named pipe is not active."
}

Write-Host "PASS named pipe active: \\.\pipe\$PipeName"
Write-Host ""


# ============================================================
# 4. RUN HELPER WITH CAPTURED LOGS
# ============================================================

Write-Host "[4/6] Running interactive helper with captured logs..."

$HelperProcess =
    Start-Process `
        -FilePath $ExpectedExecutable `
        -ArgumentList "--activity-session-helper" `
        -RedirectStandardOutput $HelperStdout `
        -RedirectStandardError $HelperStderr `
        -PassThru

if ($null -eq $HelperProcess)
{
    throw "Unable to start activity session helper."
}

Write-Host "Helper PID: $($HelperProcess.Id)"

Start-Sleep `
    -Seconds $HelperSeconds

$HelperProcess.Refresh()

if ($HelperProcess.HasExited)
{
    Write-Host "Helper exited with code: $($HelperProcess.ExitCode)"
}
else
{
    Stop-Process `
        -Id $HelperProcess.Id `
        -Force

    Start-Sleep `
        -Seconds 2
}

Write-Host "PASS helper diagnostic run completed"
Write-Host ""


# ============================================================
# 5. DISPLAY HELPER LOGS
# ============================================================

Write-Host "[5/6] Reading helper output..."
Write-Host ""

Write-Host "----- STDOUT -----"

if (Test-Path $HelperStdout)
{
    Get-Content `
        $HelperStdout
}
else
{
    Write-Host "<no stdout file>"
}

Write-Host ""
Write-Host "----- STDERR -----"

if (Test-Path $HelperStderr)
{
    Get-Content `
        $HelperStderr
}
else
{
    Write-Host "<no stderr file>"
}

Write-Host ""


# ============================================================
# 6. FINAL CHECK
# ============================================================

Write-Host "[6/6] Diagnostic summary..."

$StandardErrorText =
    ""

if (Test-Path $HelperStderr)
{
    $StandardErrorText =
        Get-Content `
            $HelperStderr `
            -Raw
}

if ($StandardErrorText -match "Unauthorized")
{
    throw (
        "Activity helper was rejected by local IPC security."
    )
}

if ($StandardErrorText -match "Timed out connecting")
{
    throw (
        "Activity helper could not connect to the Windows service named pipe."
    )
}

if ($StandardErrorText -match "Session 0")
{
    throw (
        "Activity helper was launched outside an interactive user session."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 08 PIPELINE DIAGNOSTIC COMPLETE"
Write-Host "================================================="
Write-Host ""
Write-Host "Diagnostic files:"
Write-Host $HelperStdout
Write-Host $HelperStderr
Write-Host ""