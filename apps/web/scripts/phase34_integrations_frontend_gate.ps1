$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\apps\web"

Write-Host ""
Write-Host "============================================================"
Write-Host " WorkforceOS Phase 34 - Integrations Frontend Gate"
Write-Host "============================================================"
Write-Host ""

$requiredFiles = @(
    ".\types\api-keys.ts",
    ".\services\api-keys.service.ts",
    ".\components\integrations\api-key-create-dialog.tsx",
    ".\components\integrations\api-key-secret-dialog.tsx",
    ".\components\integrations\api-key-row.tsx",
    ".\components\integrations\api-key-list.tsx",
    ".\components\integrations\integration-card.tsx",
    ".\app\(workspace)\integrations\page.tsx",
    ".\app\(workspace)\settings\integrations\page.tsx",
    ".\scripts\phase34_integrations_frontend_gate.ps1"
)

Write-Host "[1/5] Required files..."

foreach ($file in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Missing required file: $file"
    }

    Write-Host "PASS $file"
}

Write-Host ""
Write-Host "[2/5] API contract verification..."

$serviceFile = ".\services\api-keys.service.ts"
$serviceContent = Get-Content -LiteralPath $serviceFile -Raw

$requiredContractStrings = @(
    "/api-keys",
    "/api-keys/${workspaceId}/api-keys",
    "apiKeysService",
    "create",
    "revoke",
    "rotate"
)

if ($serviceContent -notmatch "/workspaces/\$\{workspaceId\}/api-keys") {
    throw "API key workspace route not found in frontend service."
}

if ($serviceContent -notmatch "/revoke") {
    throw "API key revoke route not found in frontend service."
}

if ($serviceContent -notmatch "/rotate") {
    throw "API key rotate route not found in frontend service."
}

Write-Host "PASS API key route contract references"

Write-Host ""
Write-Host "[3/5] Security checks..."

$secretFile = ".\components\integrations\api-key-secret-dialog.tsx"
$secretContent = Get-Content -LiteralPath $secretFile -Raw

if ($secretContent -match "localStorage") {
    throw "SECURITY FAILURE: API secret must not use localStorage."
}

if ($secretContent -match "sessionStorage") {
    throw "SECURITY FAILURE: API secret must not use sessionStorage."
}

if ($secretContent -match "document\.cookie") {
    throw "SECURITY FAILURE: API secret must not be written to cookies."
}

if ($secretContent -match "NEXT_PUBLIC_.*SECRET") {
    throw "SECURITY FAILURE: API secret must not use NEXT_PUBLIC environment variables."
}

Write-Host "PASS API secret storage guard"

Write-Host ""
Write-Host "[4/5] Backend contract alignment..."

$allFiles = @(
    ".\types\api-keys.ts",
    ".\services\api-keys.service.ts",
    ".\components\integrations\api-key-create-dialog.tsx",
    ".\components\integrations\api-key-secret-dialog.tsx",
    ".\components\integrations\api-key-row.tsx",
    ".\components\integrations\api-key-list.tsx",
    ".\components\integrations\integration-card.tsx",
    ".\app\(workspace)\integrations\page.tsx",
    ".\app\(workspace)\settings\integrations\page.tsx"
)

$combined = ""

foreach ($file in $allFiles) {
    $combined += "`n" + (Get-Content -LiteralPath $file -Raw)
}

if ($combined -match "ip_restriction") {
    throw "Frontend contains unsupported IP restriction contract."
}

if ($combined -match "ipRestriction") {
    throw "Frontend contains unsupported IP restriction contract."
}

if ($combined -match "editScopes") {
    throw "Frontend contains unsupported Edit Scopes action."
}

Write-Host "PASS no unsupported IP restriction/Edit Scopes contract"

Write-Host ""
Write-Host "[5/5] TypeScript production build..."

if (-not (Test-Path -LiteralPath ".\package.json")) {
    throw "package.json not found."
}

npm run build

if ($LASTEXITCODE -ne 0) {
    throw "Next.js production build failed."
}

Write-Host ""
Write-Host "============================================================"
Write-Host " PHASE 34 FRONTEND GATE COMPLETE"
Write-Host "============================================================"
Write-Host ""
Write-Host "PASS required files"
Write-Host "PASS API key routes"
Write-Host "PASS secret handling"
Write-Host "PASS backend contract alignment"
Write-Host "PASS production build"
Write-Host ""