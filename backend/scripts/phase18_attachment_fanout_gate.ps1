$ErrorActionPreference = "Stop"


. (
    Join-Path `
        $PSScriptRoot `
        "phase18_common.ps1"
)


Set-Location $script:Phase18BackendRoot


Write-Host "================================================="
Write-Host " Phase 18 Attachment Realtime E2E Gate"
Write-Host "================================================="
Write-Host ""


Write-Host "[1/4] Attachment lifecycle..."


& $script:Phase18Python `
    ".\scripts\phase17_attachment_access_contract.py"


if ($LASTEXITCODE -ne 0)
{
    Fail-Phase18 `
        "Attachment lifecycle contract failed."
}


Write-Host "PASS attachment lifecycle"
Write-Host ""


Write-Host "[2/4] Realtime attachment bridge..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_attachment_bridge.py" `
    -Tokens @(
        "publish_bound",
        "attachment_bound",
        "attachment_ids",
        "message_id"
    )


Write-Host "PASS attachment bridge"
Write-Host ""


Write-Host "[3/4] Attachment event publisher..."


Assert-Phase18Contains `
    -Path ".\app\modules\channels\realtime_events.py" `
    -Tokens @(
        "attachment_bound",
        "ATTACHMENT_BOUND",
        "message_id",
        "attachment_ids"
    )


Write-Host "PASS attachment event publisher"
Write-Host ""


Write-Host "[4/4] Certified runtime attachment fanout..."


Invoke-Phase18LegacyGate `
    -Regex "(?is)(attachment.*fanout|fanout.*attachment|attachment.*realtime.*runtime)" `
    -Label "Attachment realtime fanout"


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 18 ATTACHMENT REALTIME E2E: PASS"
Write-Host "================================================="

exit 0