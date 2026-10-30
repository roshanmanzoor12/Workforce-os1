param(
  [string]$Root = 'C:\workforce-os',
  [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$Script = Join-Path $PSScriptRoot 'apply_patch.py'
if (!(Test-Path -LiteralPath $Script)) { throw "Missing patch engine: $Script" }
if (!(Test-Path -LiteralPath $Root)) { throw "Missing WorkforceOS root: $Root" }
$ArgsForPython = @($Script, '--root', $Root)
if ($Apply) { $ArgsForPython += '--apply' }
& python @ArgsForPython
if ($LASTEXITCODE -ne 0) { throw 'Patch preflight/application failed; inspect errors.' }
if ($Apply) {
  Write-Host 'Checking Python source syntax...' -ForegroundColor Cyan
  & python -m compileall -q (Join-Path $Root 'backend\app\modules\devices') (Join-Path $Root 'backend\app\modules\live_monitoring')
  if ($LASTEXITCODE -ne 0) { throw 'Python syntax check failed; restore files from the generated backup.' }
  Write-Host 'Backend source patched. Do NOT assume Windows Agent or frontend is fixed.' -ForegroundColor Yellow
}
