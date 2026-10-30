$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = Join-Path `
    $BackendRoot `
    ".venv\Scripts\python.exe"


Set-Location $BackendRoot


function Fail-Gate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 17 PRODUCTION READINESS: FAIL"
    Write-Host "================================================="
    Write-Host "ERROR:" $Message
    Write-Host "================================================="

    exit 1
}


function Invoke-Gate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    if (-not (Test-Path $Path))
    {
        Fail-Gate (
            "Missing gate: {0}" -f $Path
        )
    }

    Write-Host ""
    Write-Host "-------------------------------------------------"
    Write-Host $Name
    Write-Host "-------------------------------------------------"

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Path

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Gate (
            "{0} failed with exit code {1}." `
                -f $Name, $LASTEXITCODE
        )
    }

    Write-Host "PASS $Name"
}


Write-Host "================================================="
Write-Host " WorkforceOS Phase 17 Production Readiness"
Write-Host "================================================="
Write-Host ""


Write-Host "[1/6] Python compile..."


& $Python `
    -m compileall `
    ".\app\modules\channels" `
    ".\app\modules\attachments" `
    ".\tests\channels" `
    -q


if ($LASTEXITCODE -ne 0)
{
    Fail-Gate `
        "Production readiness compile failed."
}


Write-Host "PASS compile"


Write-Host ""
Write-Host "[2/6] Production configuration..."


& $Python `
    ".\scripts\phase17_production_config_gate.py"


if ($LASTEXITCODE -ne 0)
{
    Fail-Gate `
        "Production configuration failed."
}


Write-Host "PASS configuration"


Write-Host ""
Write-Host "[3/6] Batch 1 certification..."


Invoke-Gate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_hardening_foundation_gate.ps1"
    ) `
    -Name "Phase 17 Batch 1"


Write-Host ""
Write-Host "[4/6] Batch 2 certification..."


Invoke-Gate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_batch2_gate.ps1"
    ) `
    -Name "Phase 17 Batch 2"


Write-Host ""
Write-Host "[5/6] Runtime regression..."


Invoke-Gate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_runtime_regression_gate.ps1"
    ) `
    -Name "Phase 17 Runtime Regression"


Write-Host ""
Write-Host "[6/6] Security regression..."


Invoke-Gate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_security_regression_gate.ps1"
    ) `
    -Name "Phase 17 Security Regression"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 17 PRODUCTION READINESS: PASS"
Write-Host "================================================="
Write-Host "Compile:                          PASS"
Write-Host "Production configuration:         PASS"
Write-Host "Batch 1:                          PASS"
Write-Host "Batch 2:                          PASS"
Write-Host "Runtime regression:               PASS"
Write-Host "Security regression:              PASS"
Write-Host "================================================="

exit 0