$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$ScriptsRoot = Join-Path $BackendRoot "scripts"
$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"

Set-Location $BackendRoot

$Results = @()


function Add-Result {
    param(
        [string] $Name,
        [string] $Status
    )

    $script:Results += [PSCustomObject]@{
        Gate   = $Name
        Status = $Status
    }
}


function Show-Summary {
    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 16D CERTIFICATION SUMMARY"
    Write-Host "================================================="
    Write-Host ""

    $script:Results |
        Format-Table -AutoSize
}


function Stop-Certification {
    param(
        [string] $Message
    )

    Write-Host ""
    Write-Host "FAIL:" $Message

    Show-Summary

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 16D FINAL CERTIFICATION FAIL"
    Write-Host "================================================="

    exit 1
}


function Invoke-PythonGate {
    param(
        [string] $Name,
        [string] $FileName
    )

    $Path = Join-Path $ScriptsRoot $FileName

    Write-Host ""
    Write-Host "================================================="
    Write-Host " $Name"
    Write-Host "================================================="
    Write-Host ""

    if (-not (Test-Path $Path)) {
        Add-Result $Name "FAIL"
        Stop-Certification "Missing Python gate: $Path"
    }

    & $Python -m py_compile $Path
    $CompileExit = $LASTEXITCODE

    if ($CompileExit -ne 0) {
        Add-Result $Name "FAIL"
        Stop-Certification "$Name compile failed."
    }

    Write-Host "PASS: Compile"

    & $Python $Path
    $GateExit = $LASTEXITCODE

    if ($GateExit -ne 0) {
        Add-Result $Name "FAIL"
        Stop-Certification "$Name failed with exit code $GateExit."
    }

    Add-Result $Name "PASS"

    Write-Host ""
    Write-Host "PASS:" $Name
}


function Invoke-PowerShellGate {
    param(
        [string] $Name,
        [string] $Path
    )

    Write-Host ""
    Write-Host "================================================="
    Write-Host " $Name"
    Write-Host "================================================="
    Write-Host ""

    if (-not (Test-Path $Path)) {
        Add-Result $Name "FAIL"
        Stop-Certification "Missing PowerShell gate: $Path"
    }

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Path

    $GateExit = $LASTEXITCODE

    if ($GateExit -ne 0) {
        Add-Result $Name "FAIL"
        Stop-Certification "$Name failed with exit code $GateExit."
    }

    Add-Result $Name "PASS"

    Write-Host ""
    Write-Host "PASS:" $Name
}


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16D Final Certification"
Write-Host "================================================="
Write-Host ""


# =========================================================
# PYTHON
# =========================================================

if (-not (Test-Path $Python)) {
    Stop-Certification "Python virtual environment missing: $Python"
}


# =========================================================
# RUNTIME ENV
# =========================================================

$RuntimeEnv = Join-Path $ScriptsRoot "phase16d_runtime_env.ps1"

if (-not (Test-Path $RuntimeEnv)) {
    Stop-Certification "Runtime environment file missing."
}

. $RuntimeEnv


$RequiredEnvironment = @(
    "WF_API_BASE",
    "WF_WS_BASE",
    "WF_CHANNEL_WS_PATH",
    "WF_WORKSPACE_ID",
    "WF_CHANNEL_ID",
    "WF_TOKEN_A",
    "WF_TOKEN_B"
)


foreach ($Name in $RequiredEnvironment) {
    $Value = [Environment]::GetEnvironmentVariable($Name)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        Add-Result "Runtime environment" "FAIL"
        Stop-Certification "Missing environment value: $Name"
    }
}


Add-Result "Runtime environment" "PASS"
Write-Host "PASS: Runtime environment"


# =========================================================
# BACKEND
# =========================================================

$Connection = Test-NetConnection `
    127.0.0.1 `
    -Port 8001 `
    -WarningAction SilentlyContinue


if (-not $Connection.TcpTestSucceeded) {
    Add-Result "Backend reachable" "FAIL"
    Stop-Certification "Backend is not listening on 127.0.0.1:8001."
}


Add-Result "Backend reachable" "PASS"
Write-Host "PASS: Backend reachable"


# =========================================================
# PHASE 16D PREFLIGHT
# =========================================================

$Preflight = Join-Path $ScriptsRoot "phase16d_preflight.ps1"

Invoke-PowerShellGate `
    "Phase 16D preflight" `
    $Preflight


# =========================================================
# PHASE 16D PYTHON GATES
# =========================================================

Invoke-PythonGate `
    "Two-client message fanout" `
    "phase16d_two_client_message_fanout.py"


Invoke-PythonGate `
    "Attachment event fanout" `
    "phase16d_attachment_event_fanout.py"


Invoke-PythonGate `
    "Reconnect and replay" `
    "phase16d_replay_gate.py"


Invoke-PythonGate `
    "Strict realtime sequence" `
    "phase16d_sequence_gate.py"


Invoke-PythonGate `
    "Unauthorized WebSocket rejection" `
    "phase16d_unauthorized_websocket_gate.py"


Invoke-PythonGate `
    "Read/unread contract" `
    "phase16d_read_unread_contract_gate.py"


# =========================================================
# PHASE 16C BACKEND REGRESSION
# =========================================================

$BackendRegression = Join-Path `
    $ScriptsRoot `
    "phase16c_attachment_backend_wiring_gate.ps1"


Invoke-PowerShellGate `
    "Phase 16C backend regression" `
    $BackendRegression


# =========================================================
# PHASE 16C FRONTEND REGRESSION DISCOVERY
# =========================================================

$FrontendRegression = $null

$Candidates = Get-ChildItem `
    -Path $ScriptsRoot `
    -Filter "phase16c*.ps1" `
    -File `
    -ErrorAction SilentlyContinue


foreach ($Candidate in $Candidates) {
    $Text = Get-Content `
        $Candidate.FullName `
        -Raw `
        -ErrorAction SilentlyContinue

    if ($Text -match "Remote attachment refresh certified") {
        $FrontendRegression = $Candidate.FullName
        break
    }
}


if ([string]::IsNullOrWhiteSpace($FrontendRegression)) {
    Add-Result "Phase 16C frontend regression" "FAIL"

    Stop-Certification `
        "Could not locate the certified Phase 16C frontend integration gate."
}


Write-Host ""
Write-Host "Detected frontend regression gate:"
Write-Host $FrontendRegression


Invoke-PowerShellGate `
    "Phase 16C frontend regression" `
    $FrontendRegression


# =========================================================
# FINAL RESULT CHECK
# =========================================================

$ExpectedGates = @(
    "Runtime environment",
    "Backend reachable",
    "Phase 16D preflight",
    "Two-client message fanout",
    "Attachment event fanout",
    "Reconnect and replay",
    "Strict realtime sequence",
    "Unauthorized WebSocket rejection",
    "Read/unread contract",
    "Phase 16C backend regression",
    "Phase 16C frontend regression"
)


foreach ($Expected in $ExpectedGates) {
    $Found = @(
        $Results |
            Where-Object {
                $_.Gate -eq $Expected
            }
    )

    if ($Found.Count -ne 1) {
        Stop-Certification "Missing or duplicate result: $Expected"
    }

    if ($Found[0].Status -ne "PASS") {
        Stop-Certification "Gate did not pass: $Expected"
    }
}


Show-Summary


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16D FINAL CERTIFICATION PASS"
Write-Host "================================================="
Write-Host ""

exit 0
