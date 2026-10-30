param([switch]$Apply)
$ErrorActionPreference='Stop'
$Root='C:\workforce-os'
if (!(Test-Path (Join-Path $Root 'backend\app\modules\live_monitoring\service.py'))) {throw 'Project not found'}
$Python='python'
if ($Apply) { & $Python "$PSScriptRoot\Apply-v4.py" $Root --apply } else { & $Python "$PSScriptRoot\Apply-v4.py" $Root }
if ($LASTEXITCODE -ne 0) {throw 'Patch validation failed'}
