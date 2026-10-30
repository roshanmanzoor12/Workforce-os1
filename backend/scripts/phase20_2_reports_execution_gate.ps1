$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 20.2 Reports Execution Gate"
Write-Host "================================================"


Write-Host ""
Write-Host "[1/8] Compile Reports execution..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\reports" `
    ".\tests\modules\reports_phase20" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20.2 compile failed."
}

Write-Host "PASS compile"


Write-Host ""
Write-Host "[2/8] Import execution stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.reports.execution import ReportExecutionService; from app.modules.reports.exporter import report_to_csv; from app.modules.reports.schemas import ReportRunRequest, ReportRunResponse; print('PASS Phase 20.2 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20.2 import failed."
}


Write-Host ""
Write-Host "[3/8] Schema contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_2_schema_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20.2 schema contract failed."
}


Write-Host ""
Write-Host "[4/8] CSV exporter..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_2_exporter.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20.2 exporter contract failed."
}


Write-Host ""
Write-Host "[5/8] Execution routes..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_2_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20.2 route contract failed."
}


Write-Host ""
Write-Host "[6/8] Full Phase 20 contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 contract regression failed."
}


Write-Host ""
Write-Host "[7/8] Analytics/Productivity regression..."

$Targets = @(
    ".\tests\modules\analytics_phase19",
    ".\tests\modules\productivity"
)

foreach ($Target in $Targets) {
    if (Test-Path $Target) {
        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "[8/8] Payroll/Monitoring regression..."

$Targets = @(
    ".\tests\modules\payroll",
    ".\tests\modules\monitoring",
    ".\tests\modules\devices",
    ".\tests\modules\audit_log"
)

foreach ($Target in $Targets) {
    if (Test-Path $Target) {
        Write-Host ""
        Write-Host "Running:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 20.2 Reports Execution Gate PASS"
Write-Host "================================================"