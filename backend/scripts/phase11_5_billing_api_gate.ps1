$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11.5 Billing API Gate"
Write-Host "==============================================="
Write-Host ""

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/5] Compiling billing API..."

& $Python `
    -m py_compile `
    .\app\modules\billing\models.py `
    .\app\modules\billing\workspace_count.py `
    .\app\modules\billing\api_schemas.py `
    .\app\modules\billing\api_service.py `
    .\app\modules\billing\router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Billing API compile failed."
}

Write-Host "PASS billing API compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/5] Running billing tests..."

& $Python `
    -m pytest `
    .\tests\modules\billing `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Billing tests failed."
}

Write-Host "PASS billing tests"
Write-Host ""


# =========================================================
# 3. CONTROL MIGRATION
# =========================================================

Write-Host "[3/5] Checking control migration..."

& $Python `
    -m alembic `
    -c .\alembic-control.ini `
    current

if ($LASTEXITCODE -ne 0)
{
    throw "Control migration check failed."
}

Write-Host "PASS control migration command"
Write-Host ""


# =========================================================
# 4. FASTAPI ROUTE WIRING
# =========================================================
#
# IMPORTANT:
#
# Current FastAPI uses _IncludedRouter wrappers for
# include_router(). Therefore app.routes does not necessarily
# contain flattened APIRoute objects.
#
# OpenAPI is the correct public API contract verification.
# =========================================================

Write-Host "[4/5] Checking FastAPI billing contract..."

@'
from app.main import app

schema = app.openapi()

expected = {
    "/api/v1/billing/plans": "get",
    "/api/v1/billing/subscription": "get",
    "/api/v1/billing/entitlements": "get",
}

paths = schema.get(
    "paths",
    {},
)

for path, method in expected.items():
    if path not in paths:
        print(
            "MISSING PATH:",
            path,
        )

        raise RuntimeError(
            f"Billing API path missing: {path}"
        )

    if method not in paths[path]:
        print(
            "MISSING METHOD:",
            method.upper(),
            path,
        )

        raise RuntimeError(
            f"Billing API method missing: "
            f"{method.upper()} {path}"
        )

    print(
        "PASS route:",
        method.upper(),
        path,
    )

print(
    "PASS FastAPI billing contract"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Billing FastAPI contract check failed."
}

Write-Host "PASS FastAPI billing wiring"
Write-Host ""


# =========================================================
# 5. PRIVACY
# =========================================================

Write-Host "[5/5] Checking public schema privacy..."

@'
from app.main import app

schema = app.openapi()

billing_paths = {
    key: value
    for key, value
    in schema.get(
        "paths",
        {},
    ).items()
    if "/billing/" in key
}

if not billing_paths:
    raise RuntimeError(
        "Billing OpenAPI paths unavailable."
    )

billing_text = str(
    billing_paths
).lower()

forbidden = (
    "card_number",
    "cardnumber",
    "cvv",
    "cvc",
    "security_code",
    "provider_customer_id",
    "provider_subscription_id",
)

for word in forbidden:
    if word in billing_text:
        raise RuntimeError(
            "Sensitive billing field exposed: "
            + word
        )

print(
    "PASS billing API exposes no "
    "raw/provider payment identifiers"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Billing API privacy check failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11.5 BILLING API GATE: PASS"
Write-Host "==============================================="
Write-Host ""