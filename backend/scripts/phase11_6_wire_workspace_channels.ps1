$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"
$MainPath = Join-Path $Backend "app\main.py"

Set-Location $Backend

if (-not (Test-Path $MainPath))
{
    throw "app\main.py not found."
}

$Text = Get-Content $MainPath -Raw


# =========================================================
# NORMALIZE OLD JOIN DAMAGE
# =========================================================

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)


# =========================================================
# IMPORT
# =========================================================

if (
    $Text -notmatch
    "from app\.modules\.channels\.router import"
)
{
    $Pattern = (
        "(?ms)" +
        "from app\.modules\.chat\.realtime_commands_router import \(" +
        "\s*router as chat_realtime_commands_router," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $Pattern
    )

    if (-not $Match.Success)
    {
        throw (
            "Realtime commands router import " +
            "anchor not found."
        )
    }

    $Block = @'

from app.modules.channels.router import (
    router as workspace_channels_router,
)
'@

    $Replacement = (
        $Match.Value +
        "`r`n" +
        $Block +
        "`r`n"
    )

    $Text = (
        $Text.Substring(
            0,
            $Match.Index
        ) +
        $Replacement +
        $Text.Substring(
            $Match.Index +
            $Match.Length
        )
    )

    Write-Host "PASS workspace channels import inserted"
}
else
{
    Write-Host "Workspace channels import already present"
}


# =========================================================
# INCLUDE
# =========================================================

if (
    $Text -notmatch
    "app\.include_router\(\s*workspace_channels_router"
)
{
    $Pattern = (
        "(?ms)" +
        "app\.include_router\(" +
        "\s*chat_realtime_commands_router," +
        "\s*prefix=settings\.api_v1_prefix," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $Pattern
    )

    if (-not $Match.Success)
    {
        throw (
            "Realtime commands include " +
            "anchor not found."
        )
    }

    $Block = @'

app.include_router(
    workspace_channels_router,
    prefix=settings.api_v1_prefix,
)
'@

    $Replacement = (
        $Match.Value +
        "`r`n" +
        $Block +
        "`r`n"
    )

    $Text = (
        $Text.Substring(
            0,
            $Match.Index
        ) +
        $Replacement +
        $Text.Substring(
            $Match.Index +
            $Match.Length
        )
    )

    Write-Host "PASS workspace channels router registered"
}
else
{
    Write-Host "Workspace channels router already registered"
}


# =========================================================
# FINAL NORMALIZATION
# =========================================================

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)


Set-Content `
    -Path $MainPath `
    -Value $Text `
    -Encoding UTF8


& $Python `
    -m py_compile `
    .\app\main.py `
    .\app\modules\channels\router.py

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel router compile failed."
}


$CheckScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/workspace-channels": "post",
    "/api/v1/workspace-channels/workspace/{workspace_id}": "get",
    "/api/v1/workspace-channels/{channel_id}": "patch",
    "/api/v1/workspace-channels/{channel_id}/messages": "post",
}

for path, method in expected.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing route: {path}"
        )

    if method not in paths[path]:
        raise RuntimeError(
            f"Missing {method.upper()} {path}"
        )

    print(
        "PASS:",
        method.upper(),
        path,
    )

print(
    "PASS workspace channel router wiring"
)
'@

$CheckScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace channel route contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 WORKSPACE CHANNEL WIRING: PASS"
Write-Host "================================================="
Write-Host ""