param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Patch = Join-Path $PSScriptRoot 'files'
$Paths = @('backend\app\modules\devices\agent_router.py','agent\WorkforceOS.ScreenCompanion\Program.cs')
foreach ($Relative in $Paths) {
    $Target = Join-Path $Root $Relative
    $Source = Join-Path $Patch $Relative
    if (!(Test-Path $Target) -or !(Test-Path $Source)) { throw "Missing source/target: $Relative" }
    $Original = [IO.File]::ReadAllText($Target)
    if ($Original -match 'WFOS_V9_EMPLOYEE_STOP_REVOCATION') { throw "V9 already applied: $Relative" }
    if ($Relative -like '*.py' -and $Original -notmatch 'async def activate_device_live_screen') { throw 'Unexpected backend baseline' }
    if ($Relative -like '*.cs' -and $Original -notmatch 'private void StopPreview\(\)') { throw 'Unexpected Companion baseline' }
    Write-Host "BASELINE OK: $Relative"
}
if (!$Apply) { Write-Host 'PREFLIGHT PASS (dry-run). Rerun with -Apply.'; exit 0 }
$Backup = Join-Path $Root ('WorkforceOS-v9-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($Relative in $Paths) {
    $Target = Join-Path $Root $Relative
    $Source = Join-Path $Patch $Relative
    $Before = [IO.File]::ReadAllText($Target)
    $Expected = [IO.File]::ReadAllText($Source)
    # Only apply to the exact submitted source state; never overwrite arbitrary local changes.
    $Baseline = Join-Path $PSScriptRoot ('baseline\' + $Relative)
    if ((Get-FileHash $Target).Hash -ne (Get-FileHash $Baseline).Hash) { throw "Source diverged: $Relative. No files changed for this entry." }
}
foreach ($Relative in $Paths) {
    $Target = Join-Path $Root $Relative
    $Source = Join-Path $Patch $Relative
    $BackupPath = Join-Path $Backup $Relative
    New-Item -ItemType Directory -Path (Split-Path $BackupPath) -Force | Out-Null
    Copy-Item $Target $BackupPath -Force
    Copy-Item $Source $Target -Force
    if ((Get-FileHash $Target).Hash -ne (Get-FileHash $Source).Hash) { throw "Copy verification failed: $Relative" }
    Write-Host "APPLIED: $Relative"
}
Write-Host "PATCH VERIFIED. Backup: $Backup"
