$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$MainFile = Join-Path $BackendRoot "app\main.py"

if (-not (Test-Path $MainFile)) {
    throw "main.py not found: $MainFile"
}

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Attachment API Wiring"
Write-Host "================================================="
Write-Host ""

$Text = Get-Content $MainFile -Raw

$ImportLine = "from app.modules.attachments.router import router as attachments_router"
$IncludeLine = "app.include_router(attachments_router, prefix=`"/api/v1`")"

if ($Text.Contains($ImportLine)) {
    Write-Host "PASS attachment router import already present"
}
else {
    $ImportAnchor = "from fastapi import"

    $Index = $Text.IndexOf($ImportAnchor)

    if ($Index -lt 0) {
        throw "Could not locate FastAPI import anchor in main.py"
    }

    $LineEnd = $Text.IndexOf(
        "`n",
        $Index
    )

    if ($LineEnd -lt 0) {
        throw "Could not locate FastAPI import line ending"
    }

    $Before = $Text.Substring(
        0,
        $LineEnd + 1
    )

    $After = $Text.Substring(
        $LineEnd + 1
    )

    $Text = (
        $Before +
        $ImportLine +
        "`r`n" +
        $After
    )

    Write-Host "PASS added attachment router import"
}

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

if ($Text.Contains($IncludeLine)) {
    Write-Host "PASS attachment router include already present"
}
else {
    $Text = (
        $Text.TrimEnd() +
        "`r`n`r`n" +
        $IncludeLine +
        "`r`n"
    )

    Write-Host "PASS added attachment router include"
}

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)

Set-Content `
    -Path $MainFile `
    -Value $Text `
    -Encoding UTF8

Write-Host ""
Write-Host "PASS main.py attachment wiring complete"