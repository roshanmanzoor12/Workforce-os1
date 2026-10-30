$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 20 Reports Audit Gate"
Write-Host "================================================"


Write-Host ""
Write-Host "[1/8] Compile Phase 20 audit pack..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\tests\modules\reports_phase20" `
    ".\scripts\phase20_reports_inventory.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 compile failed."
}

Write-Host "PASS compile"


Write-Host ""
Write-Host "[2/8] Report permission contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_permissions.py" `
    ".\tests\modules\reports_phase20\test_phase20_client_boundary.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 permission contract failed."
}


Write-Host ""
Write-Host "[3/8] Report source modules..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_domain_modules.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 source module contract failed."
}


Write-Host ""
Write-Host "[4/8] Report source routes..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_source_routes.py" `
    ".\tests\modules\reports_phase20\test_phase20_catalog.py" `
    ".\tests\modules\reports_phase20\test_phase20_server_authority.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 source route contract failed."
}


Write-Host ""
Write-Host "[5/8] Dedicated report API inventory..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\reports_phase20\test_phase20_report_api_inventory.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 report API inventory failed."
}


Write-Host ""
Write-Host "[6/8] Generate exact reports inventory..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase20_reports_inventory.py" `
    2>&1 |
    Tee-Object `
        ".\phase20_reports_inventory.txt"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 20 inventory generation failed."
}

Write-Host "PASS inventory generated"


Write-Host ""
Write-Host "[7/8] Analytics/payroll regressions..."

$PrimaryTargets = @(
    ".\tests\modules\analytics_phase19",
    ".\tests\modules\productivity",
    ".\tests\modules\payroll"
)

foreach ($Target in $PrimaryTargets) {
    if (Test-Path $Target) {
        Write-Host ""
        Write-Host "Running:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Phase 20 regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "[8/8] Report-source regressions..."

$SourceTargets = @(
    ".\tests\modules\monitoring",
    ".\tests\modules\devices",
    ".\tests\modules\goals",
    ".\tests\modules\audit_log"
)

foreach ($Target in $SourceTargets) {
    if (Test-Path $Target) {
        Write-Host ""
        Write-Host "Running:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Phase 20 source regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 20 Reports Audit Gate PASS"
Write-Host "================================================"

Write-Host ""
Write-Host "IMPORTANT:"
Write-Host "PASS means source/backend readiness passed."
Write-Host "Review phase20_reports_inventory.txt before"
Write-Host "declaring Phase 20 final certification."