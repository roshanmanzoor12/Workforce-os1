$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

$MainPath = Join-Path `
    $Backend `
    "app\main.py"

Set-Location $Backend

if (-not (Test-Path $MainPath))
{
    throw "app\main.py not found."
}

$Text = Get-Content `
    $MainPath `
    -Raw


# =========================================================
# FRIENDS IMPORT
# =========================================================

if (
    $Text -notmatch
    "app\.modules\.friends\.router"
)
{
    $ImportPattern = (
        "(?ms)" +
        "(from app\.modules\.billing\.router import \(" +
        "\s*router as billing_router," +
        "\s*\)\s*)"
    )

    if (
        $Text -notmatch
        $ImportPattern
    )
    {
        throw (
            "Billing router import block not found. " +
            "main.py was not modified."
        )
    }

    $FriendImport = @'

from app.modules.friends.router import (
    router as friends_router,
)
from app.modules.chat.router import (
    router as chat_router,
)
'@

    $Text = [regex]::Replace(
        $Text,
        $ImportPattern,
        {
            param($Match)

            return (
                $Match.Groups[1].Value +
                $FriendImport
            )
        },
        1
    )

    Write-Host "PASS social/chat imports inserted"
}
else
{
    Write-Host "Social/chat imports already present"
}


# =========================================================
# ROUTER REGISTRATION
# =========================================================

if (
    $Text -notmatch
    "app\.include_router\(\s*friends_router"
)
{
    $IncludePattern = (
        "(?ms)" +
        "(app\.include_router\(" +
        "\s*billing_router," +
        "\s*prefix=settings\.api_v1_prefix," +
        "\s*\)\s*)"
    )

    if (
        $Text -notmatch
        $IncludePattern
    )
    {
        throw (
            "Billing include_router block not found. " +
            "main.py was not modified."
        )
    }

    $SocialInclude = @'

app.include_router(
    friends_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    chat_router,
    prefix=settings.api_v1_prefix,
)
'@

    $Text = [regex]::Replace(
        $Text,
        $IncludePattern,
        {
            param($Match)

            return (
                $Match.Groups[1].Value +
                $SocialInclude
            )
        },
        1
    )

    Write-Host "PASS social/chat routers registered"
}
else
{
    Write-Host "Social/chat routers already registered"
}


Set-Content `
    -Path $MainPath `
    -Value $Text `
    -Encoding UTF8


& $Python `
    -m py_compile `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "main.py compile failed after social/chat wiring."
}

Write-Host "PASS main.py compile"
Write-Host ""
Write-Host "PHASE 11.6 SOCIAL/CHAT ROUTER WIRING: PASS"