$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$MainFile = Join-Path `
    $BackendRoot `
    "app\main.py"

if (-not (Test-Path $MainFile))
{
    throw (
        "main.py not found: " +
        $MainFile
    )
}

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Attachment Binding Wiring"
Write-Host "================================================="
Write-Host ""

$Text = Get-Content `
    $MainFile `
    -Raw

$ImportLine = (
    "from app.modules.attachments.message_router " +
    "import router as attachment_message_router"
)

$IncludeLine = (
    "app.include_router(" +
    "attachment_message_router, " +
    "prefix=`"/api/v1`")"
)

if ($Text.Contains($ImportLine))
{
    Write-Host (
        "PASS attachment message router " +
        "import already present"
    )
}
else
{
    $ImportAnchor = (
        "from app.modules.attachments.router " +
        "import router as attachments_router"
    )

    if ($Text.Contains($ImportAnchor))
    {
        $Text = $Text.Replace(
            $ImportAnchor,
            (
                $ImportAnchor +
                "`r`n" +
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

    Write-Host (
        "PASS added attachment message " +
        "router import"
    )
}

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

if ($Text.Contains($IncludeLine))
{
    Write-Host (
        "PASS attachment message router " +
        "include already present"
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

    Write-Host (
        "PASS added attachment message " +
        "router include"
    )
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
Write-Host (
    "PASS attachment binding wiring complete"
)