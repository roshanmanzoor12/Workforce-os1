$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.5 Workspace Enforcement"
Write-Host "================================================="
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/6] Compiling..."

& $Python `
    -m py_compile `
    .\app\modules\billing\workspace_creation_orchestrator.py `
    .\app\modules\billing\provider_state.py `
    .\app\modules\billing\provider_schemas.py `
    .\app\modules\billing\provider_service.py `
    .\app\modules\workspaces\service.py `
    .\scripts\phase11_5_verify_workspace_enforcement.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 enforcement compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. BILLING TESTS
# =========================================================

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


# =========================================================
# 3. WORKSPACE ENFORCEMENT
# =========================================================

Write-Host "[3/6] Workspace enforcement order..."

& $Python `
    .\scripts\phase11_5_verify_workspace_enforcement.py

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace entitlement enforcement failed."
}

Write-Host "PASS enforcement ordering"
Write-Host ""


# =========================================================
# 4. ENTITLEMENT SCENARIOS
# =========================================================

Write-Host "[4/6] Entitlement scenarios..."

@'
from app.modules.billing.entitlements import (
    evaluate_account_entitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import PlanCode


free = evaluate_account_entitlements(
    plan_code=PlanCode.FREE,
    subscription_status=SubscriptionStatus.NONE,
    workspace_count=0,
)

assert free.create_workspace is False

starter_first = evaluate_account_entitlements(
    plan_code=PlanCode.STARTER,
    subscription_status=SubscriptionStatus.ACTIVE,
    workspace_count=0,
)

assert starter_first.create_workspace is True

starter_second = evaluate_account_entitlements(
    plan_code=PlanCode.STARTER,
    subscription_status=SubscriptionStatus.ACTIVE,
    workspace_count=1,
)

assert starter_second.create_workspace is False

inactive = evaluate_account_entitlements(
    plan_code=PlanCode.PROFESSIONAL,
    subscription_status=SubscriptionStatus.CANCELED,
    workspace_count=0,
)

assert inactive.create_workspace is False

print("PASS FREE denied")
print("PASS STARTER first workspace allowed")
print("PASS STARTER second workspace denied")
print("PASS canceled paid subscription denied")
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Entitlement scenario check failed."
}

Write-Host ""


# =========================================================
# 5. OPENAPI
# =========================================================

Write-Host "[5/6] Billing/workspace OpenAPI..."

@'
from app.main import app

schema = app.openapi()

paths = schema.get(
    "paths",
    {},
)

required = (
    "/api/v1/billing/plans",
    "/api/v1/billing/subscription",
    "/api/v1/billing/entitlements",
    "/api/v1/billing/workspace-access",
    "/api/v1/workspaces",
)

for path in required:
    if path not in paths:
        raise RuntimeError(
            f"Missing OpenAPI path: {path}"
        )

if (
    "post"
    not in paths[
        "/api/v1/workspaces"
    ]
):
    raise RuntimeError(
        "POST /api/v1/workspaces missing."
    )

print(
    "PASS billing/workspace OpenAPI contract"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI contract failed."
}

Write-Host ""


# =========================================================
# 6. PAYMENT PRIVACY
# =========================================================

Write-Host "[6/6] Payment privacy..."

$BillingFiles = Get-ChildItem `
    .\app\modules\billing `
    -Recurse `
    -Filter "*.py"

$Forbidden = @(
    "card_number",
    "cardnumber",
    "cvv",
    "cvc",
    "security_code"
)

foreach ($Word in $Forbidden)
{
    $Matches = $BillingFiles |
        Select-String `
            -Pattern $Word `
            -SimpleMatch

    if ($Matches)
    {
        throw (
            "Forbidden raw payment field found: " +
            $Word
        )
    }
}

Write-Host "PASS no raw card data"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 11.5 WORKSPACE ENFORCEMENT: PASS"
Write-Host "================================================="
Write-Host ""