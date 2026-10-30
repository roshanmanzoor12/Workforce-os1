param([switch]$Apply, [string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$src = Join-Path $Root 'backend\app\modules\live_monitoring\native_frame_relay.py'
if (!(Test-Path -LiteralPath $src)) { throw "Missing file: $src" }
$patch = Join-Path $PSScriptRoot 'patch_relay.py'
$py = 'python'
if (-not $Apply) {
    & $py $patch $Root
    if ($LASTEXITCODE -ne 0) { throw 'Preflight failed' }
    return
}
& $py $patch $Root
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed - no changes made' }
$backup = Join-Path $Root ('WorkforceOS-v5-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item -LiteralPath $src -Destination (Join-Path $backup 'native_frame_relay.py') -Force
& $py $patch $Root '--apply'
if ($LASTEXITCODE -ne 0) {
    Copy-Item -LiteralPath (Join-Path $backup 'native_frame_relay.py') -Destination $src -Force
    throw 'Apply failed - original restored'
}
& $py -m py_compile $src
if ($LASTEXITCODE -ne 0) {
    Copy-Item -LiteralPath (Join-Path $backup 'native_frame_relay.py') -Destination $src -Force
    throw 'Compile failed - original restored'
}
Write-Host "Backup: $backup" -ForegroundColor Green
Write-Host 'Patch applied. Backend RESTART is required. Windows Agent is unchanged.' -ForegroundColor Green
