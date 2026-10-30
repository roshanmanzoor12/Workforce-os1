param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference='Stop'
$Files = @(
  'backend\app\modules\live_monitoring\router.py',
  'apps\web\app\(workspace)\monitoring\live-screen\page.tsx',
  'apps\web\components\monitoring\monitoring-consent-gate.tsx',
  'apps\web\components\monitoring\live-screen-auto-flow.tsx',
  'apps\web\components\monitoring\saved-screen-sharing-setting.tsx',
  'agent\WorkforceOS.ScreenCompanion\Program.cs'
)
foreach ($file in $Files) {
  if (!(Test-Path (Join-Path $Root $file))) { throw "MISSING: $file" }
}
$Backend=Get-Content -LiteralPath (Join-Path $Root $Files[0]) -Raw
if (!$Backend.Contains('_ViewerLiveScreenSession.created_at.desc()')) { throw 'V17 backend field fix missing' }
if ($Backend.Contains('_ViewerLiveScreenSession.requested_at.desc()')) { throw 'V16 invalid field still present' }
$Modal=Get-Content -LiteralPath (Join-Path $Root $Files[2]) -Raw
if (!$Modal.Contains('V17_SAVED_APPROVAL_IN_MODAL')) {throw 'Saved approval not mounted in Monitoring Settings'}
$Auto=Get-Content -LiteralPath (Join-Path $Root $Files[3]) -Raw
if ($Auto.Contains('position: "fixed"')) { throw 'Old floating approval card still present' }
$Companion=Get-Content -LiteralPath (Join-Path $Root $Files[5]) -Raw
if (!$Companion.Contains('WFOS_V17_COMPACT_INDICATOR')) { throw 'Compact employee indicator source missing' }
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { $Python='python' }
& $Python -m py_compile (Join-Path $Root $Files[0])
if ($LASTEXITCODE -ne 0) {throw 'Backend Python compile failed'}
Write-Host 'V17 SOURCE VERIFICATION PASS. Windows .NET and Next.js builds still required.' -ForegroundColor Green
