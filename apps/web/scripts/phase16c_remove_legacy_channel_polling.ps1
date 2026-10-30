$ErrorActionPreference = "Stop"


Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Remove Legacy Polling"
Write-Host "================================================="
Write-Host ""


$WebRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot


Set-Location $WebRoot


$RoomFile =
    ".\components\channels\text-channel-room.tsx"


if (
    -not (
        Test-Path $RoomFile
    )
)
{
    throw "Missing file: $RoomFile"
}


$Content =
    Get-Content `
        $RoomFile `
        -Raw


$Pattern = '(?ms)\s*const timer\s*=\s*window\.setInterval\(\s*\(\)\s*=>\s*\{\s*void load\(\s*false,\s*\);\s*\},\s*4000,\s*\);\s*return \(\) => \{\s*window\.clearInterval\(\s*timer,\s*\);\s*\};'


if (
    $Content -match
    $Pattern
)
{
    $Content =
        [regex]::Replace(
            $Content,
            $Pattern,
            "",
            1
        )


    Set-Content `
        -Path $RoomFile `
        -Value $Content `
        -Encoding utf8


    Write-Host `
        "PASS: legacy 4-second channel polling removed"

}
elseif (
    $Content -notmatch
    'setInterval'
)
{
    Write-Host `
        "PASS: no legacy setInterval found"

}
else
{
    Write-Host ""
    Write-Host (
        "FAIL: setInterval exists but expected legacy polling block did not match."
    ) `
        -ForegroundColor Red

    Write-Host ""
    Write-Host (
        "No file changes were made by this run."
    )

    exit 1
}


Write-Host ""
Write-Host "================================================="
Write-Host " LEGACY CHANNEL POLLING REMOVAL COMPLETE"
Write-Host "================================================="
Write-Host ""