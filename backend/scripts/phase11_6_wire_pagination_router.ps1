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

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)


# =========================================================
# IMPORT PAGINATION ROUTER
# =========================================================

if (
    $Text -notmatch
    "from app\.modules\.chat\.pagination_router import"
)
{
    $Pattern = (
        "(?ms)" +
        "from app\.modules\.chat\.router import \(" +
        "\s*router as chat_router," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $Pattern
    )

    if (-not $Match.Success)
    {
        throw "chat_router import anchor not found."
    }

    $Block = @'

from app.modules.chat.pagination_router import (
    router as chat_pagination_router,
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

    Write-Host "PASS pagination router import inserted"
}
else
{
    Write-Host "Pagination router import already present"
}


# =========================================================
# INCLUDE PAGINATION ROUTER
# =========================================================

if (
    $Text -notmatch
    "app\.include_router\(\s*chat_pagination_router"
)
{
    $Pattern = (
        "(?ms)" +
        "app\.include_router\(" +
        "\s*chat_router," +
        "\s*prefix=settings\.api_v1_prefix," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $Pattern
    )

    if (-not $Match.Success)
    {
        throw "chat_router include anchor not found."
    }

    $Block = @'

app.include_router(
    chat_pagination_router,
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

    Write-Host "PASS pagination router registered"
}
else
{
    Write-Host "Pagination router already registered"
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
    -Path $MainPath `
    -Value $Text `
    -Encoding UTF8


& $Python `
    -m py_compile `
    .\app\modules\chat\pagination_router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Pagination router compile failed."
}


$CheckScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

path = (
    "/api/v1/chat/{conversation_id}/messages-page"
)

if path not in paths:
    raise RuntimeError(
        f"Missing pagination API: {path}"
    )

if "get" not in paths[path]:
    raise RuntimeError(
        "Missing GET pagination API."
    )

resume_path = (
    "/api/v1/chat/realtime/resume"
)

if resume_path not in paths:
    raise RuntimeError(
        f"Missing realtime resume API: {resume_path}"
    )

if "post" not in paths[resume_path]:
    raise RuntimeError(
        "Missing POST realtime resume API."
    )

print(
    "PASS frontend message pagination API"
)

print(
    "PASS frontend realtime resume API"
)
'@

$CheckScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Pagination frontend API contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 PAGINATION API WIRING: PASS"
Write-Host "================================================="
Write-Host ""