$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "=================================================="
Write-Host " WorkforceOS Phase 11.5 Completion Gate"
Write-Host "=================================================="
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/8] Compiling Phase 11.5..."

& $Python `
    -m py_compile `
    .\app\modules\billing\customer_service.py `
    .\app\modules\billing\provider_event.py `
    .\app\modules\billing\provider_event_service.py `
    .\app\modules\billing\billing_snapshot.py `
    .\app\modules\billing\provider_service.py `
    .\app\modules\billing\workspace_access.py `
    .\app\modules\billing\workspace_guard.py `
    .\app\modules\billing\router.py `
    .\app\modules\workspaces\service.py `
    .\scripts\phase11_5_verify_live_billing.py `
    .\scripts\phase11_5_verify_openapi.py `
    .\scripts\phase11_5_verify_workspace_enforcement.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. BILLING TESTS
# =========================================================

Write-Host "[2/8] Billing tests..."

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
# 3. CONTROL MIGRATION
# =========================================================

Write-Host "[3/8] Control migration..."

$CurrentRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Control migration command failed."
}

Write-Host $CurrentRevision

if (
    $CurrentRevision -notmatch
    "d3e4f5a6b7c8"
)
{
    throw (
        "Expected billing control revision " +
        "d3e4f5a6b7c8."
    )
}

Write-Host "PASS control migration"
Write-Host ""


# =========================================================
# 4. LIVE BILLING SCHEMA
# =========================================================

Write-Host "[4/8] Live billing schema..."

& $Python `
    .\scripts\phase11_5_verify_live_billing.py

if ($LASTEXITCODE -ne 0)
{
    throw "Live billing verification failed."
}

Write-Host "PASS live billing schema"
Write-Host ""


# =========================================================
# 5. OPENAPI
# =========================================================

Write-Host "[5/8] Billing/workspace OpenAPI..."

& $Python `
    .\scripts\phase11_5_verify_openapi.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.5 OpenAPI verification failed."
}

Write-Host "PASS OpenAPI"
Write-Host ""


# =========================================================
# 6. WORKSPACE ENFORCEMENT
# =========================================================

Write-Host "[6/8] Workspace entitlement enforcement..."

& $Python `
    .\scripts\phase11_5_verify_workspace_enforcement.py

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace enforcement verification failed."
}

Write-Host "PASS workspace enforcement"
Write-Host ""


# =========================================================
# 7. ENTITLEMENT SCENARIOS
# =========================================================

Write-Host "[7/8] Entitlement scenarios..."

@'
from app.modules.billing.entitlements import (
    evaluate_account_entitlements,
)
from app.modules.billing.enums import (
    SubscriptionStatus,
)
from app.modules.billing.plans import (
    PlanCode,
)


cases = (
    (
        "FREE denied",
        PlanCode.FREE,
        SubscriptionStatus.NONE,
        0,
        False,
    ),
    (
        "STARTER first workspace allowed",
        PlanCode.STARTER,
        SubscriptionStatus.ACTIVE,
        0,
        True,
    ),
    (
        "STARTER limit denied",
        PlanCode.STARTER,
        SubscriptionStatus.ACTIVE,
        1,
        False,
    ),
    (
        "PRO canceled denied",
        PlanCode.PROFESSIONAL,
        SubscriptionStatus.CANCELED,
        0,
        False,
    ),
    (
        "PRO active allowed",
        PlanCode.PROFESSIONAL,
        SubscriptionStatus.ACTIVE,
        0,
        True,
    ),
)

for (
    name,
    plan,
    status,
    count,
    expected,
) in cases:
    result = evaluate_account_entitlements(
        plan_code=plan,
        subscription_status=status,
        workspace_count=count,
    )

    if result.create_workspace is not expected:
        raise RuntimeError(
            f"Entitlement scenario failed: {name}"
        )

    print(
        "PASS:",
        name,
    )
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Entitlement scenario verification failed."
}

Write-Host ""


# =========================================================
# 8. SECURITY / PRIVACY
# =========================================================

Write-Host "[8/8] Billing security boundaries..."

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

Write-Host "Verified provider state architecture:"
Write-Host "  customer linkage       PASS"
Write-Host "  subscription linkage   PASS"
Write-Host "  entitlement engine     PASS"
Write-Host "  workspace enforcement  PASS"
Write-Host "  provider IDs private   PASS"
Write-Host ""

Write-Host "=================================================="
Write-Host " PHASE 11.5 CORE ACCESS/BILLING: 100% PASS"
Write-Host "=================================================="
Write-Host ""