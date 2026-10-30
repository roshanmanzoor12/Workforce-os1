param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$PatchRoot = Join-Path $PSScriptRoot 'files'
$Marker = Join-Path $PSScriptRoot '.latest-backup.txt'
$Files = @(
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs',
  'agent\WorkforceOS.Agent\LiveScreen\CompanionRequestNotifier.cs',
  'agent\WorkforceOS.ScreenCompanion\Program.cs',
  'agent\WorkforceOS.ScreenCompanion\IncomingRequestPipe.cs'
)
if ($Rollback) {
  if (-not (Test-Path $Marker)) { throw 'No backup marker found' }
  $backup = (Get-Content $Marker -Raw).Trim()
  foreach ($relative in $Files) {
    $original = Join-Path $backup $relative
    $target = Join-Path $Root $relative
    if (Test-Path -LiteralPath $original) { Copy-Item -LiteralPath $original -Destination $target -Force }
    elseif ($relative -match '(CompanionRequestNotifier|IncomingRequestPipe)\.cs$') { Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue }
  }
  Write-Host "Rollback applied from $backup"; exit 0
}
foreach ($relative in $Files) {
  $source = Join-Path $PatchRoot $relative
  $target = Join-Path $Root $relative
  if (-not (Test-Path -LiteralPath $source)) { throw "Missing package file $relative" }
  if (-not (Test-Path -LiteralPath (Split-Path $target -Parent))) { throw "Project folder missing $relative" }
}
# Fail closed if source files have drifted away from the archived source this patch was built against.
$Expected = @{
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs' = '680076B8052CCFA0B5C1FFADD523362A1BDA7E349960E31C48E6B9882376D6E3'
  'agent\WorkforceOS.ScreenCompanion\Program.cs' = 'ED3F188B1D366AF984D0405A91D84FC50DE60111341F53D310074B3A13CEDC3A'
}
foreach ($relative in $Expected.Keys) {
  $target = Join-Path $Root $relative
  if (-not (Test-Path $target)) { throw "Missing existing source $relative" }
  $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
  if ($hash -ne $Expected[$relative]) { throw "Source changed; no modifications made: $relative (SHA256 $hash). A compatible patch is required." }
}
if (-not $Apply) { Write-Host 'DRY RUN PASSED. This is source-only informational native IPC; NOT a live video fix.'; exit 0 }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $Root "workforce-patch-backups\native-ipc-$stamp"
foreach ($relative in $Files) {
  $target = Join-Path $Root $relative
  if (Test-Path $target) {
    $save = Join-Path $backup $relative
    New-Item -ItemType Directory -Force -Path (Split-Path $save -Parent) | Out-Null
    Copy-Item -LiteralPath $target -Destination $save -Force
  }
}
foreach ($relative in $Files) {
  $source = Join-Path $PatchRoot $relative
  $target = Join-Path $Root $relative
  Copy-Item -LiteralPath $source -Destination $target -Force
  if ((Get-FileHash $source).Hash -ne (Get-FileHash $target).Hash) { throw "Hash verification failed: $relative" }
  Write-Host "VERIFIED: $relative"
}
Set-Content -LiteralPath $Marker -Value $backup -NoNewline
Write-Host "SOURCE PATCH INSTALLED. Backup: $backup"
Write-Host 'Does not update running binaries or enable capture. Build both projects before runtime testing.'
