$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 21 Channels Certification"
Write-Host "================================================"


Write-Host ""
Write-Host "[1/9] Compile Phase 21 tests..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\channels" `
    ".\tests\modules\channels_phase21" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 compile failed."
}

Write-Host "PASS compile"


Write-Host ""
Write-Host "[2/9] Existing channel regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Existing channel regression failed."
}


Write-Host ""
Write-Host "[3/9] HTTP/realtime route contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 route contract failed."
}


Write-Host ""
Write-Host "[4/9] Schema/channel-type contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_schema_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 schema contract failed."
}


Write-Host ""
Write-Host "[5/9] Message mutation contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_message_mutations.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 message mutation contract failed."
}


Write-Host ""
Write-Host "[6/9] Durable read-state/attachments..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_read_state.py" `
    ".\tests\modules\channels_phase21\test_phase21_attachments.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 durable state contract failed."
}


Write-Host ""
Write-Host "[7/9] Realtime security/events..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_realtime_security.py" `
    ".\tests\modules\channels_phase21\test_phase21_realtime_events.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 realtime contract failed."
}


Write-Host ""
Write-Host "[8/9] Workspace RBAC boundary..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\channels_phase21\test_phase21_rbac_boundary.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 21 RBAC contract failed."
}


Write-Host ""
Write-Host "[9/9] Attachment regression..."

$Targets = @(
    ".\tests\modules\attachments"
)

foreach ($Target in $Targets) {
    if (Test-Path $Target) {
        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 21 Channels Certification Gate PASS"
Write-Host "================================================"