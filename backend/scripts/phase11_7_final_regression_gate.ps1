$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Regression Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Compile Phase 11.7 modules..."

& $Python `
    -m compileall `
    .\app\modules\memberships `
    .\app\modules\employees `
    .\app\modules\attendance `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.7 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/5] Membership tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_workspace_memberships.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Membership regression failed."
}

Write-Host "PASS membership regression"
Write-Host ""

Write-Host "[3/5] Employee tests..."

$EmployeeTests = @(
    ".\tests\test_phase11_7_employee_membership_bridge.py",
    ".\tests\test_phase11_7_existing_employee_contract.py"
)

$ExistingEmployeeTests = @()

foreach ($Test in $EmployeeTests)
{
    if (Test-Path $Test)
    {
        $ExistingEmployeeTests += $Test
    }
}

if ($ExistingEmployeeTests.Count -gt 0)
{
    & $Python `
        -m pytest `
        $ExistingEmployeeTests `
        -q

    if ($LASTEXITCODE -ne 0)
    {
        throw "Employee regression failed."
    }
}

Write-Host "PASS employee regression"
Write-Host ""

Write-Host "[4/5] Attendance tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_attendance_models.py `
    .\tests\test_phase11_7_attendance_architecture.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance regression failed."
}

Write-Host "PASS attendance regression"
Write-Host ""

Write-Host "[5/5] Tenant REST tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_employee_rest_routes.py `
    .\tests\test_phase11_7_attendance_rest_routes.py `
    .\tests\test_phase11_7_tenant_rest_security.py `
    .\tests\test_phase11_7_tenant_rest_domain_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant REST regression failed."
}

Write-Host "PASS tenant REST regression"

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 REGRESSION: PASS"
Write-Host "================================================="