$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11.5 Billing Domain Gate"
Write-Host "==============================================="
Write-Host ""

$Python = "C:\workforce-os\.venv\Scripts\python.exe"
$Backend = "C:\workforce-os\backend"

Set-Location $Backend

Write-Host "[1/4] Compiling billing domain..."

& $Python `
    -m py_compile `
    .\app\modules\billing\plans.py `
    .\app\modules\billing\enums.py `
    .\app\modules\billing\models.py `
    .\app\modules\billing\schemas.py `
    .\app\modules\billing\entitlements.py `
    .\app\modules\billing\exceptions.py `
    .\app\modules\billing\service.py `
    .\app\modules\billing\repository.py `
    .\app\modules\billing\account_service.py `
    .\app\modules\billing\workspace_guard.py `
    .\app\modules\billing\subscription_service.py `
    .\app\modules\billing\catalog_service.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 billing compile failed."
}

Write-Host "PASS billing compile"
Write-Host ""

Write-Host "[2/4] Running billing tests..."

& $Python `
    -m pytest `
    .\tests\modules\billing `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 billing tests failed."
}

Write-Host "PASS billing tests"
Write-Host ""

Write-Host "[3/4] Checking migration source..."

$Migration = Join-Path `
    $Backend `
    "migrations\control\versions\d3e4f5a6b7c8_add_billing_foundation.py"

if (-not (Test-Path $Migration))
{
    throw "Billing migration file missing."
}

$MigrationText = Get-Content `
    $Migration `
    -Raw

if (
    $MigrationText -notmatch
    "billing_customers"
)
{
    throw "billing_customers migration definition missing."
}

if (
    $MigrationText -notmatch
    "billing_subscriptions"
)
{
    throw "billing_subscriptions migration definition missing."
}

Write-Host "PASS migration source"
Write-Host ""

Write-Host "[4/4] Checking security boundaries..."

$ModuleFiles = Get-ChildItem `
    .\app\modules\billing `
    -Filter "*.py" `
    -Recurse

$Forbidden = @(
    "card_number",
    "cardnumber",
    "cvv",
    "cvc",
    "security_code"
)

foreach (
    $Word in $Forbidden
)
{
    $Matches = $ModuleFiles |
        Select-String `
            -Pattern $Word `
            -SimpleMatch

    if ($Matches)
    {
        throw (
            "Forbidden payment data field found: " +
            $Word
        )
    }
}

Write-Host "PASS no raw payment-card fields"
Write-Host ""

Write-Host "==============================================="
Write-Host " PHASE 11.5 BILLING DOMAIN GATE: PASS"
Write-Host "==============================================="
Write-Host ""