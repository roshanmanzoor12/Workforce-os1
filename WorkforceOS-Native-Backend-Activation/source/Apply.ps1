param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $Here 'last-backup.txt'
$Files = @('backend\app\modules\live_monitoring\native_frame_relay.py', 'backend\app\modules\live_monitoring\native_http_gateway.py', 'backend\app\modules\live_monitoring\router.py', 'backend\app\modules\devices\agent_router.py')
if ($Rollback) {
  if (-not (Test-Path $Manifest)) { throw 'No installer backup reference found.' }
  $Backup = (Get-Content $Manifest -Raw).Trim()
  foreach ($F in $Files) {
    $Orig = Join-Path $Backup $F; $Dst = Join-Path $Root $F
    if (Test-Path $Orig) { Copy-Item -LiteralPath $Orig -Destination $Dst -Force }
    elseif (Test-Path $Dst) { Remove-Item -LiteralPath $Dst -Force }
  }
  Write-Host "Restored originals from $Backup"; exit 0
}
foreach ($F in $Files) {
 $Source = Join-Path $Here "patch\$F"; $Dest = Join-Path $Root $F
 if (-not (Test-Path $Source)) { throw "Patch file missing: $Source" }
 if (-not (Test-Path (Split-Path -Parent $Dest))) { throw "Target directory missing: $Dest" }
}
foreach ($F in $Files) { if ($F -like '*router.py') { $Dest = Join-Path $Root $F; if ((Get-Content -LiteralPath $Dest -Raw).Contains('NATIVE_HTTP_GATEWAY_V1')) { throw "Gateway already installed: $Dest" } } }
if (-not $Apply) { Write-Host 'DRY RUN passed. WARNING: Backend HTTP-only gateway; NOT an end-to-end native screen fix.'; exit 0 }
# Avoid overwriting unexpected changes made after the uploaded archive.
$Backup = Join-Path $Root ('workforce-patch-backups\native-http-gateway-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($F in $Files) {
 $Source = Join-Path $Here "patch\$F"; $Dest = Join-Path $Root $F; $Old = Join-Path $Backup $F
 New-Item -ItemType Directory -Force (Split-Path -Parent $Old) | Out-Null
 if (Test-Path $Dest) { Copy-Item -LiteralPath $Dest -Destination $Old -Force }
 if ($F -like '*router.py') {
   $Existing = Get-Content -LiteralPath $Dest -Raw
   if ($Existing.Contains('NATIVE_HTTP_GATEWAY_V1')) { throw "Gateway already present: $Dest" }
   $Entire = Get-Content -LiteralPath $Source -Raw
   $Marker = '# NATIVE_HTTP_GATEWAY_V1:'
   $Index = $Entire.LastIndexOf($Marker)
   if ($Index -lt 0) { throw "Patch marker missing: $Source" }
   $Append = $Entire.Substring($Index)
   $Utf8 = New-Object System.Text.UTF8Encoding($false)
   [System.IO.File]::WriteAllText($Dest, $Existing.TrimEnd()+"`r`n`r`n"+$Append, $Utf8)
 } else { Copy-Item -LiteralPath $Source -Destination $Dest -Force }
}
Set-Content -LiteralPath $Manifest -Value $Backup
Write-Host "Installed HTTP native gateway backend files. Backup: $Backup"
Write-Host 'Does NOT implement Agent-to-Companion IPC or native Windows consent popup.'
