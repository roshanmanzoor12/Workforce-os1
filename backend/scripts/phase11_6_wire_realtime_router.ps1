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
    "from app\.modules\.chat\.realtime_router import"
)
{
    $AnchorPattern = (
        "(?ms)" +
        "from app\.modules\.chat\.router import \(" +
        "\s*router as chat_router," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $AnchorPattern
    )

    if (-not $Match.Success)
    {
        throw (
            "chat_router import block not found. " +
            "main.py was not modified."
        )
    }

    $ImportBlock = @'

from app.modules.chat.realtime_router import (
    router as chat_realtime_router,
)
'@

    $Replacement = (
        $Match.Value +
        "`r`n" +
        $ImportBlock +
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

    Write-Host "PASS realtime router import inserted"
}
else
{
    Write-Host "Realtime router import already present"
}


# =========================================================
# INCLUDE ROUTER
# =========================================================

if (
    $Text -notmatch
    "app\.include_router\(\s*chat_realtime_router"
)
{
    $AnchorPattern = (
        "(?ms)" +
        "app\.include_router\(" +
        "\s*chat_router," +
        "\s*prefix=settings\.api_v1_prefix," +
        "\s*\)"
    )

    $Match = [regex]::Match(
        $Text,
        $AnchorPattern
    )

    if (-not $Match.Success)
    {
        throw (
            "chat_router include block not found. " +
            "main.py was not modified."
        )
    }

    $IncludeBlock = @'

app.include_router(
    chat_realtime_router,
    prefix=settings.api_v1_prefix,
)
'@

    $Replacement = (
        $Match.Value +
        "`r`n" +
        $IncludeBlock +
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

    Write-Host "PASS realtime router registered"
}
else
{
    Write-Host "Realtime router already registered"
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


# =========================================================
# WRITE + COMPILE
# =========================================================

Set-Content `
    -Path $MainPath `
    -Value $Text `
    -Encoding UTF8

& $Python `
    -m py_compile `
    .\app\main.py `
    .\app\modules\chat\realtime_router.py

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime router/main.py compile failed."
}

Write-Host "PASS main.py compile"


# =========================================================
# ROUTER CONTRACT
# =========================================================

@'
from fastapi.routing import (
    APIWebSocketRoute,
)

from app.main import app
from app.modules.chat.realtime_router import (
    router as chat_realtime_router,
)

schema = app.openapi()

paths = schema.get(
    "paths",
    {},
)

ticket_path = (
    "/api/v1/chat/realtime/ticket"
)

if ticket_path not in paths:
    raise RuntimeError(
        f"Missing realtime HTTP route: {ticket_path}"
    )

if "post" not in paths[ticket_path]:
    raise RuntimeError(
        "Missing POST realtime ticket operation."
    )

print(
    "PASS realtime HTTP router"
)

router_ws_paths = {
    route.path
    for route in chat_realtime_router.routes
    if isinstance(
        route,
        APIWebSocketRoute,
    )
}

expected_router_ws = (
    "/chat/realtime/ws"
)

if expected_router_ws not in router_ws_paths:
    raise RuntimeError(
        "Realtime router does not define "
        f"WebSocket path: {expected_router_ws}"
    )

print(
    "PASS realtime WebSocket route definition"
)

main_source = open(
    "app/main.py",
    "r",
    encoding="utf-8-sig",
).read()

required_main_tokens = (
    "chat_realtime_router",
    "app.include_router(",
    "prefix=settings.api_v1_prefix",
)

for token in required_main_tokens:
    if token not in main_source:
        raise RuntimeError(
            f"main.py missing realtime wiring token: {token}"
        )

print(
    "PASS realtime WebSocket router wiring"
)

print(
    "PASS effective WebSocket path: "
    "/api/v1/chat/realtime/ws"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime router contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 REALTIME ROUTER WIRING: PASS"
Write-Host "================================================="
Write-Host ""