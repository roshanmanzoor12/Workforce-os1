$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Attachment Contract Dump"
Write-Host "================================================="
Write-Host ""

$BackendRoot =
    Split-Path `
        -Parent `
        $PSScriptRoot

Set-Location $BackendRoot

$Python =
    Join-Path `
        $BackendRoot `
        ".venv\Scripts\python.exe"

if (
    -not (
        Test-Path $Python
    )
) {
    Write-Host `
        "FAIL: virtualenv Python not found." `
        -ForegroundColor Red

    exit 1
}


Write-Host "[1/5] Publisher class contract"
Write-Host "-------------------------------------------------"

& $Python `
    ".\scripts\phase16c_realtime_contract_probe.py"

if (
    $LASTEXITCODE -ne 0
) {
    Write-Host ""
    Write-Host `
        "FAIL: realtime contract probe failed." `
        -ForegroundColor Red

    exit 1
}


Write-Host ""
Write-Host "[2/5] realtime_events.py"
Write-Host "-------------------------------------------------"

Get-Content `
    ".\app\modules\channels\realtime_events.py"


Write-Host ""
Write-Host "[3/5] Attachment bind route locations"
Write-Host "-------------------------------------------------"

$BindMatches =
    Get-ChildItem `
        ".\app" `
        -Recurse `
        -File `
        -Filter "*.py" |
    Select-String `
        -Pattern `
        "bind_to_message|attachment_ids|messages/.*/attachments|messages.*attachments" `
        -Context 12,28


if ($BindMatches)
{
    $BindMatches
}
else
{
    Write-Host "[NO MATCHES]"
}


Write-Host ""
Write-Host "[4/5] Realtime publish call sites"
Write-Host "-------------------------------------------------"

$RealtimeCalls =
    Get-ChildItem `
        ".\app" `
        -Recurse `
        -File `
        -Filter "*.py" |
    Select-String `
        -Pattern `
        "channel_realtime_events|WorkspaceChannelRealtimeEventPublisher" `
        -Context 10,30


if ($RealtimeCalls)
{
    $RealtimeCalls
}
else
{
    Write-Host "[NO MATCHES]"
}


Write-Host ""
Write-Host "[5/5] Message mutation realtime examples"
Write-Host "-------------------------------------------------"

$MutationCalls =
    Get-ChildItem `
        ".\app\modules\channels" `
        -Recurse `
        -File `
        -Filter "*.py" |
    Select-String `
        -Pattern `
        "message.created|message.updated|message.deleted|message.edited|publish" `
        -Context 12,30


if ($MutationCalls)
{
    $MutationCalls
}
else
{
    Write-Host "[NO MATCHES]"
}


Write-Host ""
Write-Host "================================================="
Write-Host " CONTRACT DUMP COMPLETE"
Write-Host "================================================="
Write-Host ""