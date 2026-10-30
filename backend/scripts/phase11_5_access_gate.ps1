$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11.5 Access Gate"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/6] Compile Phase 11.5 access files..."

& $Python `
    -m py_compile `
    .\app\main.py `
    .\app\modules\billing\workspace_access.py `
    .\app\modules\billing\subscription_bootstrap.py `
    .\app\modules\billing\workspace_decision.py `
    .\app\modules\billing\access_schemas.py `
    .\app\modules\billing\api_service.py `
    .\app\modules\billing\router.py `
    .\scripts\phase11_5_verify_billing_schema.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 access compile failed."
}

Write-Host "PASS access compile"
Write-Host ""

Write-Host "[2/6] Billing tests..."

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

Write-Host "[3/6] Billing control schema..."

& $Python `
    .\scripts\phase11_5_verify_billing_schema.py

if ($LASTEXITCODE -ne 0)
{
    throw "Billing schema verification failed."
}

Write-Host "PASS billing schema"
Write-Host ""

Write-Host "[4/6] FastAPI billing routes..."

@'
from app.main import app

expected = {
    ("GET", "/api/v1/billing/plans"),
    ("GET", "/api/v1/billing/subscription"),
    ("GET", "/api/v1/billing/entitlements"),
    ("GET", "/api/v1/billing/workspace-access"),
}

actual = set()

for route in app.routes:
    path = getattr(
        route,
        "path",
        None,
    )

    methods = getattr(
        route,
        "methods",
        None,
    )

    if path is None or methods is None:
        continue

    for method in methods:
        actual.add(
            (
                method,
                path,
            )
        )

missing = (
    expected
    - actual
)

if missing:
    for item in sorted(
        missing
    ):
        print(
            "MISSING:",
            item,
        )

    raise RuntimeError(
        "Billing routes missing."
    )

for method, path in sorted(
    expected
):
    print(
        "PASS route:",
        method,
        path,
    )
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Billing route verification failed."
}

Write-Host ""

Write-Host "[5/6] Billing OpenAPI privacy..."

@'
from app.main import app

schema = app.openapi()

billing_paths = {
    path: value
    for path, value
    in schema["paths"].items()
    if "/billing/" in path
}

text = str(
    billing_paths
).lower()

forbidden = (
    "card_number",
    "cardnumber",
    "cvv",
    "cvc",
    "provider_customer_id",
    "provider_subscription_id",
)

for word in forbidden:
    if word in text:
        raise RuntimeError(
            f"Sensitive field exposed: {word}"
        )

print(
    "PASS billing OpenAPI privacy"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Billing OpenAPI privacy failed."
}

Write-Host ""

Write-Host "[6/6] Workspace entitlement architecture..."

@'
from app.modules.billing.workspace_access import (
    WorkspaceEntitlementAccess,
)

from app.modules.billing.workspace_guard import (
    WorkspaceCreationGuard,
)

from app.modules.billing.workspace_count import (
    count_owned_active_workspaces,
)

assert WorkspaceEntitlementAccess is not None
assert WorkspaceCreationGuard is not None
assert callable(
    count_owned_active_workspaces
)

print(
    "PASS workspace entitlement architecture"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace entitlement architecture failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11.5 ACCESS GATE: PASS"
Write-Host "==============================================="
Write-Host ""