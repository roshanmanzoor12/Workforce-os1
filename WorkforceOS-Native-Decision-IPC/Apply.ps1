param([switch]$Apply,[switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Files = @(
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs',
  'agent\WorkforceOS.Agent\LiveScreen\CompanionRequestNotifier.cs',
  'agent\WorkforceOS.ScreenCompanion\Program.cs',
  'agent\WorkforceOS.ScreenCompanion\IncomingRequestPipe.cs'
)
$Expected = @{
  'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs' = 'C285C87E107CCFDD5AE4FB212A3CB1DD5C39895FA90497592934F2A1E403D799'
  'agent\WorkforceOS.Agent\LiveScreen\CompanionRequestNotifier.cs' = '624F10AD0F54950166681F3BC6DE846A55591274452A7D6DFD1FA67032B80A11'
  'agent\WorkforceOS.ScreenCompanion\Program.cs' = '898C34E8267AA154EC8F9308DDFDA03FE29F4A268F3329828B995ADAE058A6D4'
  'agent\WorkforceOS.ScreenCompanion\IncomingRequestPipe.cs' = '86285AE8A02191F8B81DC2623060C98C277FE33E020C2993D5BF722C9EDD465A'
}
$Marker = Join-Path $PSScriptRoot '.latest-backup.txt'
if ($Rollback) {
  if (!(Test-Path -LiteralPath $Marker)) { throw 'Backup marker missing' }
  $Backup = (Get-Content -LiteralPath $Marker -Raw).Trim()
  foreach ($Rel in $Files) {
    $Saved = Join-Path $Backup $Rel
    if (!(Test-Path -LiteralPath $Saved)) { throw "Cannot restore missing backup: $Saved" }
    Copy-Item -LiteralPath $Saved -Destination (Join-Path $Root $Rel) -Force
  }
  Write-Host "Restored four files from $Backup"; exit 0
}
foreach ($Rel in $Files) {
  $Target = Join-Path $Root $Rel
  $Source = Join-Path (Join-Path $PSScriptRoot 'files') $Rel
  if (!(Test-Path -LiteralPath $Target) -or !(Test-Path -LiteralPath $Source)) { throw "Missing file: $Rel" }
  $Current = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
  if ($Current -ne $Expected[$Rel]) { throw "Existing file drift; no changes: $Rel ($Current)" }
}
if (!$Apply) { Write-Host 'DRY RUN PASSED: source matches previous Native IPC Step. No changes.'; exit 0 }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup = Join-Path $Root "workforce-patch-backups\native-decision-ipc-$Stamp"
foreach ($Rel in $Files) {
  $Dest = Join-Path $Backup $Rel
  New-Item -ItemType Directory -Force -Path (Split-Path $Dest -Parent) | Out-Null
  Copy-Item -LiteralPath (Join-Path $Root $Rel) -Destination $Dest -Force
}
try {
  foreach ($Rel in $Files) {
    $Src = Join-Path (Join-Path $PSScriptRoot 'files') $Rel
    $Dst = Join-Path $Root $Rel
    Copy-Item -LiteralPath $Src -Destination $Dst -Force
    if ((Get-FileHash -LiteralPath $Src).Hash -ne (Get-FileHash -LiteralPath $Dst).Hash) { throw "Hash verification failed: $Rel" }
    Write-Host "VERIFIED: $Rel"
  }
} catch {
  foreach ($Rel in $Files) { Copy-Item -LiteralPath (Join-Path $Backup $Rel) -Destination (Join-Path $Root $Rel) -Force }
  throw
}
Set-Content -LiteralPath $Marker -Value $Backup -NoNewline
Write-Host "SOURCE PATCH INSTALLED. Backup: $Backup"
Write-Host 'IMPORTANT: Decision is local-only; no backend approval or remote capture enabled.'
