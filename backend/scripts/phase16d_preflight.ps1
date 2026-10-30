$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16D Runtime Preflight"
Write-Host "================================================="
Write-Host ""


$BackendRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $BackendRoot


function Fail-Gate {
    param(
        [string]$Message
    )

    Write-Host ""
    Write-Host `
        "FAIL: $Message" `
        -ForegroundColor Red
    Write-Host ""

    exit 1
}


function Pass-Step {
    param(
        [string]$Message
    )

    Write-Host `
        "PASS: $Message" `
        -ForegroundColor Green
}


Write-Host "[1/7] Python environment..."


$Python =
    ".\.venv\Scripts\python.exe"


if (
    -not (
        Test-Path $Python
    )
)
{
    Fail-Gate `
        "Python virtual environment missing."
}


Pass-Step `
    "Python virtual environment"


Write-Host ""
Write-Host "[2/7] Runtime environment file..."


$RuntimeEnv =
    ".\scripts\phase16d_runtime_env.ps1"


if (
    -not (
        Test-Path $RuntimeEnv
    )
)
{
    Fail-Gate `
        "Create phase16d_runtime_env.ps1 from the example first."
}


. $RuntimeEnv


Pass-Step `
    "Runtime environment loaded"


Write-Host ""
Write-Host "[3/7] Required environment values..."


foreach (
    $Name in @(
        "WF_API_BASE",
        "WF_WS_BASE",
        "WF_TOKEN_A",
        "WF_TOKEN_B",
        "WF_WORKSPACE_ID",
        "WF_CHANNEL_ID"
    )
)
{
    $Value =
        [Environment]::GetEnvironmentVariable(
            $Name
        )


    if (
        [string]::IsNullOrWhiteSpace(
            $Value
        )
    )
    {
        Fail-Gate `
            "Missing environment value: $Name"
    }
}


Pass-Step `
    "Runtime values configured"


Write-Host ""
Write-Host "[4/7] PostgreSQL..."


$Postgres =
    Test-NetConnection `
        -ComputerName "127.0.0.1" `
        -Port 5434 `
        -WarningAction SilentlyContinue


if (
    -not $Postgres.TcpTestSucceeded
)
{
    Fail-Gate `
        "PostgreSQL 5434 unreachable."
}


Pass-Step `
    "PostgreSQL reachable"


Write-Host ""
Write-Host "[5/7] Redis..."


$Redis =
    Test-NetConnection `
        -ComputerName "127.0.0.1" `
        -Port 6381 `
        -WarningAction SilentlyContinue


if (
    -not $Redis.TcpTestSucceeded
)
{
    Fail-Gate `
        "Redis 6381 unreachable."
}


Pass-Step `
    "Redis reachable"


Write-Host ""
Write-Host "[6/7] Python dependencies..."


& $Python `
    -c `
    "import websockets; print('PASS websockets import')"


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "Python websockets package unavailable."
}


Pass-Step `
    "Runtime dependencies"


Write-Host ""
Write-Host "[7/7] Contract probe..."


& $Python `
    ".\scripts\phase16d_contract_probe.py"


if (
    $LASTEXITCODE -ne 0
)
{
    Fail-Gate `
        "Phase 16D contract probe failed."
}


Pass-Step `
    "Realtime contracts"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16D RUNTIME PREFLIGHT PASS"
Write-Host "================================================="
Write-Host ""