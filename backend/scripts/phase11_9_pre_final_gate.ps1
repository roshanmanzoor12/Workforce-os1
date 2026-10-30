param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.9 Pre-Final Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Goals + Notes foundation..."

.\scripts\phase11_9_goals_notes_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Goals/Notes gate failed."
}

Write-Host ""

Write-Host "[2/5] Regression..."

.\scripts\phase11_9_regression_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Regression gate failed."
}

Write-Host ""

Write-Host "[3/5] Tenant migrations..."

.\scripts\phase11_9_tenant_migration_gate.ps1 `
    -DatabaseName $DatabaseName

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant migration gate failed."
}

Write-Host ""

Write-Host "[4/5] Final tenant revision..."

$Current = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read final tenant revision."
}

Write-Host $Current

if (
    $Current -notmatch
    "f6a7b8c9d0e1"
)
{
    throw "Tenant is not at Phase 11.9 schema head."
}

Write-Host "PASS tenant revision"
Write-Host ""

Write-Host "[5/5] Security contract..."

$SecurityCheck = @'
from pathlib import Path

roots = [
    Path("app/modules/goals"),
    Path("app/modules/notes"),
    Path("app/modules/knowledge"),
]

forbidden = [
    "request.state.authorized_tenant_session",
    "postgresql://",
    "database_password",
    "tenant_password",
    "capture_keystrokes",
    "capture_clipboard",
    "capture_password",
]

for root in roots:
    for path in root.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        for token in forbidden:
            if token.lower() in text:
                raise SystemExit(
                    f"Forbidden token "
                    f"{token!r} in {path}"
                )

print("PASS Phase 11.9 security contract")
'@

$SecurityCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Security contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.9 PRODUCTIVITY FOUNDATION: PASS"
Write-Host " Goals / Notes / Knowledge"
Write-Host "================================================="
Write-Host ""
Write-Host "AI productivity layer remains pending."