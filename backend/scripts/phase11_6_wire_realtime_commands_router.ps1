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
# NORMALIZE
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
    "from app\.modules\.chat\.realtime_commands_router import"
)
{
    $Pattern = (
        "(?ms)" +
        "from app\.modules\.chat\.realtime_router import \(" +
        "\s*router as chat_realtime_router," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $Pattern
    )

    if (-not $Match.Success)
    {
        throw (
            "chat_realtime_router import " +
            "block not found."
        )
    }

    $Block = @'

from app.modules.chat.realtime_commands_router import (
    router as chat_realtime_commands_router,
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

    Write-Host "PASS realtime commands import inserted"
}
else
{
    Write-Host "Realtime commands import already present"
}


# =========================================================
# INCLUDE
# =========================================================

if (
    $Text -notmatch
    "app\.include_router\(\s*chat_realtime_commands_router"
)
{
    $Pattern = (
        "(?ms)" +
        "app\.include_router\(" +
        "\s*chat_realtime_router," +
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
            "chat_realtime_router include " +
            "block not found."
        )
    }

    $Block = @'

app.include_router(
    chat_realtime_commands_router,
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

    Write-Host "PASS realtime commands router registered"
}
else
{
    Write-Host "Realtime commands router already registered"
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
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "main.py compile failed."
}


@'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/chat/realtime/typing/{conversation_id}/start": "post",
    "/api/v1/chat/realtime/typing/{conversation_id}/stop": "post",
    "/api/v1/chat/realtime/typing/{conversation_id}": "get",
    "/api/v1/chat/realtime/heartbeat": "post",
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
    "PASS realtime command router wiring"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime commands contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 REALTIME COMMAND WIRING: PASS"
Write-Host "================================================="
Write-Host ""