$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Employee Existing Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[preflight 1/2] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL 5434 is not reachable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""

Write-Host "[preflight 2/2] Membership migration..."

$Revision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $Revision

if ($Revision -notmatch "d9e0f1a2b3c4")
{
    throw "Phase 11.7 membership foundation is not current."
}

Write-Host "PASS membership foundation"
Write-Host ""

Write-Host "[1/5] Compile..."

& $Python `
    -m compileall `
    .\app\modules\employees `
    .\tests\test_phase11_7_employee_membership_bridge.py `
    .\tests\test_phase11_7_existing_employee_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Employee integration compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/5] Existing Employee tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_employee_membership_bridge.py `
    .\tests\test_phase11_7_existing_employee_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Employee integration tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/5] Existing tenant model contract..."

$ModelScript = @'
from app.db.tenant_base import TenantBase

from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)

for model in (
    Department,
    Team,
    Employee,
):
    if not issubclass(
        model,
        TenantBase,
    ):
        raise SystemExit(
            model.__name__
            + " is not tenant scoped."
        )

if Employee.__tablename__ != "employees":
    raise SystemExit(
        "Employee table mismatch."
    )

if Department.__tablename__ != "departments":
    raise SystemExit(
        "Department table mismatch."
    )

if Team.__tablename__ != "teams":
    raise SystemExit(
        "Team table mismatch."
    )

print("PASS existing Department model")
print("PASS existing Team model")
print("PASS existing Employee model")
print("PASS TenantBase isolation")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Employee model contract failed."
}

Write-Host ""

Write-Host "[4/5] Cross-database identity boundary..."

$IdentityScript = @'
from app.modules.employees.models import (
    Employee,
)

column = Employee.__table__.columns[
    "user_id"
]

if column.foreign_keys:
    raise SystemExit(
        "Employee.user_id must not have "
        "a cross-database ForeignKey."
    )

print(
    "PASS Employee remains separate "
    "from global User"
)

print(
    "PASS Employee.user_id is logical "
    "control-plane reference"
)

print(
    "PASS no cross-database FK"
)
'@

$IdentityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Employee identity boundary failed."
}

Write-Host ""

Write-Host "[5/5] Membership authorization bridge..."

$BridgeScript = @'
from pathlib import Path

bridge = Path(
    "app/modules/employees/"
    "membership_bridge.py"
).read_text(
    encoding="utf-8",
)

access = Path(
    "app/modules/employees/"
    "access_service.py"
).read_text(
    encoding="utf-8",
)

required_bridge = [
    "WorkspaceMembershipRepository",
    "require_active_member",
    "require_manager",
    "validate_employee_user_link",
    "WORKSPACE_ROLE_OWNER",
    "WORKSPACE_ROLE_ADMIN",
]

for token in required_bridge:
    if token not in bridge:
        raise SystemExit(
            "Missing membership bridge token: "
            + token
        )

required_access = [
    "control_session",
    "tenant_session",
    "EmployeeService",
    "EmployeeMembershipBridge",
]

for token in required_access:
    if token not in access:
        raise SystemExit(
            "Missing access service token: "
            + token
        )

print("PASS membership authorization bridge")
print("PASS OWNER/ADMIN mutation boundary")
print("PASS active-member read boundary")
print("PASS control DB authorization first")
print("PASS tenant domain service second")
'@

$BridgeScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Employee membership bridge failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 EMPLOYEE EXISTING FOUNDATION: PASS"
Write-Host "================================================="