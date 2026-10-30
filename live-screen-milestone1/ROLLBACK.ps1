param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$Target = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion'
if (Test-Path $Target) {
  Remove-Item -LiteralPath $Target -Recurse -Force
  Write-Host 'Milestone-1 companion source removed. Restore prior backup-screencompanion-* if present.'
}
