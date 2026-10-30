$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$MainFile = Join-Path $BackendRoot "app\main.py"

if (-not (Test-Path $MainFile))
{
    throw "main.py not found."
}

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Tenant REST Wiring"
Write-Host "================================================="
Write-Host ""

$Text = Get-Content $MainFile -Raw

$FutureLine = "from __future__ import annotations"

$ImportLine = "from app.modules.tenant_api.router import router as tenant_api_router"

$IncludeLine = 'app.include_router(tenant_api_router, prefix="/api/v1")'

if (-not $Text.Contains($ImportLine))
{
    if ($Text.Contains($FutureLine))
    {
        $Text = $Text.Replace(
            $FutureLine,
            $FutureLine + "`r`n`r`n" + $ImportLine
        )
    }
    else
    {
        $Text = $ImportLine + "`r`n" + $Text
    }

    Write-Host "PASS tenant API import added"
}
else
{
    Write-Host "PASS tenant API import already present"
}

if (-not $Text.Contains($IncludeLine))
{
    $Text = $Text.TrimEnd() + "`r`n`r`n" + $IncludeLine + "`r`n"

    Write-Host "PASS tenant API include added"
}
else
{
    Write-Host "PASS tenant API include already present"
}

Set-Content `
    -Path $MainFile `
    -Value $Text `
    -Encoding UTF8

Write-Host ""
Write-Host "PASS Phase 11.7 Tenant REST wiring"