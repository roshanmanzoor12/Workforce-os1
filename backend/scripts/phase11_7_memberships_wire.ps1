$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$MainFile = Join-Path `
    $BackendRoot `
    "app\main.py"

if (-not (Test-Path $MainFile))
{
    throw "main.py not found."
}

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Membership Wiring"
Write-Host "================================================="
Write-Host ""

$Text = Get-Content `
    $MainFile `
    -Raw

$ImportLine = (
    "from app.modules.memberships.router " +
    "import router as memberships_router"
)

$IncludeLine = (
    "app.include_router(" +
    "memberships_router, " +
    "prefix=`"/api/v1`")"
)

if ($Text.Contains($ImportLine))
{
    Write-Host (
        "PASS membership router import already present"
    )
}
else
{
    $FutureLine = (
        "from __future__ import annotations"
    )

    if ($Text.Contains($FutureLine))
    {
        $Text = $Text.Replace(
            $FutureLine,
            (
                $FutureLine +
                "`r`n`r`n" +
                $ImportLine
            )
        )
    }
    else
    {
        $Text = (
            $ImportLine +
            "`r`n" +
            $Text
        )
    }

    Write-Host "PASS membership router import added"
}

if ($Text.Contains($IncludeLine))
{
    Write-Host (
        "PASS membership router include already present"
    )
}
else
{
    $Text = (
        $Text.TrimEnd() +
        "`r`n`r`n" +
        $IncludeLine +
        "`r`n"
    )

    Write-Host "PASS membership router include added"
}

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)

Set-Content `
    -Path $MainFile `
    -Value $Text `
    -Encoding UTF8

Write-Host ""
Write-Host "PASS Phase 11.7 membership wiring"