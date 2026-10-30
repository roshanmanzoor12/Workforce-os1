$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"

$MainPath = Join-Path `
    $Backend `
    "app\main.py"

if (-not (Test-Path $MainPath))
{
    throw "app\main.py not found."
}

$Text = Get-Content `
    $MainPath `
    -Raw

$ImportText = @'
from app.modules.billing.router import (
    router as billing_router,
)

'@

if (
    $Text -notmatch
    "app\.modules\.billing\.router"
)
{
    $Anchor = (
        "from app.modules.auth.router import " +
        "router as auth_router"
    )

    if (
        $Text -notmatch
        [regex]::Escape($Anchor)
    )
    {
        throw (
            "Unable to locate auth router " +
            "import anchor in app\main.py."
        )
    }

    $Text = $Text.Replace(
        $Anchor,
        $Anchor +
        [Environment]::NewLine +
        $ImportText.TrimEnd()
    )

    Write-Host "Added billing router import"
}
else
{
    Write-Host "Billing router import already present"
}

if (
    $Text -notmatch
    "include_router\(\s*billing_router"
)
{
    $RootMarker = (
        "# =========================================================" +
        [Environment]::NewLine +
        "# ROOT"
    )

    if (
        $Text -notmatch
        [regex]::Escape($RootMarker)
    )
    {
        throw (
            "Unable to locate ROOT marker " +
            "in app\main.py."
        )
    }

    $IncludeText = @'
app.include_router(
    billing_router,
    prefix=settings.api_v1_prefix,
)


'@

    $Text = $Text.Replace(
        $RootMarker,
        $IncludeText +
        $RootMarker
    )

    Write-Host "Added billing router registration"
}
else
{
    Write-Host "Billing router registration already present"
}

Set-Content `
    -Path $MainPath `
    -Value $Text `
    -Encoding UTF8

Write-Host ""
Write-Host "PASS Phase 11.5 billing router wiring"